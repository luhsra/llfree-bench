# Collection of benchmark scripts for LLFree

**Related Projects**
- Allocator: https://github.com/luhsra/llfree-rs
- Modified Linux: https://github.com/llfree-linux
- Benchmark Module: https://github.com/luhsra/linux-alloc-bench


## Usage

Before executing the benchmarks, you have to build the modified kernel and kernel modules and the allocator itself.
The vm benchmarks also need an installed qemu disk image (e.g. debian 11.3.0).

The benchmark scripts can be executed with the `max_power.sh` script to disable powersaving:

```bash
./max_power.sh python3 module.py bulk repeat -c 8 -m 32 -o 0 1 2 3 4 5 6 7 8 9 10 --kernel ../llfree-linux/build-llfree-vm/arch/x86/boot/bzImage --module ../linux-alloc-bench/alloc.ko --suffix ll-o
```

With `--help` you can see all possible cli arguments.

The results are stored in `./module/<datatime>-ll-o/`.

> This assumes that you cloned and built the allocator
> [module](https://github.com/luhsra/linux-alloc-bench)
> and that you built the [llfree-linux](https://github.com/llfree-linux) kernel in
> `../llfree-linux/build-llfree-vm/arch/x86/boot/bzImage`.
>
> You might have to change these paths accordingly.

### Benchmarks

- **allocator**: Benchmarks [LLFree](https://github.com/luhsra/llfree-rs) on a virtual memory mapping in the userspace
- **frag**: Fragmentation benchmark
- **memtier**: Running the memtier benchmark and measuring its performance
- **module**: [Kernel module](https://github.com/luhsra/linux-alloc-bench) benchmarks (bulk/repeat/rand) and [Kernel](https://github.com/llfree-linux)
- **size_counters**: Running the memtier benchmark and counting the page allocations
- **write**: Userspace [write benchmark](https://github.com/luhsra/llfree-rs/blob/main/bench/src/bin/write.rs)

> Scripts ending with `_vm` execute the benchmarks on the customized kernel in a qemu kvm.
