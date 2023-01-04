from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
from typing import Dict

MODULE = [
    "mm/nvalloc/*"
]

EXCLUDE = [
    "*.config",
    "README.md",
    *MODULE,
]


def main():
    parser = ArgumentParser(description="Changes in the linux integration")
    parser.add_argument("repo", help="LLFree Linux Repository")
    parser.add_argument("since", help="Last commit before our changes")
    parser.add_argument("--dref", help="Output into a dref file")
    args = parser.parse_args()

    module = check_output(["git", "diff", "--stat", args.since, "--",
                           *[f":{p}" for p in MODULE]], text=True, cwd=args.repo)
    module_stats = parse_stats(module)
    print(sum(module_stats.values()), module_stats)
    linux = check_output(["git", "diff", "--stat", args.since, "--",
                          *[f":!{p}" for p in EXCLUDE]], text=True, cwd=args.repo)
    linux_stats = parse_stats(linux)
    print(sum(linux_stats.values()), linux_stats)

    if args.dref:
        dref = ""
        for file, changes in module_stats.items():
            dref += f"\\drefset{{diff_module/{file}}}{{{changes}}}\n"
        dref += f"\\drefset{{diff_module}}{{{sum(module_stats.values())}}}\n"

        for file, changes in linux_stats.items():
            dref += f"\\drefset{{diff_linux/{file}}}{{{changes}}}\n"
        dref += f"\\drefset{{diff_linux}}{{{sum(linux_stats.values())}}}\n"
        Path(args.dref).write_text(dref)


def parse_stats(stats: str) -> Dict[str, int]:
    result = dict()
    for line in stats.splitlines(keepends=False):
        cols = line.split("|")
        assert (len(cols) <= 2)
        if len(cols) == 2:
            result[cols[0].strip()] = int(cols[1].strip(" -+"))
    return result


if __name__ == "__main__":
    main()
