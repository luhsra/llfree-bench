from argparse import ArgumentParser
import json
from pathlib import Path
import shlex
from subprocess import CalledProcessError, Popen
from time import sleep
from typing import Tuple

from utils import SSHExec, non_block_read, qemu_vm, setup, rm_ansi_escape
from psutil import Process


def main():
    parser = ArgumentParser(
        description="Compiling linux in a vm while monitoring memory usage")
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--user", default="debian")
    parser.add_argument("--img", default="resources/hda.qcow2")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", type=int, default=8)
    parser.add_argument("-i", "--iter", type=int, default=1)
    parser.add_argument("--frag", action="store_true")
    parser.add_argument("--post-delay", type=int, default=10)

    args, root = setup("compiling", parser, custom="vm")

    ssh = SSHExec(args.user, port=args.port)

    print("Running")

    try:
        print("start qemu...")
        qemu = qemu_vm(args.qemu, args.port, args.kernel, args.mem, args.cores, hda=args.img)
        ps_proc = Process(qemu.pid)

        print("started")
        (root / "cmd.sh").write_text(shlex.join(qemu.args))
        (root / "boot.txt").write_text(rm_ansi_escape(non_block_read(qemu.stdout)))

        # ssh.run(f"echo 200 | sudo tee /proc/sys/vm/vfs_cache_pressure")

        for i in range(args.iter):
            if qemu.poll() is not None:
                raise Exception("Qemu crashed")

            print(f"Exec i={i} c={args.cores}")

            mem_usage = (root / f"out_{i}.csv").open("w+")
            mem_usage.write("rss,small,huge,cached\n")

            ssh.run("make -C llfree-linux clean")

            def measure(sec: int, process: Popen[str] | None = None):
                small, huge = free_pages(ssh.output("cat /proc/buddyinfo"))
                cached = mem_cached(ssh.output("cat /proc/meminfo"))
                rss = ps_proc.memory_info().rss
                mem_usage.write(f"{rss},{small},{huge},{cached}\n")

                if args.frag:
                    output = ssh.output("cat /proc/llfree_frag")
                    (root / f"frag_{i}_{sec}.txt").write_text(output)

                if process is not None:
                    with (root / f"out_{i}.txt").open("a+") as f:
                        f.write(rm_ansi_escape(non_block_read(process.stdout)))

            process = ssh.background(f"make -C llfree-linux -j{args.cores}")

            sec = 1
            while process.poll() is None:
                measure(sec, process)
                sleep(1)
                sec += 1
            build_end = sec

            # After the compilation
            for s in range(sec, sec + args.post_delay):
                measure(s)
                sleep(1)
            sec += args.post_delay
            delay_end = sec

            process = ssh.background("make -C llfree-linux clean")
            for s in range(sec, sec + args.post_delay):
                measure(s)
                sleep(1)
            assert process.poll() is not None
            sec += args.post_delay
            clean_end = sec

            # Shrink page cache
            ssh.run(f"echo 1 | sudo tee /proc/sys/vm/drop_caches")
            for s in range(sec, sec + args.post_delay):
                measure(s)
                sleep(1)
            sec += args.post_delay
            shrink_end = sec

            ssh.run(f"echo 1 | sudo tee /proc/sys/vm/compact_memory")
            for s in range(sec, sec + args.post_delay):
                measure(s)
                sleep(1)
            sec += args.post_delay
            compact_end = sec

            (root / f"times_{i}.json").write_text(json.dumps({
                "build": build_end, "delay": delay_end,
                "clean": clean_end, "shrink": shrink_end,
                "compact": compact_end,
            }))

    except Exception as e:
        print(e)
        if isinstance(e, CalledProcessError):
            with (root / f"error_{i}.txt").open("w+") as f:
                if e.stdout: f.write(e.stdout)
                if e.stderr: f.write(e.stderr)

        (root / "error.txt").write_text(rm_ansi_escape(non_block_read(qemu.stdout)))
        qemu.terminate()
        raise e

    (root / "out.txt").write_text(rm_ansi_escape(non_block_read(qemu.stdout)))
    print("terminate...")
    qemu.terminate()
    sleep(3)


def free_pages(buddyinfo: str) -> Tuple[int, int]:
    """Calculates the number of free small and huge pages from the buddy allocator state."""
    small = 0
    huge = 0
    for line in buddyinfo.splitlines():
        orders = line.split()[4:]
        for order, free in enumerate(orders):
            small += int(free) << order
            if order >= 9:
                huge += int(free) << (order - 9)
    return small, huge


def mem_cached(meminfo: str) -> int:
    """Returns the number of cached 4k pages"""
    for line in meminfo.splitlines():
        if line.startswith("Cached:"):
            return int(line.split()[1]) * 1024
    raise Exception("invalid meminfo")


if __name__ == "__main__":
    main()
