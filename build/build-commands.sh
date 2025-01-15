#!/usr/bin/env bash
log_error() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') ERROR: $@" >&2
}

if ! make modules -j$(nproc); then
    log_error "The build command failed."
    exit 1
fi

echo "The build command completed."
