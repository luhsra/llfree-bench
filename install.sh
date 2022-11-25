qemu-system-x86_64 -m 4G -smp 4 \
  -hda hda.qcow2 \
  -boot d \
  -cdrom resources/debian-live-11.3.0-amd64-standard.iso \
# -enable-kvm \
# -curses \
# -nographic \
# -netdev user,id=mynet \
# -nic user,hostfwd=tcp:127.0.0.1:2222-:22

# https://wiki.debian.org/QEMU
# https://fosspost.org/tutorials/use-qemu-test-operating-systems-distributions
# https://wiki.qemu.org/Documentation/Networking
# Bootparameter
# vm 0000 (root 0000)
# User: debian debian

# Solve networking issues:
# The device might have the wrong name
# Open /etc/network/interfaces.d/setup and change the interface name to the one from `ip a`
