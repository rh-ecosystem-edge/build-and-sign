import json
import os
import md5mod
import urllib.request
import read_argfile

# Download driver_info_file from argfile.conf
config = read_key_value_file()
DRIVER_VER_JSON = config.get("DRIVER_VER_JSON", "Key 'DRIVER_VER_JSON' not found.")
download_dir = "/vendor"
os.makedirs(download_dir, exist_ok=True)

# Sources for kernel versions and driver versions
driver_info_file = download_file(DRIVER_VER_JSON, os.path.join(download_dir, os.path.basename(DRIVER_VER_JSON))) if DRIVER_VER_JSON.startswith("http") else "Invalid URL"
#driver_info_file = "data/driver-list.json"
kernel_versions_file = "data/kernel-list.json"
matrix_file = "data/combined_output.json"

# Load the driver versions JSON
with open(driver_info_file, 'r') as driver_file:
    driver_data = json.load(driver_file)

# Load the DTK JSON of kernel versions available
with open(kernel_versions_file, 'r') as kernel_file:
    kernel_data = json.load(kernel_file)

# Check if the combined JSON file already exists
if os.path.exists(matrix_file):
    # Load the existing combined data
    with open(matrix_file, 'r') as combined_file:
        combined_data = json.load(combined_file)
else:
    # Initialize an empty list if the file doesn't exist
    combined_data = []

# Create a set of existing combinations for quick lookup
existing_combinations = set()
for entry in combined_data:
    combination_key = (entry["DRIVER_VERSION"], entry["KERNEL_VERSION"])
    existing_combinations.add(combination_key)

# Iterate over each driver version
for driver in driver_data:
    # Iterate over each kernel version
    for kernel_version, kernel_checksum in kernel_data.items():
        # Create a unique key for the combination
        combination_key = (driver["VERSION"], kernel_version)

        # Check if the combination already exists
        if combination_key not in existing_combinations:
            combined_entry = {
                "DRIVER_VERSION": driver["VERSION"],
                "KERNEL_VERSION": kernel_version,
                "KERNEL_CHECKSUM": kernel_checksum,
                "DRIVER_URL": driver["URL"],
                "DRIVER_RELEASE_DATE": driver["RELEASE_DATE"],
                "DRIVER_PUBLISHED": driver["PUBLISHED"],
                "DRIVER_CHECKSUM": driver["CHECKSUM"],
                "DRIVER_STATUS": driver["DRIVER_STATUS"],
                "ARCH": driver["ARCH"],
                "TAGS": driver["TAGS"]
            }
            # Append the combined entry to the list
            combined_data.append(combined_entry)
            # Add the combination to the set of existing combinations
            existing_combinations.add(combination_key)

# Write the combined matrix data to the JSON file
with open(matrix_file, 'w') as combined_file:
    json.dump(combined_data, combined_file, indent=4)


print("Matrix JSON file updated successfully!")
# Generate MD5 checksum for matrix.json
md5mod.createmd5(matrix_file)
