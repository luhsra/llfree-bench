# Collection of benchmarks for NVALLOC

**Related Projects**
- https://scm.sra.uni-hannover.de/research/nvalloc-rs
- https://scm.sra.uni-hannover.de/research/nvalloc-linux
- https://scm.sra.uni-hannover.de/papers/2022/eurosys23-nvalloc


## Usage

The benchmark scripts can be executed with the `max_power.sh` script to disable powersaving:

```bash
./max_power.sh python3 module.py bulk repeat rand -c 1 2 4 8 16 24 32 -m 128 -o 1 --kernel ../nvalloc-linux/build-buddy-vm/arch/x86/boot/bzImage
```
