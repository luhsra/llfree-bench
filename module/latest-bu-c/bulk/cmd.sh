qemu-system-x86_64 -m 128G -smp 32,sockets=1 -hda resources/hda.qcow2 -serial mon:stdio -nographic -kernel ../nvalloc-linux/build-buddy-vm/arch/x86/boot/bzImage -append 'root=/dev/sda1 console=ttyS0 nokaslr' -nic user,hostfwd=tcp:127.0.0.1:5222-:22 -no-reboot -enable-kvm --cpu host,-rdtscp -numa node,cpus=0,cpus=1,cpus=2,cpus=3,cpus=4,cpus=5,cpus=6,cpus=7,cpus=8,cpus=9,cpus=10,cpus=11,cpus=12,cpus=13,cpus=14,cpus=15,cpus=16,cpus=17,cpus=18,cpus=19,cpus=20,cpus=21,cpus=22,cpus=23,cpus=24,cpus=25,cpus=26,cpus=27,cpus=28,cpus=29,cpus=30,cpus=31,nodeid=0,memdev=m0 -object memory-backend-ram,size=128G,id=m0