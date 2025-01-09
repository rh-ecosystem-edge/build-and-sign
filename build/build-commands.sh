#!/usr/bin/env bash
export KVER=$(rpm -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}\n' kernel-core | tail -n 1)
make all && make install
