from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep
import shlex

from utils import SSHExec, timestamp, non_block_read, qemu_vm, rm_ansi_escape


def main():
    parser = ArgumentParser(
        description="Running the memtier benchmark and measuring the page allocations")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-t", "--time", type=int, default=60)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("--kernel", required=True)
    args = parser.parse_args()

    mem = args.mem // 2
    assert (mem > 0)

    root = Path("memtier") / timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        json.dump(vars(args), f)

    ssh = SSHExec(args.user, port=args.port)

    for cores in args.cores:
        print(f"Run c{cores}")
        dir = root / f"c{cores}"
        dir.mkdir(parents=True, exist_ok=True)

        try:
            print("start qemu...")
            qemu = qemu_vm(args.kernel, args.mem, cores, args.port, sockets=2)
            if not ((ret := qemu.poll()) is None):
                raise Exception(f"QEMU Crashed {ret}")

            print("started")
            with (dir / "cmd.sh").open("w+") as f:
                f.write(shlex.join(qemu.args))
            with (dir / "boot.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            print("memcached")
            ssh(f"memcached -t {cores} -d")

            sleep(10)

            for iter in range(args.iterations):
                print(f"memtier {iter}")

                ssh(
                    f"./memtier_benchmark -s localhost -p 11211 --protocol memcache_text " +
                    f"--test-time {args.time} -t {cores} --json-out-file=out.json",
                    timeout=args.time * 2)
                with (dir / f"out_{iter}.json").open("w+") as f:
                    f.write(ssh("cat out.json", output=True))

                sleep(3)

            with (dir / "running.txt").open("a+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        except Exception as e:
            with (dir / "error.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
            qemu.terminate()
            raise e

        print("terminate...")
        qemu.terminate()


if __name__ == "__main__":
    main()
