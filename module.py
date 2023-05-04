from argparse import ArgumentParser
from time import sleep, time
from subprocess import Popen, PIPE, STDOUT, check_call
from utils import non_block_read, rm_ansi_escape, setup


def main():
    parser = ArgumentParser(description="Running the module benchmarks")
    parser.add_argument("--user", default="halbuer")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=22, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("-o", "--orders", type=int, default=0, nargs="+")
    parser.add_argument("--node", type=int, default=0)
    parser.add_argument("--module")
    parser.add_argument("--kernel", required=False)
    parser.add_argument("benches", type=str, nargs="+")
    args, root = setup("module", parser, custom="local")

    dmesgp = Popen(["sudo dmesg --follow"], stdout=PIPE,
                   stderr=STDOUT, text=True, shell=True)

    with (root / "boot.txt").open("w+") as f:
        f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))

    for bench in args.benches:
        dir = root / bench
        dir.mkdir(parents=True, exist_ok=True)

        print(f"bench {bench}")

        try:
            for order in args.orders:
                allocs = (((args.mem * (512 ** 2)) //
                          max(args.cores)) // 2) // (1 << order)
                core_list = ','.join([str(c) for c in args.cores])
                print(
                    f"run ({allocs} on {core_list} o={order} i={args.iterations})")

                benchp = Popen(
                    [f"echo '{bench} {args.iterations} {allocs} {order} {core_list} {args.node}' | sudo tee /proc/alloc/run"], shell=True)

                timeout = time() + 600.0  # seconds
                while benchp.poll() is None:
                    sleep(5)
                    with (dir / "running.txt").open("a+") as f:
                        f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))
                    if time() > timeout:
                        print("Timeout..killing benchmark")
                        benchp.kill()
                        raise TimeoutError()

                sleep(1)

                with (dir / "running.txt").open("a+") as f:
                    f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))

                print("save out")
                check_call(
                    [f"sudo cat /proc/alloc/out | tee {dir}/out_{order}.csv"], shell=True)

        except Exception as e:
            with (dir / "error.txt").open("w+") as f:
                f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))
            dmesgp.send_signal(2)
            raise e

        with (dir / "running.txt").open("a+") as f:
            f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))

        print("terminate...")
        dmesgp.send_signal(2)
        sleep(3)


if __name__ == "__main__":
    main()
