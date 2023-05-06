from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call
from typing import List
import psutil

CORES = psutil.cpu_count() // 2
MEM = int(round(psutil.virtual_memory().total / 2 / (1024**3)))

ROOT = Path.cwd().parent
KERNEL = ROOT / "llfree-linux"
MODULE = ROOT / "linux-alloc-bench"
USER = ROOT / "llfree-rs"

BUILD_BUDDY = Path.cwd() / "build-buddy"
BUILD_LLFREE = Path.cwd() / "build-llfree"
BUILD_USER = Path.cwd() / "build-user"


class Exec:
    def __init__(self, path: Path, cmds: List[str]) -> None:
        self.path = path
        self.cmds = cmds

    def run(self, **args):
        assert(self.cmds and self.path.exists())
        for cmd in self.cmds:
            cmd = cmd.format(**args)
            print(f"\n\x1b[94mEXEC: {cmd}\x1b[0m")
            check_call(cmd, cwd=self.path, shell=True)


def main():
    parser = ArgumentParser(description="Run the benchmarks")
    subparsers = parser.add_subparsers(help="sub-command help", required=True)

    parser_build = subparsers.add_parser("build", help="build the components")
    parser_build.add_argument(
        "target", choices=list(BUILD_CONFIG.keys()))
    parser_build.set_defaults(func=build)

    parser_bench = subparsers.add_parser("bench", help="run the benchmarks")
    parser_bench.add_argument(
        "kind", choices=list(BENCH_CONFIG.keys()))
    parser_bench.add_argument(
        "-m", "--mem", type=int, help="Amount of memory", default=MEM)
    parser_bench.add_argument(
        "-c", "--cores", type=int, help="Number of CPUs", default=CORES)
    parser_bench.set_defaults(func=bench)

    args = parser.parse_args()
    args.func(args)


BUILD_CONFIG = {
    "kernel": Exec(KERNEL, [
        f"make O=build-buddy-vm LLVM=-14 -j{CORES}",
        f"cp build-buddy-vm/arch/x86/boot/bzImage {BUILD_BUDDY}",
        f"make O=build-llfree-vm LLVM=-14 -j{CORES}",
        f"cp build-llfree-vm/arch/x86/boot/bzImage {BUILD_LLFREE}",
    ]),
    "module": Exec(MODULE, [
        f"make LINUX_BUILD_DIR={KERNEL}/build-buddy-vm LLVM=-14 -j{CORES}",
        f"cp alloc.ko {BUILD_BUDDY}",
        f"make LINUX_BUILD_DIR={KERNEL}/build-llfree-vm LLVM=-14 -j{CORES}",
        f"cp alloc.ko {BUILD_LLFREE}",
    ]),
    "user": Exec(USER, [
        f"cargo perf-build bench",
        f"cp target/release/bench {BUILD_USER}",
    ]),
}


def build(args):
    print("Rebuilding the artifacts for", args.target)
    BUILD_BUDDY.mkdir(parents=True, exist_ok=True)
    BUILD_LLFREE.mkdir(parents=True, exist_ok=True)
    BUILD_USER.mkdir(parents=True, exist_ok=True)

    # module depends on kernel
    if args.target == "module":
        BUILD_CONFIG["kernel"].run()

    BUILD_CONFIG[args.target].run()


BENCH_USER_C = f"python3 allocator_vm.py bulk repeat rand -a Array4C32 --kernel {BUILD_BUDDY}/bzImage -e {BUILD_USER}/bench -m{{mem}}"
BENCH_KERNEL_C = f"python3 module_vm.py bulk repeat rand -m{{mem}}"
BENCH_FRAG_C = f"python3 frag_vm.py -c 8 -m {{mem}} -i 100 -r 10 -o 0"

BENCH_CONFIG = {
    "user": Exec(Path.cwd(), [
        f"{BENCH_USER_C} -c 8 -o 0 1 2 3 4 5 6 7 8 9 10 --output test-dram-o",
        f"{BENCH_USER_C} -c 8 -o 0 1 2 3 4 5 6 7 8 9 10 --dax --output test-nvram-o",
        f"{BENCH_USER_C} -c {{cores}} -o 0 9 --output test-dram-c",
        f"{BENCH_USER_C} -c {{cores}} -o 0 9 --dax --output test-nvram-c",
    ]),
    "kernel": Exec(Path.cwd(), [
        f"{BENCH_KERNEL_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko -c 8 -o 0 1 2 3 4 5 6 7 8 9 10 --output test-bu-o",
        f"{BENCH_KERNEL_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko -c 8 -o 0 1 2 3 4 5 6 7 8 9 10 --output test-ll-o",
        f"{BENCH_KERNEL_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko -c {{cores}} -o 0 9 --output test-bu-o",
        f"{BENCH_KERNEL_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko -c {{cores}} -o 0 9 --output test-ll-o",
    ]),
    "frag": Exec(Path.cwd(), [
        f"{BENCH_FRAG_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko --output test-bu",
        f"{BENCH_FRAG_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko --output test-ll",
    ]),
}


def bench(args):
    print("Benchmark", args.kind, f"cores={args.cores} mem={args.mem}")

    assert(args.cores >= 8, "We need at least 8 cores")
    cores = " ".join(map(str, range(1, args.cores + 1)))

    BENCH_CONFIG[args.kind].run(cores=cores, mem=args.mem)


if __name__ == "__main__":
    main()
