FROM debian:11

RUN apt-get -y update ; \
    apt-get -y install dumb-init openssh-server sudo ; \
    apt-get -y install qemu qemu-kvm ; \
    apt-get -y install python3-psutil python3-seaborn python3-pandas python3-numpy ; \
    apt-get -y install build-essential curl git vim htop ; \
    apt-get -y install libncurses-dev gawk flex bison openssl libssl-dev dkms libelf-dev libudev-dev libpci-dev libiberty-dev autoconf llvm-13 bc lld \

RUN useradd -rm -d /home/user -s /bin/bash -g root -G sudo,ssh -u 1000 user ; \
    passwd -d user ; \
    mkdir -p /run/sshd ;

RUN curl https://sh.rustup.rs -sSf | su user -c "bash -s -- -y --default-toolchain nightly" ; \
    echo 'source $HOME/.cargo/env' >> /home/user/.bashrc ;

RUN rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu

RUN su user -c "git clone --depth 1 https://github.com/luhsra/llfree-bench.git --single-branch -b atc23-artifact-eval /home/user/llfree-bench" && \
    su user -c "git clone --depth 1 https://github.com/luhsra/llfree-rs.git --single-branch -b atc23-artifact-eval /home/user/llfree-rs" && \
    su user -c "git clone --depth 1 https://github.com/luhsra/llfree-linux.git --single-branch -b atc23-artifact-eval /home/user/llfree-linux" && \
    su user -c "git clone --depth 1 https://github.com/luhsra/linux-alloc-bench.git --single-branch -b atc23-artifact-eval /home/user/linux-alloc-bench"

# Use the local llfree-rs repo
RUN sed -i -e "s/git = \"ssh:\\/\\/git@github.com\\/luhsra\\/llfree-rs.git\"/path = \"..\\/..\\/..\\/llfree-rs\\/core\"/g" /home/user/llfree-linux/mm/llfree/Cargo.toml

COPY files/halt /bin/
COPY files/sshd_config /etc/ssh/

EXPOSE 22

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/usr/sbin/sshd","-D"]
