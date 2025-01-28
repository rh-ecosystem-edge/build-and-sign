import json
import subprocess

# File paths
matrix_json_file = "data/combined_output.json"
argsfile = "argfile.conf"

# Function to update the DRIVER_PUBLISHED field and DRIVER_VERSION file
def update_files(driver_version, kernel_version):
    # Update DRIVER_PUBLISHED field in combined JSON
    with open(matrix_json_file, "r") as f:
        combined_data = json.load(f)

    for entry in combined_data:
        if entry["DRIVER_VERSION"] == driver_version and entry["KERNEL_VERSION"] == kernel_version:
            entry["DRIVER_PUBLISHED"] = "Y"
            break

    with open(matrix_json_file, "w") as f:
        json.dump(combined_data, f, indent=4)

    # Update argsfile
    with open(argsfile, "r") as f:
        lines = f.readlines()

    with open(argsfile, "w") as f:
        for line in lines:
            if line.startswith("DRIVER_VERSION="):
                f.write(f"DRIVER_VERSION={driver_version}\n")
            else:
                f.write(line)

# Function to create a new branch, commit changes, and push
def create_branch_and_pr(driver_version, kernel_version):
    branch_name = driver_version + "-" + kernel_version
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # Update files
    update_files(driver_version, kernel_version)

    # Commit changes
    subprocess.run(["git", "add", matrix_json_file, argsfile], check=True)
    subprocess.run(["git", "commit", "-m", f"Update DRIVER_PUBLISHED status and KERNEL_VERSION for {driver_version}-{kernel_version}"], check=True)

    # Push branch
    subprocess.run(["git", "push", "origin", branch_name], check=True)

# Main script
if __name__ == "__main__":
    # Load current combined JSON data
    with open(matrix_json_file, "r") as f:
        combined_data = json.load(f)

    # Find entries with DRIVER_PUBLISHED = "N"
    entries_to_process = [entry for entry in combined_data if entry.get("DRIVER_PUBLISHED") == "N"]

    if not entries_to_process:
        print("No entries with DRIVER_PUBLISHED = 'N' found. Exiting.")
        exit(0)

    # Process each entry
    for entry in entries_to_process:
        driver_version = entry["DRIVER_VERSION"]
        kernel_version = entry["KERNEL_VERSION"]
        print(f"Processing entry: {driver_version}-{kernel_version}")

        # Create a new branch, update files, and push changes
        create_branch_and_pr(driver_version, kernel_version)
