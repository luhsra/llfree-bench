mkdir -p artifact
docker run -p 2222:22 --device=/dev/kvm --rm ghcr.io/luhsra/llfree_ae -v "$(pwd)"/artifact:/home/user/llfree-bench/artifact
