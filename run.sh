# qemu-system-x86_64 \
#   -m 64G \
#   -smp 8 \
#   -hda resources/hda.qcow2 \
#   -serial mon:stdio \
#   -nographic \
#   -append 'root=/dev/sda1 console=ttyS0 earlyprintk=ttyS0 nokaslr' \
#   -nic user,hostfwd=tcp:127.0.0.1:5222-:22 \
#   -s \
#   -no-reboot \
#   --cpu host,-rdtscp \
#   -enable-kvm \
#   -kernel '../nvalloc-linux/build-nvalloc-vm/arch/x86/boot/bzImage' \
#   $@
  # -smp 8,sockets=2 \
  # -numa node,cpus=0,cpus=2,cpus=4,cpus=6,nodeid=0,memdev=m0 \
  # -numa node,cpus=1,cpus=3,cpus=5,cpus=7,nodeid=1,memdev=m1 \
  # -object memory-backend-ram,size=16G,id=m0 \
  # -object memory-backend-ram,size=16G,id=m1 \
  # -kernel '../nvalloc-linux/linux/bzImage_BUDDY' \
  # -nic tap \
  # -netdev user,id=mynet \
  # -serial tcp::6666,server,nowait \
  # -curses \
  # -append 'root=/dev/sda1 console=ttyS0' \
  # -kernel ../linux/arch/x86/boot/bzImage \
  # -append 'root=/dev/sda1 ro console=ttyS0 kgdbwait kgdboc=ttyS1 nokaslr' \
  # -append 'console=ttyS0' \
  # -nic user,id=nic0,smb=$PWD \

qemu-system-x86_64 -m 128G -smp 32,sockets=2 -hda resources/hda.qcow2 -serial mon:stdio -nographic -kernel ../nvalloc-linux/build-buddy-vm/arch/x86/boot/bzImage -append 'root=/dev/sda1 console=ttyS0 nokaslr' -nic user,hostfwd=tcp:127.0.0.1:5222-:22 -no-reboot -enable-kvm --cpu host,-rdtscp -numa node,cpus=0,cpus=2,cpus=4,cpus=6,cpus=8,cpus=10,cpus=12,cpus=14,cpus=16,cpus=18,cpus=20,cpus=22,cpus=24,cpus=26,cpus=28,cpus=30,nodeid=0,memdev=m0 -numa node,cpus=1,cpus=3,cpus=5,cpus=7,cpus=9,cpus=11,cpus=13,cpus=15,cpus=17,cpus=19,cpus=21,cpus=23,cpus=25,cpus=27,cpus=29,cpus=31,nodeid=1,memdev=m1 -object memory-backend-ram,size=64G,id=m0 -object memory-backend-ram,size=64G,id=m1
