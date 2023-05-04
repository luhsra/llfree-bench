# Collection of benchmarks for NVALLOC

**Related Projects**
- Allocator: https://scm.sra.uni-hannover.de/research/nvalloc-rs
- Modified Linux: https://scm.sra.uni-hannover.de/research/nvalloc-linux
- Benchmark Module: https://scm.sra.uni-hannover.de/research/linux-alloc-bench
- Paper: https://scm.sra.uni-hannover.de/papers/2022/eurosys23-nvalloc


## Usage

Before executing the benchmarks, you have to build the modified kernel and kernel modules and the allocator itself (`vm`).
The vm benchmarks also need an installed qemu disk image (e.g. debian 11.3.0) in `vm/hda.qcow2`.

The benchmark scripts can be executed with the `max_power.sh` script to disable powersaving:

```bash
./max_power.sh python3 module.py bulk repeat -c 8 -m 128 -o 0 1 2 3 4 5 6 7 8 9 10 --kernel ../nvalloc-linux/build-nvalloc-vm/arch/x86/boot/bzImage --module ./build-nvalloc/alloc.ko --suffix ll-o
```

With `--help` you can see all possible cli arguments.

The results are stored in `./module/<datatime>-ll-o/`.

> This assumes that you built and copied the allocator
> [module](https://scm.sra.uni-hannover.de/research/linux-alloc-bench)
> to `./build-nvalloc` and that you built the nvalloc-linux kernel in
> `../nvalloc-linux/build-nvalloc-vm/arch/x86/boot/bzImage`.
>
> You might have to change these paths accordingly.

### Benchmarks

- **allocator**: Benchmarks [LLFree](https://scm.sra.uni-hannover.de/research/nvalloc-rs) on a virtual memory mapping in the userspace
- **frag**: Fragmentation benchmark
- **memtier**: Running the memtier benchmark and measuring its performance
- **module**: [Kernel module](https://scm.sra.uni-hannover.de/research/linux-alloc-bench) benchmarks (bulk/repeat/rand)
- **rand**: Userspace [random benchmark](https://scm.sra.uni-hannover.de/research/nvalloc-rs/-/blob/main/bench/src/bin/rand.rs)
- **size_counters**: Running the memtier benchmark and counting the page allocations
- **write**: Userspace [write benchmark](https://scm.sra.uni-hannover.de/research/nvalloc-rs/-/blob/main/bench/src/bin/write.rs)

> Scripts ending with `_vm` execute the benchmarks on the customized kernel in a qemu kvm.
