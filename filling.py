from argparse import ArgumentParser
from subprocess import check_output, STDOUT, CalledProcessError

from utils import setup, rm_ansi_escape


def main():
    parser = ArgumentParser(
        description="Running the allocator benchmarks locally")
    parser.add_argument("-a", "--alloc", nargs="+")
    parser.add_argument("-e", "--exe",
                        default="../llfree-rs/target/release/bench")
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", type=int, default=8)
    parser.add_argument("-o", "--order", type=int, default=0)
    parser.add_argument("-i", "--iter", type=int, default=4)
    parser.add_argument("-l", "--levels", type=int, nargs="+",
                        required=True, help="Initial filling levels as percentage")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--dax")
    args, root = setup("filling", parser, custom="local")

    print("Running")

    print(f"Exec filling o={args.order} c={args.cores}")

    levels = map(lambda c: f"-x{c}", args.levels)
    outfile = root / f"out.csv"

    bargs = [args.exe, "filling", *args.alloc, *levels, f"-s{args.order}",
             f"-t{args.cores}", f"-i{args.iter}",
             f"-m{args.mem}", "--stride", str(args.stride),
             "-o", str(outfile)]
    if args.dax:
        bargs = [*bargs, "--dax", args.dax]

    try:
        output = check_output(
            bargs, text=True, stderr=STDOUT, timeout=600.0)
    except CalledProcessError as e:
        (root / f"error.txt").write_text(rm_ansi_escape(e.output))
        raise e

    (root / f"running.txt").write_text(rm_ansi_escape(output))


if __name__ == "__main__":
    main()
