from argparse import ArgumentParser
from subprocess import check_output, STDOUT, CalledProcessError

from utils import setup, rm_ansi_escape


def main():
    parser = ArgumentParser(
        description="Running the allocator benchmarks locally")
    parser.add_argument("bench", nargs="+", choices=["bulk", "repeat", "rand"])
    parser.add_argument("-a", "--alloc", nargs="+")
    parser.add_argument("-e", "--exe",
                        default="../llfree-rs/target/release/bench")
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+",
                        type=int, required=True)
    parser.add_argument("-o", "--orders", nargs="+",
                        type=int, required=True)
    parser.add_argument("-i", "--iter", type=int, default=4)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--dax")
    args, root = setup("allocator", parser, custom="local")

    print("Running")

    for bench in args.bench:
        dir = root / str(bench)
        dir.mkdir(parents=True, exist_ok=True)

        for order in args.orders:
            print(f"Exec {bench} o={order} c={args.cores}")

            threads = map(lambda c: f"-x{c}", args.cores)
            max_threads = max(args.cores)
            outfile = dir / f"out_{order}.csv"

            bargs = [args.exe, bench, *args.alloc, *threads, f"-s{order}",
                     f"-t{max_threads}", f"-i{args.iter}",
                     f"-m{args.mem}", "--stride", str(args.stride),
                     "-o", str(outfile)]
            if args.dax:
                bargs = [*bargs, "--dax", args.dax]

            try:
                output = check_output(
                    bargs, text=True, stderr=STDOUT, timeout=2 * 60.0 * 60.0)
            except CalledProcessError as e:
                (dir / f"error.txt").write_text(rm_ansi_escape(e.output))
                raise e

            (dir / f"out_{order}.txt").write_text(rm_ansi_escape(output))


if __name__ == "__main__":
    main()
