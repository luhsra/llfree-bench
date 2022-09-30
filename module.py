from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, timestamp


def main():
    parser = ArgumentParser(
        description="Running the memtier benchmark and measuring the page allocations")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("benches", type=str, nargs="+")
    parser.add_argument("--kernel", required=True)
    args = parser.parse_args()

    root = Path("module") / timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        json.dump(vars(args), f)

    ssh = SSHExec(args.user, port=args.port)

    for bench in args.benches:
        dir = root / bench
        dir.mkdir(parents=True, exist_ok=True)

        print(f"bench {bench}")

        try:
            print("start qemu...")
            qemu = qemu_vm(args.kernel, args.mem, max(
                args.cores), args.port, sockets=2)

            print("started")
            with (dir / "boot.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            print("load module")
            ssh("sudo insmod alloc.ko")

            print("configure")
            allocs = ((args.mem * (512 ** 2)) // max(args.cores)) // 2
            core_list = ','.join([str(c) for c in args.cores])
            print(f"allocate half the memory ({allocs} on {core_list})")

            with (dir / "running.txt").open("a+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            print("run")
            ssh(f"echo '{bench} {core_list} {args.iterations} {allocs}' | sudo tee /sys/kernel/alloc/run",
                timeout=600.0)

            sleep(1)

            print("save out")
            out = ssh("cat /sys/kernel/alloc/out", output=True)
            with (dir / "out.csv").open("w+") as f:
                f.write(out)

            with (dir / "running.txt").open("a+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

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
