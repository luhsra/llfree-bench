from datetime import datetime
import fcntl
import os
import re
from subprocess import Popen, PIPE, STDOUT, check_call, check_output
from time import sleep
from typing import IO, List


ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def timestamp() -> str:
    return datetime.now().strftime("%y%m%d-%H%M%S")


def rm_ansi_escape(input: str) -> str:
    return ANSI_ESCAPE.sub("", input)


def non_block_read(output: IO[str]) -> str:
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""


def qemu_vm(kernel: str, mem: int, cores: int, port: int, delay: int = 15) -> Popen:
    qemu = Popen([
        "qemu-system-x86_64",
        "-m", f"{mem}G",
        "-smp", f"{cores}",
        "-hda", "resources/hda.qcow2",
        "-serial", "mon:stdio",
        "-nographic",
        "-kernel", kernel,
        "-append", "root=/dev/sda1 console=ttyS0 nokaslr",
        "-nic", f"user,hostfwd=tcp:127.0.0.1:{port}-:22",
        "-no-reboot",
        "--cpu", "host,-rdtscp",
        "-enable-kvm",
    ], stdout=PIPE, stderr=STDOUT, text=True)

    # wait for startup
    sleep(delay)

    return qemu


class SSHExec:
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
        args: List[str] | None = None
    ) -> str | None:
        if not args:
            args = []
        if output:
            return check_output([*self._ssh(), *args, cmd],
                                text=True, stderr=STDOUT, timeout=timeout)
        else:
            check_call([*self._ssh(), *args, cmd], timeout=timeout)
