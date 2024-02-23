from pathlib import Path
from sys import argv
from time import sleep
import subprocess
from typing import Tuple
import shlex

def free_pages() -> Tuple[int, int]:
    buddyinfo = Path("/proc/buddyinfo").read_text()
    small = 0
    huge = 0
    for line in buddyinfo.splitlines():
        orders = line.split()[4:]
        for order, free in enumerate(orders):
            small += int(free) << order
            if order >= 9:
                huge += int(free) << (order - 9)
    return small, huge

def main():

    if len(argv) <= 1:
        print("Usage: python monitor_mem.py <program> <args>")
        exit(1)

    with Path("mem_usage.csv").open("w+") as output:

        process = subprocess.Popen(args=shlex.join(argv[1:]), shell=True)
        while process.poll() is None:
            small, huge = free_pages()
            output.write(f"{small},{huge}\n")
            sleep(1)

        print("Process finished with return code", process.returncode)
        exit(process.returncode)

if __name__ == "__main__":
    main()
