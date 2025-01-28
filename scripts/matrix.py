import json
import md5mod

# File paths for the input JSON files
driver_info_file = "data/driver-list.json"
kernel_versions_file = "data/kernel-list.json"
matrix_file = "data/combined_output.json"

# Load JSON data from files
with open(driver_info_file, "r") as driver_file:
    driver_info_json = json.load(driver_file)  # List of drivers

with open(kernel_versions_file, "r") as kernel_file:
    kernel_versions_json = json.load(kernel_file)  # Dict of kernel versions and checksums

# Load the combined output if it already exists to avoid rewriting
try:
    with open(matrix_file, "r") as existing_output:
        combined_json = json.load(existing_output)
except FileNotFoundError:
    combined_json = {"KERNELS": []}

# Track existing kernel versions to avoid duplication
existing_kernels = {entry["KERNEL_VERSION"]: entry for entry in combined_json["KERNELS"]}

# Process and add new kernels and drivers
for kernel_version, kernel_checksum in kernel_versions_json.items():
    # If the kernel already exists, use it; otherwise, create a new entry
    if kernel_version in existing_kernels:
        kernel_entry = existing_kernels[kernel_version]
    else:
        kernel_entry = {
            "KERNEL_VERSION": kernel_version,
            "CHECKSUM": kernel_checksum,
            "DRIVERS": []
        }
        combined_json["KERNELS"].append(kernel_entry)
    
    # Add drivers and ensure "BUILD" is set
    for driver in driver_info_json:
        # Check if driver already exists in the current kernel
        driver_exists = any(existing_driver["VERSION"] == driver["VERSION"] for existing_driver in kernel_entry["DRIVERS"])
        
        if not driver_exists:
            # Add the driver with "BUILD: N" if it doesn't exist
            new_driver = driver.copy()
            new_driver["BUILD"] = "N"  # Add BUILD field
            kernel_entry["DRIVERS"].append(new_driver)
        else:
            # Ensure BUILD field is present in existing drivers
            for existing_driver in kernel_entry["DRIVERS"]:
                if existing_driver["VERSION"] == driver["VERSION"] and "BUILD" not in existing_driver:
                    existing_driver["BUILD"] = "N"

# Write the resulting JSON to an output file
with open(matrix_file, "w") as output:
    json.dump(combined_json, output, indent=2)

print(f"Combined JSON written to {matrix_file}")
# Generate MD5 checksum for matrix.json
md5mod.createmd5(matrix_file)

