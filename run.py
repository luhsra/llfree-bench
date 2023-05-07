import numpy as np
import pandas as pd
import seaborn as sns
from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call
from typing import List
import psutil

CORES = psutil.cpu_count(logical=False) // 2
MEM = int(round(psutil.virtual_memory().total / 2 / (1024**3)))

ROOT = Path.cwd().parent
KERNEL = ROOT / "llfree-linux"
MODULE = ROOT / "linux-alloc-bench"
USER = ROOT / "llfree-rs"

BUILD_BUDDY = Path.cwd() / "build-buddy"
BUILD_LLFREE = Path.cwd() / "build-llfree"
BUILD_USER = Path.cwd() / "build-user"


def main():
    parser = ArgumentParser(description="Run the benchmarks")
    subparsers = parser.add_subparsers(help="sub-command help", required=True)

    parser_build = subparsers.add_parser("build", help="build the components")
    parser_build.add_argument(
        "target", choices=["all"] + list(BUILD_CONFIG.keys()))
    parser_build.set_defaults(func=build)

    parser_bench = subparsers.add_parser("bench", help="run the benchmarks")
    parser_bench.add_argument(
        "target", choices=["all"] + list(BENCH_CONFIG.keys()))
    parser_bench.add_argument(
        "-m", "--mem", type=int, help="Amount of memory", default=MEM)
    parser_bench.add_argument(
        "-c", "--cores", type=int, help="Number of CPUs", default=CORES)
    parser_bench.set_defaults(func=bench)

    parser_bench = subparsers.add_parser("plot", help="plot the results")
    parser_bench.add_argument(
        "target", choices=["all"] + list(BENCH_CONFIG.keys()))
    parser_bench.set_defaults(func=plot)

    args = parser.parse_args()
    args.func(args)


def build(args):
    print("Rebuilding the artifacts for", args.target)
    BUILD_BUDDY.mkdir(parents=True, exist_ok=True)
    BUILD_LLFREE.mkdir(parents=True, exist_ok=True)
    BUILD_USER.mkdir(parents=True, exist_ok=True)

    if args.target == "all":
        for config in BUILD_CONFIG.values():
            config.run()
    else:
        # module depends on kernel
        if args.target == "module":
            BUILD_CONFIG["kernel"].run()

        BUILD_CONFIG[args.target].run()


def bench(args):
    cores = " ".join(map(str, range(1, args.cores + 1)))

    stride = psutil.cpu_count() // psutil.cpu_count(logical=False)
    if stride != 1:
        print(
            "\x1b[91mWARNING: Hyperthreading detected! The results might differ!\x1b[0m")

    min_cores = min(8, args.cores / stride)

    targets = BENCH_CONFIG.keys() if args.target == "all" else [args.target]
    print("Benchmark", " ".join(targets), f"cores={args.cores} mem={args.mem}")
    for target in targets:
        BENCH_CONFIG[target].run(
            cores=cores,
            min_cores=min_cores,
            mem=args.mem,
            stride=stride,
        )
    # also plot the results
    plot(args)


def plot(args):
    sns.set_style("whitegrid")
    sns.set_context("poster")
    sns.set_palette("colorblind")

    plotters = {
        "user": plot_user,
        "kernel": plot_kernel,
        "frag": plot_frag,
    }
    targets = plotters.keys() if args.target == "all" else [args.target]
    for target in targets:
        plotters[target]()


def plot_user():
    print("Plotting user results...")

    outdir = Path("artifact/user")
    outdir.mkdir(parents=True, exist_ok=True)

    volatile_orders = Path("allocator/artifact-dram-o")
    volatile_cores = Path("allocator/artifact-dram-c")

    col_order = ["Bulk", "Rand", "Repeat"]

    def read_orders(dir: str, orders: List[int]) -> pd.DataFrame:
        data = []
        for o in orders:
            d = pd.read_csv(f"{dir}/out_{o}.csv")
            d["order"] = o
            data.append(d)
        data = pd.concat(data)
        data["Allocator"] = data["alloc"]
        data["cores"] = data["x"]
        data["alloc"] = data["get_avg"]
        data["free"] = data["put_avg"]
        return data[["Allocator", "order", "cores", "iteration", "alloc", "free"]]

    def read_all_bench(dir: Path, orders: List[int], bulk=True, repeat=True, rand=True) -> pd.DataFrame:
        data = []
        if bulk:
            data_b = read_orders(dir / "bulk", orders)
            data_b["bench"] = "Bulk"
            data.append(data_b)
        if repeat:
            data_r = read_orders(dir / "repeat", orders)
            data_r["bench"] = "Repeat"
            data_r["free+alloc"] = data_r["alloc"]
            del data_r["alloc"]
            del data_r["free"]
            data.append(data_r)
        if rand:
            data_a = read_orders(dir / "rand", orders)
            data_a["bench"] = "Rand"
            del data_a["alloc"]
            data.append(data_a)
        return pd.concat(data)

    # --------------------------------------------------------------------------
    # Orders
    # --------------------------------------------------------------------------
    data = read_all_bench(volatile_orders, list(range(11)))
    data["Memory"] = "Volatile"
    pgd = data[["bench", "order", "cores", "Memory", "alloc", "free", "free+alloc"]].melt(
        id_vars=["bench", "order", "cores", "Memory"],
        value_vars=["alloc", "free", "free+alloc"], value_name="time", var_name="Operation")

    g = sns.FacetGrid(data=pgd, col="bench",
                      col_order=col_order, height=5, aspect=0.8)
    g.map_dataframe(sns.lineplot, x="order", y="time",
                    markers=True, hue="Operation", style="Memory")
    g.add_legend(adjust_subtitles=True)
    g.set(ylim=(0, None))
    # g.set(ylim=(10, 10**5))
    # g.set(yscale="log")
    g.set(ylabel="Avg. time (ns)")
    g.set(xlabel="Orders")
    g.set(xticks=[0, 2, 4, 6, 8, 10])
    g.set_titles("{col_name}")
    g.savefig(outdir / "orders.png")

    # --------------------------------------------------------------------------
    # Multicore
    # --------------------------------------------------------------------------
    data = read_all_bench(volatile_cores, [0, 9])
    data["Memory"] = "Volatile"
    pgd = data[["bench", "order", "cores", "Memory", "alloc", "free", "free+alloc"]].melt(
        id_vars=["bench", "order", "cores", "Memory"],
        value_vars=["alloc", "free", "free+alloc"], value_name="time", var_name="Operation")

    g = sns.FacetGrid(data=pgd, row="order", col="bench", col_order=col_order,
                      height=5, aspect=0.8, margin_titles=True)
    g.map_dataframe(sns.lineplot, x="cores", y="time",
                    style="Memory", hue="Operation")
    g.add_legend(adjust_subtitles=True)
    g.set(ylim=(0, None))
    # g.set(ylim=(1, 10**5 * 1.5))
    # g.set(yscale="log")
    g.set(ylabel="Avg. time (ns)")
    g.set(xlabel="Cores")
    g.set_titles(col_template="{col_name}",
                 row_template="Order {row_name}")
    g.savefig(outdir / "cores.png")


def plot_kernel():
    print("Plotting kernel results...")

    ll_o = Path("module/artifact-ll-o")
    bu_o = Path("module/artifact-bu-o")
    ll_c = Path("module/artifact-ll-c")
    bu_c = Path("module/artifact-bu-c")

    outdir = Path("artifact/kernel")
    outdir.mkdir(parents=True, exist_ok=True)

    col_order = ["Bulk", "Rand", "Repeat"]

    def read_orders(dir: str, orders: List[int]) -> pd.DataFrame:
        data = []
        for o in orders:
            d = pd.read_csv(f"{dir}/out_{o}.csv")
            d["order"] = o
            data.append(d)
        data = pd.concat(data)
        data["cores"] = data["x"]
        data["alloc"] = data["get_avg"]
        data["free"] = data["put_avg"]
        return data[["order", "cores", "iteration", "alloc", "free"]]

    def read_all_bench(dir: Path, orders: List[int]) -> pd.DataFrame:
        data_b = read_orders(dir / "bulk", orders)
        data_b["bench"] = "Bulk"
        data_r = read_orders(dir / "repeat", orders)
        data_r["bench"] = "Repeat"
        data_r["free+alloc"] = data_r["alloc"]
        del data_r["alloc"]
        del data_r["free"]
        data_a = read_orders(dir / "rand", orders)
        data_a["bench"] = "Rand"
        del data_a["alloc"]
        return pd.concat([data_b, data_r, data_a])

    # --------------------------------------------------------------------------
    # Intro plot
    # --------------------------------------------------------------------------
    data_bu = read_orders(bu_c / "bulk", [0, 9])
    pgd = data_bu.melt(
        id_vars=["order", "cores"],
        value_vars=["alloc", "free"], value_name="time", var_name="Operation")

    g = sns.FacetGrid(data=pgd, col="order", aspect=1.1,
                      height=5, sharey=False)
    g.map_dataframe(sns.lineplot, x="cores", y="time",
                    hue="Operation", style="Operation")

    g.add_legend(adjust_subtitles=True)
    g.legend.set_title("Operation")
    g.set(ylim=(0, None))
    g.set(ylabel="Avg. time (ns)")
    g.set(xlabel="Threads")
    g.set_titles("Order {col_name}")
    g.axes_dict[9].set_ylabel("")
    g.axes_dict[0].set_title("Frames")
    g.axes_dict[9].set_title("Huge Frames")
    g.savefig(outdir / "intro.png")

    # --------------------------------------------------------------------------
    # Orders
    # --------------------------------------------------------------------------
    data_ll = read_all_bench(ll_o, list(range(11)))
    data_ll["Allocator"] = "LLFree"
    data_bu = read_all_bench(bu_o, list(range(11)))
    data_bu["Allocator"] = "Buddy"

    data_o = pd.concat([data_ll, data_bu], ignore_index=True)
    pgd = data_o.melt(
        id_vars=["bench", "order", "Allocator"],
        value_vars=["alloc", "free", "free+alloc"], value_name="time", var_name="Operation")

    g = sns.FacetGrid(data=pgd, col="bench",
                      col_order=col_order, aspect=0.8, height=5)
    g.map_dataframe(sns.lineplot, x="order", y="time",
                    hue="Operation", style="Allocator", markers=True)
    g.add_legend(adjust_subtitles=True)
    # g.set(ylim=(None, 10000))
    g.set(ylim=(50, 10**5))
    g.set(yscale="log")
    g.set(ylabel="Avg. time (ns)")
    g.set(xlabel="Orders")
    g.set(xticks=[0, 2, 4, 6, 8, 10])
    g.set_titles("{col_name}")
    g.savefig(outdir / "orders.png")

    # --------------------------------------------------------------------------
    # Multicore
    # --------------------------------------------------------------------------
    data_ll = read_all_bench(ll_c, [0, 9])
    data_ll["Allocator"] = "LLFree"
    data_bu = read_all_bench(bu_c, [0, 9])
    data_bu["Allocator"] = "Buddy"

    data_c = pd.concat([data_ll, data_bu], ignore_index=True)
    pgd = data_c.melt(
        id_vars=["bench", "order", "cores", "Allocator"],
        value_vars=["alloc", "free", "free+alloc"], value_name="time", var_name="Operation")

    g = sns.FacetGrid(data=pgd, row="order", col="bench", col_order=col_order,
                      height=5, aspect=0.8, margin_titles=True)
    g.map_dataframe(sns.lineplot, x="cores", y="time",
                    style="Allocator", hue="Operation")
    g.add_legend(adjust_subtitles=True)

    g.set(ylim=(50, 10**5))
    g.set(yscale="log")
    g.set(ylabel="Avg. time (ns)")
    g.set(xlabel="Cores")
    g.set_titles(col_template="{col_name}",
                 row_template="Order {row_name}")
    g.savefig(outdir / "cores.png")


def plot_frag():
    print("Plotting frag results...")

    llfree = Path("frag/artifact-ll")
    buddy = Path("frag/artifact-bu")

    outdir = Path("artifact/frag")
    outdir.mkdir(parents=True, exist_ok=True)

    def parse_fragout(file: Path, iterations: int) -> pd.DataFrame:
        data = file.read_bytes()
        assert(len(data) % (iterations * 2) == 0)
        huge_pages = len(data) // iterations // 2
        out = np.zeros((iterations, huge_pages))
        for i in range(iterations):
            total = 0
            for hp in range(huge_pages):
                b = data[(i * huge_pages + hp) *
                         2:(i * huge_pages + hp) * 2 + 2]
                n = int.from_bytes(b, byteorder="little", signed=False)
                assert(n <= 512)
                total += n
                out[i, hp] = float(n)
            # print(huge_pages, total)
        return pd.DataFrame(out)

    def compaction_copies_per_iteration(data: pd.DataFrame):
        count = len(data.index)
        copies = np.zeros(count)
        # copies = [0] * count
        for n in range(count):
            print(f"\r- iteration={n+1}/{count}", end="", flush=True)
            it = data.iloc[n].sort_values().reset_index(drop=True)
            left = 0
            right = len(it) - 1
            while left < right:
                d = min(512 - it[right], it[left])
                it[right] += d
                it[left] -= d
                copies[n] += d
                if it[right] == 512:
                    right -= 1
                if it[left] == 0:
                    left += 1
        print()
        return pd.DataFrame(copies)

    print("computing fragmentation costs, this might take several minutes...")
    print("buddy:")
    buddy_data = parse_fragout(buddy / "fragout.bin", 100)
    buddy_copies = compaction_copies_per_iteration(buddy_data)

    print("llfree:")
    llfree_data = parse_fragout(llfree / "fragout.bin", 100)
    llfree_copies = compaction_copies_per_iteration(llfree_data)

    # --------------------------------------------------------------------------
    # Combined plot
    # --------------------------------------------------------------------------
    # Hugepages
    bdata = pd.read_csv(buddy / "out.csv")
    possible = bdata["small"][0] / 512
    # bdata["Possible"] = bdata["small"] / 512
    bdata["Buddy"] = bdata["huge"]
    bdata = bdata[["iter", "Buddy"]]
    ndata = pd.read_csv(llfree / "out.csv")
    ndata["LLFree"] = ndata["huge"]
    ndata = ndata[["iter", "LLFree"]]

    huge = pd.concat([ndata, bdata])
    huge = huge.melt(["iter"], value_vars=["LLFree", "Buddy"],
                     value_name="count", var_name="alloc")
    initial = huge["count"][0]
    print(initial, possible)
    huge["count"] -= initial  # subtract leftover huge pages
    huge["type"] = "Free Huge Frames"
    huge["count"] /= (possible - initial) / 50  # normalize

    # Moves
    bdata = buddy_copies.copy()
    bdata.columns = ["Buddy"]
    bdata["iter"] = bdata.index
    ldata = llfree_copies.copy()
    ldata.columns = ["LLFree"]
    ldata["iter"] = ldata.index

    move = pd.concat([ldata, bdata])
    move = move.melt(["iter"], value_vars=["LLFree", "Buddy"],
                     value_name="count", var_name="alloc")
    move["type"] = "Compaction Costs"

    # Combined
    data = pd.concat([huge, move])
    g = sns.FacetGrid(data, col="type", sharey=False,
                      height=5.5, aspect=1.2)
    g.map_dataframe(sns.lineplot, x="iter", y="count", hue="alloc")
    g.set_titles(col_template="{col_name}")
    g.axes_dict["Free Huge Frames"].set(ylim=(-4, 54))
    g.set_xlabels("Iteration")
    g.set_ylabels("Percentage", clear_inner=False)
    g.set(xticks=[x * 20 for x in range(6)])
    g.set()
    g.add_legend()
    g.figure.subplots_adjust(wspace=0.35)
    g.axes_dict["Compaction Costs"].set(ylabel="Page Moves")
    g.axes_dict["Free Huge Frames"].set(yticks=[10 * x for x in range(6)])
    g.savefig(outdir / "frag.png")


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


BENCH_USER_C = f"python3 allocator.py bulk rand repeat -a Array4C32 -e {BUILD_USER}/bench -m{{mem}} --stride {{stride}}"
BENCH_KERNEL_C = f"python3 module_vm.py bulk rand repeat -m{{mem}}"
BENCH_FRAG_C = f"python3 frag_vm.py -c {{min_cores}} -m {{mem}} -i 100 -r 10 -o 0"

BENCH_CONFIG = {
    "user": Exec(Path.cwd(), [
        f"{BENCH_USER_C} -c {{min_cores}} -o 0 1 2 3 4 5 6 7 8 9 10 --output artifact-dram-o",
        f"{BENCH_USER_C} -c {{cores}} -o 0 9 --output artifact-dram-c",
    ]),
    "kernel": Exec(Path.cwd(), [
        f"{BENCH_KERNEL_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko -c {{min_cores}} -o 0 1 2 3 4 5 6 7 8 9 10 --output artifact-bu-o",
        f"{BENCH_KERNEL_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko -c {{min_cores}} -o 0 1 2 3 4 5 6 7 8 9 10 --output artifact-ll-o",
        f"{BENCH_KERNEL_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko -c {{cores}} -o 0 9 --output artifact-bu-c",
        f"{BENCH_KERNEL_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko -c {{cores}} -o 0 9 --output artifact-ll-c",
    ]),
    "frag": Exec(Path.cwd(), [
        f"{BENCH_FRAG_C} --kernel {BUILD_BUDDY}/bzImage --module {BUILD_BUDDY}/alloc.ko --output artifact-bu",
        f"{BENCH_FRAG_C} --kernel {BUILD_LLFREE}/bzImage --module {BUILD_LLFREE}/alloc.ko --output artifact-ll",
    ]),
}


if __name__ == "__main__":
    main()
