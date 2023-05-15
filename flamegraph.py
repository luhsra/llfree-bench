from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_call

import re

def main():
    parser = ArgumentParser("Generating an customizing flamegraphs")
    parser.add_argument("input", help="Folded perf input")
    parser.add_argument("--fg", help="Path to the flamegraph repo", default="../FlameGraph")
    args = parser.parse_args()

    input = Path(args.input)
    filtered = input.with_suffix(".filtered")
    svg = input.with_suffix(".svg")
    filtered_svg = svg.with_stem("filtered")

    flamegraph = Path(args.fg) / "flamegraph.pl"
    assert flamegraph.exists()

    check_call(f"{flamegraph} --minwidth 2 --bgcolors '#ffffff' {input} --title '' --fonttype Arial > {svg}", shell=True)

    with input.open() as inp:
        with filtered.open("w+") as out:
            for line in inp:
                line = re.sub(r"std::sys_common::backtrace::", "", line)
                line = re.sub(r".llvm.[^;]*;", ";", line)
                line = re.sub(r".llvm.[^;]* ", " ", line)
                line = re.sub(r"\b\[unknown\];", "", line)
                line = re.sub(r"\b\[unknown\] ", " ", line)
                line = re.sub(r"\b__[^;]*;", "", line)
                line = re.sub(r"\b__[^;]* ", " ", line)
                line = re.sub(r"\b_(R|Z)N[^;]*;", "", line)
                line = re.sub(r"\b_(R|Z)N[^;]* ", "", line)
                line = re.sub(
                    r"\b(entry_SYSCALL_64|do_syscall_64|madvise_dontneed_free)_\[k\];", "", line)
                # line = re.sub(r"\b__GI___ioctl_time64;__x64_sys_ioctl;", "", line)
                line = re.sub(r"\bsubmit_bio_noacct[^;]*;", "", line)
                line = re.sub(r"\bdo_idle[^;]*;", ";do_idle;", line)
                line = re.sub(
                    r";(exc_page_fault|handle_mm_fault)_\[k\]", "", line)
                line = re.sub(
                    r";(get_page_from_freelist|rmqueue_\w+|free_pcppages_bulk)_\[k\]", "", line)
                line = re.sub(r";(zap_pmd_range|zap_pte_range)_\[k\]", "", line)
                line = re.sub(r";(error_entry|sync_regs|memcpy_erms)_\[k\]", "", line)
                line = re.sub(r"\bwrite\b;?", "", line)
                out.write(line)

    check_call(f"{flamegraph} --minwidth 5 --bgcolors '#ffffff' --colors blue --width 500 {filtered} --title '' --fonttype Arial > {filtered_svg}", shell=True)

    def replace_color(t: str, color: str) -> str:
        return re.sub(r"fill=\"rgb\(\d+,\d+,\d+\)\"", f"fill=\"{color}\"", line)

    with filtered_svg.open() as inp:
        with filtered_svg.with_stem("colored").open("w+") as out:
            for line in inp:
                if re.match(r"<title>all ", line):
                    print("found", line)
                    line = replace_color(line, "#0173b2")
                if re.match(r"<title>.*(rmqueue|free).* ", line):
                    print("found", line)
                    line = replace_color(line, "rgb(222,143,5)")
                elif re.match(r"<title>(.*_lock_|up_read|down_read).* ", line):
                    print("found", line)
                    line = replace_color(line, "rgb(213,94,0)")
                elif re.match(r"<title>.*(dirty|shared).* ", line):
                    print("found", line)
                    line = replace_color(line, "#029e73")
                elif re.match(r"<title>.*(lru|memcg|preemption|cgroup|rmap|prep|clear).* ", line):
                    print("found", line)
                    line = replace_color(line, "#029e73")
                elif re.match(r"<title>", line):
                    line = replace_color(line, "#a8a8a8")
                out.write(line)


if __name__ == "__main__":
    main()
