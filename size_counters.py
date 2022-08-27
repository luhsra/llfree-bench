#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, timestamp


def status(ssh: SSHExec, file: Path):
    with file.open("w+") as f:
        f.write(ssh(f"cat /sys/kernel/page_alloc/size_counters", output=True))


def main():
    parser = ArgumentParser(
        description="Running the memtier benchmark and measuring the page allocations")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default="32G")
    parser.add_argument("-c", "--cores", default=8, type=int)
    parser.add_argument("-t", "--time", type=int, nargs="+")
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--kernel", required=True)
    args = parser.parse_args()

    root = Path("size_counters") / timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        json.dump(vars(args), f)

    ssh = SSHExec(args.user, port=args.port)

    for time in args.time:
        dir = root / f"t{time}"
        dir.mkdir(parents=True, exist_ok=True)

        print(f"time {time}")
        try:
            print("start qemu...")
            qemu = qemu_vm(args.kernel, args.mem, args.cores, args.port)

            print("status...")
            status(ssh, dir / "t0.csv")


            print("memcached...")
            if not args.dry:
                ssh("memcached", args=["-f"])
            sleep(5)

            print("status...")
            status(ssh, dir / "t1.csv")

            print("bench...")
            if args.dry or time == 0:
                sleep(max(1, time))
            else:
                with (dir / "bench.txt").open("wb+") as f:
                    out = ssh(f"memtier_benchmark -s localhost -p 11211 --protocol memcache_text --test-time {time}",
                        output=True)
                    f.write(out)

            print("status...")
            status(ssh, dir / "t2.csv")

            print("terminate...")
            qemu.terminate()
        except Exception as e:
            with (dir / "error.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
            raise e

        sleep(3)


if __name__ == "__main__":
    main()
