#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep
import shlex
from typing import IO

from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, timestamp


def status(ssh: SSHExec, dir: Path, name: str, stdout: IO[str]):
    with (dir / name).open("w+") as f:
        f.write(ssh(f"cat /sys/kernel/page_alloc/size_counters", output=True))
    with (dir / "running.txt").open("a+") as f:
        f.write(rm_ansi_escape(non_block_read(stdout)))


def main():
    parser = ArgumentParser(
        description="Running the memtier benchmark and counting the page allocations")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
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

            print("started")
            with (dir / "cmd.sh").open("w+") as f:
                f.write(shlex.join(qemu.args))
            with (dir / "boot.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            print("status...")
            status(ssh, dir, "t0.csv", qemu.stdout)

            print("memcached...")
            if not args.dry:
                ssh("memcached", args=["-f"])
            sleep(5)

            print("status...")
            status(ssh, dir, "t1.csv", qemu.stdout)

            print("bench...")
            if args.dry or time == 0:
                sleep(max(1, time))
            else:
                with (dir / "bench.txt").open("w+") as f:
                    out = ssh(f"./memtier_benchmark -s localhost -p 11211 --protocol memcache_text --test-time {time}",
                              output=True, timeout=2 * time)
                    f.write(out)

            print("status...")
            status(ssh, dir, "t2.csv", qemu.stdout)

            print("terminate...")
            qemu.terminate()
        except Exception as e:
            with (dir / "error.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
            qemu.terminate()
            raise e

        sleep(3)


if __name__ == "__main__":
    main()
