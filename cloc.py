from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
from typing import List, Optional, Tuple
import re
import json

TEST_START = re.compile("\\bmod +test *{")

ALLOC_FILES = [
    "core/src/lower/cache.rs",
    "core/src/lower/mod.rs",
    "core/src/upper/array.rs",
    "core/src/upper/mod.rs",
    "core/src/entry.rs",
    "core/src/lib.rs",
    "core/src/table.rs",
    "core/src/util.rs",
]

LINUX_FILES = [
    "mm/page_alloc.c",
]


def main():
    parser = ArgumentParser(
        description="Count line of code and tests separately")
    parser.add_argument("--llfree", help="Path to the allocator repository")
    parser.add_argument("--linux", help="Path to the Linux repository")
    parser.add_argument("--dref", help="Save the totals as dref")
    args = parser.parse_args()

    tmp = Path("/tmp/cloc")
    tmp.mkdir(exist_ok=True)

    print("file,code,tests")

    dref = ""

    if args.llfree:
        code, tests = cloc_files("llfree", ALLOC_FILES, Path(args.llfree), tmp)
        if args.dref:
            dref += f"\\drefset{{llfree_loc}}{{{code}}}\n"
            dref += f"\\drefset{{llfree_loc_tests}}{{{tests}}}\n"

    if args.linux:
        code, tests = cloc_files("linux", LINUX_FILES, Path(args.linux), tmp)
        if args.dref:
            dref += f"\\drefset{{linux_loc}}{{{code}}}\n"

    if args.dref:
        Path(args.dref).write_text(dref)


def cloc_files(name: str, files: List[str], dir: Path, tmp: Path) -> Tuple[int, int]:
    assert (dir.exists())
    total_code = 0
    total_tests = 0
    for file_name in files:
        code, tests = cloc_tests(name, file_name, dir, tmp)
        total_code += code
        total_tests += tests
    print(f"{name},{total_code},{total_tests}")
    return (total_code, total_tests)


def cloc_tests(name: str, file_name: str, dir: Path, tmp: Path) -> Tuple[int, int]:
    file = dir / file_name
    if file.suffix == ".rs":
        assert (file.exists())

        code_f, tests_f = split_file(tmp, file)
        code = cloc(code_f)
        tests = cloc(tests_f)

        print(f"{name}/{file_name},{code},{tests}")
        return (code, tests)
    else:
        code = cloc(file)
        print(f"{name}/{file_name},{code},0")
        return (code, 0)


def cloc(file: Path) -> int:
    if out := check_output(["cloc", "-json", str(file)], text=True):
        return json.loads(out)['SUM']['code']
    return 0


def split_file(tmp: Path, file: Path) -> Tuple[Path, Path]:
    code = ""
    tests = ""

    remainder = file.read_text()

    while match := TEST_START.search(remainder):
        code += remainder[:match.end()]
        remainder = remainder[match.end():]
        test_brackets = 1
        for i, char in enumerate(remainder):
            if char == "{":
                test_brackets += 1
            elif char == "}":
                test_brackets -= 1

            if test_brackets <= 0:
                remainder = remainder[i:]
                break

            tests += char

    code += remainder

    code_path = tmp / f"code{file.suffix}"
    code_path.write_text(code)
    tests_path = tmp / f"tests{file.suffix}"
    tests_path.write_text(tests)
    return (code_path, tests_path)


def count_brackets(line: str) -> int:
    return line.count("{") - line.count("}")


if __name__ == "__main__":
    main()
