# Building the Linux Kernel

## Building on MacOS

```
brew install llvm
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
```

### Building config:

```
make LLVM=/opt/homebrew/opt/llvm ARCH=x86_64 CROSS_COMPILE=x86_64-unknown-linux-gnu- defconfig
```

## Docker Debian

```
make LLVM=1 ARCH=x86_64 defconfig
# Activate KGDB...
make LLVM=1 ARCH=x86_64 menuconfig
make LLVM=1 ARCH=x86_64 -j6
```

Run qemu on host.

Connect to kgdb on docker using:
```
target remote docker.for.mac.host.internal:1234
```

## Running QEMU

- https://www.josehu.com/memo/2021/01/02/linux-kernel-build-debug.html
- buildroot...
  - probably better in docker container
