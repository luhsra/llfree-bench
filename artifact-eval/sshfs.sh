#!/bin/bash
mkdir -p llfree_ae
sshfs -o StrictHostKeyChecking=no -p 2222 user@localhost:/home/user llfree_ae
