# Artifact Evaluation

This document provides instructions for the artifact evaluation of the [USENIX ATC'23](https://www.usenix.org/conference/atc23/call-for-artifacts) submission.

Our artifacts are packaged in a Docker image, which includes the necessary tools to execute them.
Thus the only prerequisites for the evaluation are:

- A Linux-based system (for KVM).
  - We have tested this on Linux 6.0, 6.1, and 6.2.
- At least 8 physical cores and 32GB RAM (more is better).
  - Lower specifications should work, but the results may be less meaningful.
- Hyperthreading should be disabled for more stable results.
- A properly installed and running Docker daemon.


## Getting Started Instructions

This section aims to help you check the basic functionality of the artifact within a short time frame.
You will be guided through starting the Docker image and running the fastest of our benchmarks.

### Obtaining and Starting the Docker Image

Our Docker image is hosted on GitHub and can be pulled using the commands below.

To build the image run:

```sh
# Pull the docker image (only once)
docker pull ghcr.io/luhsra/llfree_ae:latest
```

Start the image with:

```sh
./run.sh
```

Connect to the image with:
```sh
ssh -p2222 user@localhost
```

> **TODO: Correct docker image links!**

### Running the First Benchmark

After connecting to the docker image, you can build and run the benchmarks with the `run.py` script.

The fastest benchmark is the "alloc" benchmark, which tests the allocator in userspace on a memory mapping.
Start it with the following command:

```sh
# within Docker
cd llfree-bench

./run.py bench alloc
# (about 10m)
```

This command executes the benchmarks and generates the corresponding plots.
The results can be found in the mounted `artifacts/alloc` directory on your host machine.

The raw data from your benchmark run can be found in `allocator/artifacts-*` (within the Docker container), while the data from the paper is in `allocator/latest-*`.
The metadata, such as system, environment, and benchmark parameters, can also be found in these directories.
The paper's plots are located in the `out` directory.

> Note that even though this artifact evaluation does rely heavily on virtualization, the data for the paper was obtained on raw hardware.


## Detailed Instructions

This section contains detailed information on executing all the paper's evaluation benchmarks.

### Optional: Build the Artifacts

The docker image contains the following build targets.

- **alloc**: The pure LLFree implementation that can be tested and benchmarked in userspace.
- **kernel**: The modified Linux kernel, configured and built with and without the LLFree allocator.
- **module**: The kernel module that benchmarks the Linux page allocator.

To expedite the process, the image contains pre-built artifacts.
However, if desired, they can be rebuilt with the following command:

```sh
# cd llfree-bench

./run.py build all
# (this builds two Linux kernels and usually takes 30-60m)
```

> "all" can be replaced with a specific target like "alloc", "kernel" and "module".

The build artifacts are copied into the `build-(alloc|buddy|llfree)` directories.


### Running the Benchmarks

These build targets are used for the following benchmarks:

- **alloc**: Execute the *bulk*, *rand*, and *repeat* benchmarks with the LLFree allocator in userspace (needs the *alloc* build target)
- **kernel**: Execute the *bulk*, *rand*, and *repeat* benchmarks with the buddy and LLFree allocators within the Kernel in KVM+QEMU (needs the *kernel* and *module* build targets)
- **frag**: Execute the *frag* benchmark with the buddy and LLFree allocators within the Kernel in KVM+QEMU (needs the *kernel* and *module* build targets)

They can be executed with:

```sh
# cd llfree-bench

./run.py bench all
# (about 30m)
```

> "all" can be replaced with a specific target like "alloc", "kernel" and "frag".

The plots can be found in the mounted `artifact` directory on the host, and the raw data in the `allocator/artifact-*` (alloc), `module/artifact-*` (kernel), and `frag/artifact-*` directories.


### Optional: Redrawing the Plots

To redraw the plots from the previously gathered benchmark data, run:

```sh
# cd llfree-bench

./run.py plot all
# (about 5m)
```

This command will regenerate the plots using the existing benchmark data without re-running the benchmarks.


### Exploring the Artifacts

This section might be helpful if you want to explore the contents of the docker container more easily.

The container has a running ssh server that allows you to create an `sshfs` mount.
This requires `sshfs` to be installed on your system.

```sh
# Mount the dockers home directory to your host machine
./sshfs.sh
```

Now, you can explore the `llfree_ae` directory with your file manager.
The home directory contains the following subdirectories:

- [llfree-bench](https://github.com/luhsra/llfree-bench): Collection of benchmark scripts for LLFree.
  - `allocator`: Contains the "alloc" results.
  - `module`: Contains the "kernel" results.
  - `frag`: Contains the "frag" results.
- [llfree-rs](https://github.com/luhsra/llfree-rs): The LLFree Rust implementation.
- [llfree-linux](https://github.com/luhsra/llfree-linux): The modified Linux Kernel that can be configured to use LLFree instead of the Buddy allocator.
- [linux-alloc-bench](https://github.com/luhsra/linux-alloc-bench): Kernel module for benchmarking the page allocator.
