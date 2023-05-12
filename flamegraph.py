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

    flamegraph = Path(args.fg) / "flamegraph.pl"
    assert flamegraph.exists()

    with input.open() as inp:
        with filtered.open("w+") as out:
            for line in inp:
                line = re.sub(r".llvm.[^;]*;", ";", line)
                line = re.sub(r".llvm.[^;]* ", " ", line)
                line = re.sub(r"\b\[unknown\];", "", line)
                line = re.sub(r"\b\[unknown\] ", " ", line)
                line = re.sub(r"\b__[^;]*;", "", line)
                line = re.sub(r"\b__[^;]* ", " ", line)
                line = re.sub(r"\b_(R|Z)N[^;]*;", "", line)
                line = re.sub(r"\b_(R|Z)N[^;]* ", "", line)
                line = re.sub(r"\bentry_SYSCALL_64_after_hwframe;do_syscall_64;", "", line)
                line = re.sub(r"\b__GI___ioctl_time64;__x64_sys_ioctl;", "", line)
                line = re.sub(r"\bsubmit_bio_noacct[^;]*;", "", line)
                line = re.sub(r"\bdo_idle[^;]*;", ";do_idle;", line)
                line = re.sub(r"\bentry_SYSCALL_64_after_hwframe.* ", "", line)
                line = re.sub(
                    r";(asm_exc_page_fault_\[k\]|exc_page_fault_\[k\]|do_user_addr_fault_\[k\]|handle_mm_fault_\[k\])", "", line)
                line = re.sub(r";(get_page_from_freelist_\[k\]|rmqueue_\[k\])", "", line)
                line = re.sub(r"\bwrite\b;?", "", line)
                out.write(line)

    check_call(f"{flamegraph} --minwidth 5 --bgcolors '#ffffff' --colors blue --width 500 {filtered} --title '' --fonttype Arial > {svg}", shell=True)

    def replace_color(t: str, color: str) -> str:
        return re.sub(r"fill=\"rgb\(\d+,\d+,\d+\)\"", f"fill=\"{color}\"", line)

    with svg.open() as inp:
        with svg.with_stem("colored").open("w+") as out:
            for line in inp:
                if re.match(r"<title>.*nvalloc.* ", line):
                    print("found", line)
                    line = replace_color(line, "rgb(222,143,5)")
                elif re.match(r"<title>.*_lock_.* ", line):
                    print("found", line)
                    line = replace_color(line, "rgb(213,94,0)")
                elif re.match(r"<title>.*(dirty|shared).* ", line):
                    print("found", line)
                    line = replace_color(line, "#029e73")
                elif re.match(r"<title>.*(lru).* ", line):
                    print("found", line)
                    line = replace_color(line, "#029e73")
                out.write(line)


if __name__ == "__main__":
    main()
