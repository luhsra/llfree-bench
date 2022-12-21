from argparse import ArgumentParser
from time import sleep
import shlex

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, setup


def main():
    parser = ArgumentParser(description="Running the frag benchmark")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("-r", "--realloc", type=int, default=10)
    parser.add_argument("-o", "--order", type=int, default=0)
    parser.add_argument("--module")
    parser.add_argument("--kernel", required=True)
    args, root = setup("frag", parser, custom="vm")

    assert(args.cores > 0)
    assert(args.realloc > 0 and args.realloc <= 100)
    assert(args.order <= 10)

    ssh = SSHExec(args.user, port=args.port)

    try:
        print("start qemu...")
        qemu = qemu_vm(args.kernel, args.mem, args.cores, args.port)

        print("started")
        with (root / "cmd.sh").open("w+") as f:
            f.write(shlex.join(qemu.args))
        with (root / "boot.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        print("load module")
        if args.module:
            ssh.upload(args.module)

        ssh("sudo insmod alloc.ko")

        print(
            f"allocate half the memory ({args.cores}, o={args.order})")

        with (root / "running.txt").open("a+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        print("run")
        ssh(f"echo 'frag {args.iterations} {args.realloc} {args.order} 0' | sudo tee /proc/alloc/run",
            timeout=600.0)

        sleep(1)

        print("save out")
        out = ssh("sudo cat /proc/alloc/out", output=True)
        with (root / "out.csv").open("w+") as f:
            f.write(out)

        out = ssh("sudo cat /proc/alloc/fragout", output=True, text=False)
        with (root / "fragout.bin").open("wb+") as f:
            f.write(out)

        with (root / "running.txt").open("a+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

    except Exception as e:
        with (root / "error.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
        qemu.terminate()
        raise e

    print("terminate...")
    qemu.terminate()
    sleep(3)


if __name__ == "__main__":
    main()
