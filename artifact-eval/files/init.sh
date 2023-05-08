#!/bin/bash

echo 'SSH server started: use "ssh -p2222 user@localhost"'
exec /usr/sbin/sshd -D
