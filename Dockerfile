# to run this file do
# docker build -t somename .
# docker run --rm -it -v ~/Documents:/outfile:z somename


# credit for initial dockerfile: Sebastian
# 1) build-environment: a container that sets up the build environment needed
#    to compile conjure oxide.
#
#    This stage can be used as the container for Github workflows that involve
#    building Conjure Oxide e.g. nightly releases, testing.
#
#    This uses an older version of glibc, 2.8, to ensure the build binary is
#    widely runnable on many linux systems. For more details on supported
#    systems, see manylinux_2_28 documentation.

# --platform=$TARGETPLATFORM is for podman compatibility
FROM --platform=$TARGETPLATFORM 'quay.io/pypa/manylinux_2_28' AS build-environment
ARG TARGETPLATFORM

# download wget for downloading node below, and zip for our nightly build CI.
RUN yum install -y wget zip;

# llvm / clang: for C++ dependencies (Minion, SAT) and bindgen.
# using clang not gcc as Rust's bindgen library requires libclang
RUN yum install -y llvm-toolset;

# openssl headers for Rust's openssl-sys crate
RUN yum install -y openssl-devel;

# nodejs: required to build treesitter grammar

# treesitter builds fail on the version of node found in this containers
# package manager, as it is very old. Installing node from a binary download
# instead.


# FIXME: Conjure has no linux/arm64 builds yet, so neither can we! When Conjure
# gets these, we can trivially make this container multi-platform by commenting
# out the below elif.

RUN if [ "$TARGETPLATFORM"  == "linux/amd64" ]; then ARCH="x64";\
    # elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then ARCH="arm64";\
    else exit 1; fi;\
    wget https://nodejs.org/dist/v22.16.0/node-v22.16.0-linux-${ARCH}.tar.xz &&\
    tar -xf node-v22.16.0-linux-${ARCH}.tar.xz &&\
    cp node-v22.16.0-linux-${ARCH}/bin/* /usr/local/bin &&\
    cp -r node-v22.16.0-linux-${ARCH}/share/* /usr/local/share &&\
    cp -r node-v22.16.0-linux-${ARCH}/include/* /usr/local/include &&\
    cp -r node-v22.16.0-linux-${ARCH}/lib/* /usr/local/lib &&\
    rm -rf node-v22.16.0*;



# rustup
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y;

ENV PATH="/root/.cargo/bin:$PATH"

###########################################################
# 2) builder: a container that builds conjure oxide.

FROM build-environment AS builder

# grab conjure oxide source
WORKDIR /build

RUN git clone https://www.github.com/conjure-cp/conjure-oxide

WORKDIR /build/conjure-oxide

RUN git submodule update --init --recursive;

# build the release version (no debug symbols + optimisations etc)
RUN cargo build --release --features z3-bundled;

###########################################################
# # 3) a container that contains conjure oxide and conjure.
# 
# FROM ghcr.io/conjure-cp/conjure:main
# 
# # conjure should do this already, but for forwards compatibility
# RUN mkdir -p /opt/conjure;
# ENV PATH=/opt/conjure:$PATH
# 
# WORKDIR /usr
# 
# COPY --from=builder /build/conjure-oxide/target/release/conjure-oxide /opt/conjure/conjure-oxide

FROM archlinux:latest

# Added make, gcc, numactl, parallel, and vim
RUN pacman -Syu --noconfirm zip unzip wget python3 uv clang git htop sqlite jdk-openjdk make gcc numactl parallel vim

RUN git clone https://www.github.com/conjure-cp/conjure-oxide-tester

RUN wget https://github.com/conjure-cp/conjure/releases/download/v2.6.0/conjure-v2.6.0-linux-with-solvers.zip;\
    unzip conjure-v2.6.0-linux-with-solvers.zip;

# Build and install runsolver
RUN git clone https://github.com/ozgurakgun/runsolver.git /tmp/runsolver && \
    cd /tmp/runsolver && \
    git checkout 42f77c75fc511341f475f378f7bc1e5b3d708afb && \
    cd src && \
    make && \
    cp runsolver /conjure-v2.6.0-linux-with-solvers/ && \
    rm -rf /tmp/runsolver

ENV PATH=/conjure-v2.6.0-linux-with-solvers:$PATH
COPY --from=builder /build/conjure-oxide/target/release/conjure-oxide /conjure-v2.6.0-linux-with-solvers/