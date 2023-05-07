from argparse import ArgumentParser
import shlex
from time import sleep

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, setup


def main():
    parser = ArgumentParser(description="Running the write benchmark")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-s", "--sockets", type=int, default=1)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--args", default="--private")
    parser.add_argument("--exe")
    args, root = setup("write", parser, custom="vm")

    mem = args.mem // 2
    assert (mem > 0)

    ssh = SSHExec(args.user, port=args.port)

    try:
        print("start qemu...")
        qemu = qemu_vm(args.port, args.kernel, args.mem,
                       max(args.cores), sockets=args.sockets)
        with (root / "cmd.sh").open("w+") as f:
            f.write(shlex.join(qemu.args))

        if not ((ret := qemu.poll()) is None):
            raise Exception(f"QEMU Crashed {ret}")

        print("started")
        with (root / "boot.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        if args.exe:
            ssh.upload(args.exe, "write")

        print("run")

        with (root / "out.csv").open("w+") as f:
            f.write("x,iteration,mem,map,amin,aavg,amax,fmin,favg,fmax,unmap\n")
            f.flush()

            for c in args.cores:
                for i in range(args.iterations):
                    out = ssh(f"./write -t{c} -m{mem} {args.args}",
                              output=True, timeout=600.0)
                    result = out.splitlines(False)[1]
                    f.write(f"{c},{i},{mem},{result}\n")
                    f.flush()

        sleep(1)

        with (root / "running.txt").open("a+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

    except Exception as e:
        with (root / "error.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
        qemu.terminate()
        raise e

    print("terminate...")
    qemu.terminate()


if __name__ == "__main__":
    main()
