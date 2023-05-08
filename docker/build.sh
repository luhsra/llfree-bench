#!/bin/bash
cp -r ../build-alloc .
cp -r ../build-buddy .
cp -r ../build-llfree .
docker build -t ghcr.io/luhsra/llfree_ae .
rm -r ./build-alloc
rm -r ./build-buddy
rm -r ./build-llfree
