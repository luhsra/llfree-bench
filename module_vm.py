from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep
import shlex

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, timestamp, sys_info


def main():
    parser = ArgumentParser(description="Running the module benchmarks")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("-o", "--orders", type=int, default=0, nargs="+")
    parser.add_argument("--module")
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--suffix")
    parser.add_argument("benches", type=str, nargs="+")
    args = parser.parse_args()

    root = Path("module")
    if args.suffix:
        root /= f"{timestamp()}-{args.suffix}"
    else:
        root /= timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        values = vars(args)
        values["sys"] = sys_info()
        json.dump(values, f)

    ssh = SSHExec(args.user, port=args.port)

    for bench in args.benches:
        dir = root / bench
        dir.mkdir(parents=True, exist_ok=True)

        print(f"bench {bench}")

        try:
            print("start qemu...")
            qemu = qemu_vm(args.kernel, args.mem, max(
                args.cores), args.port)

            print("started")
            with (dir / "cmd.sh").open("w+") as f:
                f.write(shlex.join(qemu.args))
            with (dir / "boot.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            print("load module")
            if args.module:
                ssh.upload(args.module)
            ssh("sudo insmod alloc.ko")

            for order in args.orders:
                print("configure")
                allocs = (((args.mem * (512 ** 2)) // max(args.cores)) // 2) // (1 << order)
                core_list = ','.join([str(c) for c in args.cores])
                print(f"allocate half the memory ({allocs} on {core_list}, o={order})")

                with (dir / "running.txt").open("a+") as f:
                    f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

                print(f"run order={order}")
                ssh(f"echo '{bench} {args.iterations} {allocs} {order} {core_list}' | sudo tee /proc/alloc/run",
                    timeout=600.0)

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
