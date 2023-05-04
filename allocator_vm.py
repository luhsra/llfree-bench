from argparse import ArgumentParser
import shlex
from subprocess import CalledProcessError
from time import sleep

from utils import SSHExec, non_block_read, qemu_vm, setup, rm_ansi_escape


BENCH_NAME = "allocator-bench"


def main():
    parser = ArgumentParser(
        description="Running the allocator benchmarks in a vm")
    parser.add_argument("bench", nargs="+", choices=["bulk", "repeat", "rand"])
    parser.add_argument("-a", "--alloc", nargs="+")
    parser.add_argument("-e", "--exe")
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--user", default="debian")
    parser.add_argument("--img", default="resources/hda.qcow2")
    parser.add_argument("--port", default=5222, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+",
                        type=int, required=True)
    parser.add_argument("-o", "--orders", nargs="+",
                        type=int, required=True)
    parser.add_argument("-i", "--iter", type=int, default=4)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--dax", action="store_true")
    args, root = setup("allocator", parser, custom="vm")

    ssh = SSHExec(args.user, port=args.port)

    print("Running")

    try:
        print("start qemu...")
        qemu = qemu_vm(args.kernel, args.mem, max(args.cores), args.port, hda=args.img, dax=args.dax)

        print("started")
        with (root / "cmd.sh").open("w+") as f:
            f.write(shlex.join(qemu.args))
        with (root / "boot.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

        if args.exe:
            print("Upload", args.exe)
            ssh.upload(args.exe, BENCH_NAME)

        if args.dax:
            ssh("sudo ndctl create-namespace --mode devdax --map dev -e namespace0.0 -f")
            ssh("sudo chmod ugo+rw /dev/dax0.0")

        for bench in args.bench:
            dir = root / str(bench)
            dir.mkdir(parents=True, exist_ok=True)

            if qemu.poll() is not None:
                raise Exception("Qemu crashed")

            for order in args.orders:
                print(f"Exec {bench} o={order} c={args.cores}")

                threads = ' '.join(map(lambda c: f"-x{c}", args.cores))
                max_threads = max(args.cores)

                bargs = f"./{BENCH_NAME} {bench} {' '.join(args.alloc)} {threads} -s{order} -t{max_threads} -i{args.iter} -m{args.mem} --stride {args.stride} -o out.csv"

                if args.dax:
                    bargs += f" --dax /dev/dax0.0"

                try:
                    output = ssh(bargs, output=True, timeout=2 * 60.0 * 60.0)
                    with (dir / f"out_{order}.csv").open("w+") as f:
                        f.write(ssh("cat out.csv", output=True))
                    ssh("rm out.csv")
                except CalledProcessError as e:
                    print(e.output)
                    with (dir / f"error.txt").open("w+") as f:
                        print(e.output)
                        f.write(rm_ansi_escape(e.output))
                    raise e

                with (dir / f"out_{order}.txt").open("w+") as f:
                    f.write(rm_ansi_escape(output))

    except Exception as e:
        with (root / "error.txt").open("w+") as f:
            f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
        qemu.terminate()
        raise e

    print("terminate...")
    qemu.terminate()
    sleep(3)


if __name__ == "__main__":
    main()
