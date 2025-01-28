import requests
import json
import hashlib
import subprocess
import md5mod 

dtk_registry_api = "https://quay.io/v1/repositories/build-and-sign/pa-driver-toolkit/tags"
# Get DTK tags
response = requests.get(dtk_registry_api)
kernel_json = (response.json())
kernel_list = "data/kernel-list.json"
# Save tags in file
with open(kernel_list, "w+") as output:
    json.dump(kernel_json, output)
# Generate MD5 checksum for kernel-list.json
md5mod.createmd5(kernel_list)
