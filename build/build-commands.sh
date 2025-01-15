#!/usr/bin/env bash
BUILD_KERNEL_VER=$(cat /tmp/BUILD_KERNEL_VER)
log_error() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') ERROR: $@" >&2
}

if ! make modules -j$(nproc) SYSSRC=/usr/src/kernels/$BUILD_KERNEL_VER; then
    log_error "The build command failed."
    exit 1
fi

echo "The build command completed."
