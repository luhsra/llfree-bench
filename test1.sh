qemu-system-x86_64 -m 8G \
    -smp 8 -hda resources/hda.qcow2 \
    -machine pc,accel=kvm \
    -no-reboot -enable-kvm \
    -serial mon:stdio -nographic \
    -kernel ../llfree-linux/build-llfree-vm/arch/x86/boot/bzImage \
    -append 'root=/dev/sda1 console=ttyS0 nokaslr earlyprintk=ttyS0' \
    -nic user,hostfwd=tcp:127.0.0.1:5222-:22 \
    --cpu host,-rdtscp \
    $@
