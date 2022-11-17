from argparse import ArgumentParser
from pathlib import Path
import json
from time import sleep
import shlex

from utils import SSHExec, timestamp, non_block_read, qemu_vm, rm_ansi_escape


def main():
    parser = ArgumentParser(description="Running the write benchmark")
    parser.add_argument("--user", default="debian")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-s", "--sockets", type=int, default=2)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--args", default="--private")
    args = parser.parse_args()

    mem = args.mem // 2
    assert (mem > 0)

    root = Path("write") / timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        json.dump(vars(args), f)

    dir = root

    ssh = SSHExec(args.user, port=args.port)

    try:
        print("start qemu...")
        qemu = qemu_vm(args.kernel, args.mem, max(
            args.cores), args.port, sockets=args.sockets)
        if not ((ret := qemu.poll()) is None):
            raise Exception(f"QEMU Crashed {ret}")

        print("started")
        with (dir / "cmd.sh").open("w+") as f:
            f.write(shlex.join(qemu.args))
        with (dir / "boot.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        print("run")

        with (dir / "out.csv").open("w+") as f:
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
