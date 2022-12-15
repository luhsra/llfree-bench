from argparse import ArgumentParser
from pathlib import Path
import json
from subprocess import check_output, STDOUT
import shlex

from utils import timestamp


def main():
    parser = ArgumentParser(description="Running the write benchmark locally")
    parser.add_argument("exe", default="./write")
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-s", "--sockets", type=int, default=1)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("--args", default="--private")
    args = parser.parse_args()

    root = Path("write") / timestamp()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        meta = vars(args)
        meta["local"] = True
        json.dump(meta, f)

    print("run")

    with (root / "out.csv").open("w+") as f:
        f.write("x,iteration,mem,map,amin,aavg,amax,fmin,favg,fmax,unmap\n")
        f.flush()

        for c in args.cores:
            for i in range(args.iterations):
                out = check_output([args.exe, f"-t{c}", f"-m{args.mem}", *shlex.split(args.args)],
                                   text=True, stderr=STDOUT, timeout=600.0)
                result = out.splitlines(False)[1]
                f.write(f"{c},{i},{args.mem},{result}\n")
                f.flush()


if __name__ == "__main__":
    main()
