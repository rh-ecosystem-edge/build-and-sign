import sys
import re
import json

from readconfig import KeyValueFile, JsonList, JsonDict

DEBUG = False
if "debug" in sys.argv:
    DEBUG = True
MATRIX_FILE = "data/combined_output.json"

config = KeyValueFile("argfile.conf")

vendordata = JsonList(config.get('DRIVER_VER_JSON', "driver-list.json"),
                        config.get('DRIVER_VER_TOKEN', None))

kerneldata = JsonDict(config.get('KERNEL_VERSION_LIST', 'data/kernel-list.json'))

combined_data = {}
for build in vendordata:
    for kernel in kerneldata.keys():
        arch = kernel.split('.')[-1]
        if build['ARCH'] != arch:
            continue
        if build.get('BLACKLIST') is not None and re.match(build['BLACKLIST'], kernel):
            print(f"blacklist={kernel}")
            #breakpoint()
            continue
        if build.get('WHITELIST') and not re.match(build['WHITELIST'], kernel):
            continue

        if DEBUG:
            print(f"BUILD {build['VERSION']} for {kernel} in {build.get('WHITELIST')} not in {build.get('BLACKLIST')}" )

        combined_data[(build["VERSION"], kernel)] = {
            "DRIVER_VERSION": build["VERSION"],
            "KERNEL_VERSION": kernel,
            "KERNEL_CHECKSUM": kerneldata[kernel],
            "DRIVER_URL": config["DRIVER_REPO"],
            "DRIVER_COMMIT": build.get("BRANCH", "main"),
            "DRIVER_RELEASE_DATE": build["RELEASE_DATE"],
            "ARCH": build["ARCH"],
            "DRIVER_PUBLISHED": build["PUBLISHED"],
            "DRIVER_CHECKSUM": build["CHECKSUM"],
            "DRIVER_STATUS": build["DRIVER_STATUS"],
            "TAGS": build["TAGS"]
        }

if DEBUG:
    print(json.dumps(list(combined_data.values()), indent=4))

# Write the combined matrix data to the JSON file
with open(MATRIX_FILE, 'w') as combined_file:
    json.dump(list(combined_data.values()), combined_file, indent=4)
