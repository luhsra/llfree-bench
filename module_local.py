from argparse import ArgumentParser
from time import sleep, time
import shlex
import os
from subprocess import Popen, PIPE, STDOUT, check_call, check_output
from utils import SSHExec, non_block_read, qemu_vm, rm_ansi_escape, setup
import signal


def main():
    parser = ArgumentParser(description="Running the module benchmarks")
    parser.add_argument("--user", default="halbuer")
    parser.add_argument("--password", default="debian")
    parser.add_argument("--port", default=22, type=int)
    parser.add_argument("-m", "--mem", default=32, type=int)
    parser.add_argument("-c", "--cores", nargs="+", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, default=4)
    parser.add_argument("-o", "--orders", type=int, default=0, nargs="+")
    parser.add_argument("--module")
    parser.add_argument("--kernel", required=False)
    parser.add_argument("benches", type=str, nargs="+")
    args, root = setup("module", parser, custom="vm")

    ssh = SSHExec(args.user, port=args.port)
    dmesgp = Popen(["sudo dmesg --follow"], stdout=PIPE, stderr=STDOUT, text=True, shell=True)

    for bench in args.benches:
        dir = root / bench
        dir.mkdir(parents=True, exist_ok=True)


        print(f"bench {bench}")

        try:
            # print("start qemu...")
            # qemu = qemu_vm(args.kernel, args.mem, max(
            #     args.cores), args.port)

            # print("started")
            # with (dir / "cmd.sh").open("w+") as f:
            #     f.write(shlex.join(qemu.args))
            # with (dir / "boot.txt").open("w+") as f:
            #     f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

            # print("load module")
            # if args.module:
            #     ssh.upload(args.module)
            # os.system(f"sudo insmod {args.module}")

            for order in args.orders:
                print("configure")
                allocs = (((args.mem * (512 ** 2)) // max(args.cores)) // 2) // (1 << order)
                core_list = ','.join([str(c) for c in args.cores])
                print(f"allocate half the memory ({allocs} on {core_list}, o={order})")

                # with (dir / "running.txt").open("a+") as f:
                #     f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

                print(f"run order={order}")
                benchp = Popen([f"echo '{bench} {args.iterations} {allocs} {order} {core_list}' | sudo tee /proc/alloc/run"], shell=True)

                timeout = time() + 600.0 # seconds
                while benchp.poll() is None:
                    sleep(5)
                    with (root / "running.txt").open("a+") as f:
                        f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))
                    if time() > timeout:
                        print("Timeout..killing benchmark")
                        benchp.kill()
                        raise TimeoutError()
              
        


                sleep(1)

                with (root / "running.txt").open("a+") as f:
                    f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))

                # with (dir / "running.txt").open("a+") as f:
                #     f.write(rm_ansi_escape(non_block_read(qemu.stdout)))

                print("save out")
                os.system(f"sudo cat /proc/alloc/out | tee {dir}/out_{order}.csv")
                # with (dir / f"out_{order}.csv").open("w+") as f:
                #     out = os.system("sudo cat /proc/alloc/out", output=True)
                #     f.write(out)

        except Exception as e:
            # with (dir / "error.txt").open("w+") as f:
            #     f.write(rm_ansi_escape(non_block_read(qemu.stdout)))
            # qemu.terminate()
            raise e


        with (root / "running.txt").open("a+") as f:
            f.write(rm_ansi_escape(non_block_read(dmesgp.stdout)))


        print("terminate...")
        # Kill dmesg logging
        dmesgp.send_signal(2)
        # qemu.terminate()
        sleep(3)


if __name__ == "__main__":
    main()