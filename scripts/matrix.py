import json

# File paths for the input JSON files
driver_info_file = "data/driver-list.json"
kernel_versions_file = "data/kernel-list.json"
output_file = "data/combined_output.json"

# Load JSON data from files
with open(driver_info_file, "r") as driver_file:
    driver_info_json = json.load(driver_file)

with open(kernel_versions_file, "r") as kernel_file:
    kernel_versions_json = json.load(kernel_file)

# Combine JSON into the desired format
combined_json = {"KERNELS": []}

for kernel_version, kernel_checksum in kernel_versions_json.items():
    kernel_entry = {
        "KERNEL_VERSION": kernel_version,
        "CHECKSUM": kernel_checksum,
        "DRIVERS": [driver_info_json]  # Add the driver info for each kernel
    }
    combined_json["KERNELS"].append(kernel_entry)

# Write the resulting JSON to an output file
with open(output_file, "w") as output:
    json.dump(combined_json, output, indent=2)

print(f"Combined JSON written to {output_file}")

