from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
from typing import List, Tuple
import re
import json

from utils import dump_dref

TEST_START = re.compile("\\bmod +test *{")
UNSAFE_START = re.compile("\\bunsafe\\b([ \\w\\d:<>_-]*){")

ALLOC_FILES = [
    "core/src/lower/cache.rs",
    "core/src/lower/mod.rs",
    "core/src/upper/array.rs",
    "core/src/upper/mod.rs",
    "core/src/atomic.rs",
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

    dref = {}

    if args.llfree:
        code, tests, unsafe = cloc_files(
            "llfree", ALLOC_FILES, Path(args.llfree), tmp)
        if args.dref:
            dref["llfree"] = code
            dref["llfree_tests"] = tests
            dref["llfree_unsafe"] = unsafe

    if args.linux:
        code, tests, unsafe = cloc_files(
            "linux", LINUX_FILES, Path(args.linux), tmp)
        if args.dref:
            dref["linux"] = code

    if args.dref:
        with Path(args.dref).open("w+") as f:
            dump_dref(f, "loc", dref)


def cloc_files(name: str, files: List[str], dir: Path, tmp: Path) -> Tuple[int, int, int]:
    assert (dir.exists())
    total_code = 0
    total_tests = 0
    total_unsafe = 0
    for file_name in files:
        code, tests, unsafe = cloc_tests(name, file_name, dir, tmp)
        total_code += code
        total_tests += tests
        total_unsafe += unsafe
    print(f"{name},{total_code},{total_tests},{total_unsafe}")
    return (total_code, total_tests, total_unsafe)


def cloc_tests(name: str, file_name: str, dir: Path, tmp: Path) -> Tuple[int, int, int]:
    file = dir / file_name
    if file.suffix == ".rs":
        assert (file.exists())

        code_d, tests_d = split_file(file.read_text(), TEST_START)

        code_f = tmp / f"code{file.suffix}"
        code_f.write_text(code_d)

        tests_f = tmp / f"tests{file.suffix}"
        tests_f.write_text(tests_d)

        code = cloc(code_f)
        tests = cloc(tests_f)

        unsafe = count_unsafe(code_d)

        print(f"{name}/{file_name},{code},{tests}")
        return (code, tests, unsafe)
    else:
        code = cloc(file)
        print(f"{name}/{file_name},{code},0,{code}")
        return (code, 0, code)


def cloc(file: Path) -> int:
    if out := check_output(["cloc", "-json", str(file)], text=True):
        return json.loads(out)['SUM']['code']
    return 0


def split_file(input: str, start: re.Pattern) -> Tuple[Path, Path]:
    code = ""
    tests = ""

    while match := start.search(input):
        code += input[:match.end()]
        input = input[match.end():]
        i = closing_bracket(input)
        tests += input[:i]
        input = input[i:]

    code += input
    return (code, tests)


def closing_bracket(text: str) -> int:
    brackets = 1
    for i, char in enumerate(text):
        if char == "{":
            brackets += 1
        elif char == "}":
            brackets -= 1

        if brackets <= 0:
            break

        i += 1
    return i


def count_unsafe(input: str) -> int:
    unsafe = 0
    while match := UNSAFE_START.search(input):
        input = input[match.end():]
        i = closing_bracket(input)
        # print(f"unsafe {{{input[:i]}}}")
        unsafe += 1 + input[:i].count("\n")
        input = input[i:]

    return unsafe


def count_brackets(line: str) -> int:
    return line.count("{") - line.count("}")


if __name__ == "__main__":
    main()
