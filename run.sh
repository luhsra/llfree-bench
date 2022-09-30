qemu-system-x86_64 \
  -m 32G \
  -smp 8,sockets=2 \
  -hda resources/hda.qcow2 \
  -serial mon:stdio \
  -nographic \
  -append 'root=/dev/sda1 console=ttyS0 earlyprintk=ttyS0 nokaslr' \
  -nic user,hostfwd=tcp:127.0.0.1:5222-:22 \
  -s \
  -no-reboot \
  --cpu host,-rdtscp \
  -numa node,cpus=0,cpus=2,cpus=4,cpus=6,nodeid=0,memdev=m0 \
  -numa node,cpus=1,cpus=3,cpus=5,cpus=7,nodeid=1,memdev=m1 \
  -object memory-backend-ram,size=16G,id=m0 \
  -object memory-backend-ram,size=16G,id=m1 \
  -enable-kvm \
  -kernel '../nvalloc-linux/arch/x86/boot/bzImage' \
  $@
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
