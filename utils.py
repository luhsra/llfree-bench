from datetime import datetime
import fcntl
from itertools import chain
import os
from pathlib import Path
import re
import json
from subprocess import Popen, PIPE, STDOUT, check_call, check_output
from time import sleep
from typing import IO, Any, Dict, List, Optional, Tuple
from argparse import ArgumentParser, Namespace
import pandas as pd

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def setup(name: str, parser: ArgumentParser, custom=None) -> Tuple[Namespace, Path]:
    """
    Setup the benchmark directory and save the system config and execution parameters.

    Args:
        name: Name of the benchmark
        parser: CLI Arguments to be parsed and saved
        custom: Any custom metadata that should be saved
    """
    parser.add_argument("--suffix")
    args = parser.parse_args()
    root = Path(name) / (timestamp() +
                         (f"-{args.suffix}" if args.suffix else ""))
    root.mkdir(parents=True, exist_ok=True)
    with (root / "meta.json").open("w+") as f:
        values = {
            "args": vars(args),
            "sys": sys_info(),
        }
        if custom:
            values["custom"] = custom
        json.dump(values, f)
    return args, root


def timestamp() -> str:
    return datetime.now().strftime("%y%m%d-%H%M%S")


def rm_ansi_escape(input: str) -> str:
    return ANSI_ESCAPE.sub("", input)


def non_block_read(output: IO[str]) -> str:
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    try:
        out = output.read()
    except:
        out = ""

    fcntl.fcntl(fd, fcntl.F_SETFL, fl)
    return out


def qemu_vm(kernel: str, mem: int, cores: int, port: int,
            sockets: int = 1, delay: int = 15,
            hda: str = "resources/hda.qcow2", kvm: bool = True) -> Popen:
    """
    Start a vm with the given configuration.
    """
    assert (cores > 0 and cores % sockets == 0)
    assert (mem > 0 and mem % sockets == 0)
    assert (Path(hda).exists())

    # every nth cpu
    def cpus(i) -> str:
        return ",".join([
            f"cpus={c}" for c in range(i, cores, sockets)
        ])

    args = [
        "qemu-system-x86_64",
        "-m", f"{mem}G",
        "-smp", f"{cores},sockets={sockets}",
        "-hda", hda,
        "-serial", "mon:stdio",
        "-nographic",
        "-kernel", kernel,
        "-append", "root=/dev/sda1 console=ttyS0 nokaslr",
        "-nic", f"user,hostfwd=tcp:127.0.0.1:{port}-:22",
        "-no-reboot",
        "--cpu", "host,-rdtscp",
        *chain(*[["-numa", f"node,{cpus(i)},nodeid={i},memdev=m{i}"]
                 for i in range(sockets)]),
        *chain(*[["-object", f"memory-backend-ram,size={mem // sockets}G,id=m{i}"]
                 for i in range(sockets)]),
    ]

    if kvm:
        args.append("-enable-kvm")

    qemu = Popen(args, stdout=PIPE, stderr=STDOUT, text=True)

    # wait for startup
    sleep(delay)

    return qemu


class SSHExec:
    """
    Executing shell commands over ssh.
    """

    def __init__(self, user: str, host: str = "localhost", port: int = 22) -> None:
        self.user = user
        self.host = host
        self.port = port

    def _ssh(self) -> List[str]:
        return ["ssh", f"{self.user}@{self.host}", f"-p {self.port}"]

    def __call__(
        self,
        cmd: str,
        output: bool = False,
        timeout: float = None,
        args: Optional[List[str]] = None,
        text: bool = True
    ) -> Optional[str]:
        """Run cmd and wait for its termination"""
        if not args:
            args = []
        ssh_args = [*self._ssh(), *args, cmd]
        if output:
            return check_output(ssh_args, text=text, stderr=STDOUT, timeout=timeout)
        else:
            check_call(ssh_args, timeout=timeout)

    def background(self, cmd: str, args: Optional[List[str]] = None) -> Popen:
        """Run cmd in the background."""
        if not args:
            args = []
        ssh_args = [*self._ssh(), *args, cmd]
        return Popen(ssh_args, stdout=PIPE, stderr=STDOUT, text=True)

    def upload(self, file: str):
        """Upload a file over ssh."""
        check_call(
            ["scp", f"-P{self.port}", file, f"{self.user}@{self.host}:alloc.ko"], timeout=30)


def sys_info() -> dict:
    return {
        "uname": check_output(["uname", "-a"], text=True),
        "lscpu": json.loads(check_output(["lscpu", "--json"]))["lscpu"],
        "meminfo": mem_info(),
    }


def mem_info() -> dict:
    rows = {"MemTotal", "MemFree", "MemAvailable"}
    out = {}
    for row in open("/proc/meminfo"):
        try:
            [key, value] = list(map(lambda v: v.strip(), row.split(":")))
            if key in rows:
                out[key] = value
        except:
            pass
    return out


def dump_dref(file: IO, prefix: str, data: Dict[str, Any]):
    for key, value in data.items():
        if isinstance(value, dict):
            dump_dref(file, f"{prefix}/{key}", value)
        elif isinstance(value, list):
            dump_dref(file, f"{prefix}/{key}", dict(enumerate(data)))
        else:
            file.write(f"\\drefset{{{prefix}/{key}}}{{{value}}}\n")


def dref_dataframe(name: str, dir: Path, groupby: List[str], data: pd.DataFrame):
    out = {}
    data = data.dropna(axis=0).groupby(groupby).mean(numeric_only=True)
    for index, row in data.iterrows():
        out["/".join(map(str, index))] = row.values[0]
    with (dir / f"{name}.dref").open("w+") as f:
        dump_dref(f, name, out)
