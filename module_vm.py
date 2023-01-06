from argparse import ArgumentParser
from time import sleep, time
import shlex

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, setup


def main():
    parser = ArgumentParser(description="Running the module benchmarks")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("-o", "--orders", type=int, default=0, nargs="+")
    parser.add_argument("--node", type=int, default=0)
    parser.add_argument("--module")
    parser.add_argument("--kernel", required=True)
    parser.add_argument("benches", type=str, nargs="+")
    args, root = setup("module", parser, custom="vm")

    ssh = SSHExec(args.user, port=args.port)
    dir = root
    try:
        print("start qemu...")
        qemu = qemu_vm(args.kernel, args.mem, max(args.cores), args.port)

        print("started")
        with (dir / "cmd.sh").open("w+") as f:
            f.write(shlex.join(qemu.args))
        with (dir / "boot.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        print("load module")
        if args.module:
            ssh.upload(args.module)
        ssh("sudo insmod alloc.ko")

        for bench in args.benches:
            dir = root / bench
            dir.mkdir(parents=True, exist_ok=True)

            print(f"bench {bench}")
            if qemu.poll() is not None:
                raise Exception("Qemu crashed")

            for order in args.orders:
                allocs = (((args.mem * (512 ** 2)) // max(args.cores)) // 2) // (1 << order)
                core_list = ','.join([str(c) for c in args.cores])
                print(f"run ({allocs} on {core_list} o={order} i={args.iterations})")

                with (dir / "running.txt").open("a+") as f:
                    f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

                benchmark = ssh.background(
                    f"echo '{bench} {args.iterations} {allocs} {order} {core_list} {args.node}' | sudo tee /proc/alloc/run")

                timeout = time() + 600.0 # seconds
                while benchmark.poll() is None:
                    sleep(5)
                    with (dir / "running.txt").open("a+") as f:
                        f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
                    if time() > timeout:
                        raise TimeoutError()

                if benchmark.returncode != 0:
                    raise Exception("Benchmark crashed")

                sleep(1)

                with (dir / "running.txt").open("a+") as f:
                    f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

                print("save out")
                with (dir / f"out_{order}.csv").open("w+") as f:
                    out = ssh("sudo cat /proc/alloc/out", output=True)
                    f.write(out)

    except Exception as e:
        with (dir / "error.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
        qemu.terminate()
        raise e

    print("terminate...")
    qemu.terminate()
    sleep(3)


if __name__ == "__main__":
    main()
