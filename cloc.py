from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
from typing import Optional, Tuple
import re
import json

TEST_START = re.compile("\\bmod +test *{")

FILES = [
    "core/src/lower/cache.rs",
    "core/src/lower/mod.rs",
    "core/src/upper/array.rs",
    "core/src/upper/mod.rs",
    "core/src/entry.rs",
    "core/src/lib.rs",
    "core/src/table.rs",
    "core/src/util.rs",
]


def main():
    parser = ArgumentParser(
        description="Count line of code and tests separately")
    parser.add_argument("dir")
    args = parser.parse_args()

    tmp = Path("/tmp/cloc")
    tmp.mkdir(exist_ok=True)

    total_code = 0
    total_tests = 0

    print("file,code,tests")

    dir = Path(args.dir)
    assert (dir.exists())

    for file_name in FILES:
        file = dir / file_name
        assert (file.exists())

        code, tests = split_file(tmp, file)
        code_loc = cloc(code)
        tests_loc = cloc(tests)

        print(f"{file_name},{code_loc},{tests_loc}")
        total_code += code_loc
        total_tests += tests_loc

    print(f"total,{total_code},{total_tests}")


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


def is_test_start(line: str) -> Optional[str]:
    if match := TEST_START.search(line):
        return line[match.end():]
    return None


def count_brackets(line: str) -> int:
    return line.count("{") - line.count("}")


if __name__ == "__main__":
    main()
