import json
import subprocess
import requests
import os

# File paths
matrix_json_file = "data/combined_output.json"
argsfile = "argfile.conf"
token = os.getenv("TOKEN")
api = os.getenv("GITHUB_API_URL")
dtk_reg = "quay.io/build-and-sign/pa-driver-toolkit"

if not token:
    raise ValueError("GITHUB_TOKEN is missing!")

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
            elif line.startswith("DTK_IMAGE="):
                dtk_image = f"{dtk_reg}:{kernel_version}"
                f.write(f"DTK_IMAGE={dtk_image}\n")                
            else:
                f.write(line)

# Function to create a new branch, commit changes, and push
def create_branch_and_pr(driver_version, kernel_version):
    branch_name = driver_version + "-" + kernel_version
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # Config git identity
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)

    # Update files
    update_files(driver_version, kernel_version)

    # Commit changes
    subprocess.run(["git", "add", matrix_json_file, argsfile], check=True)
    subprocess.run(["git", "commit", "-m", f"Update DRIVER_PUBLISHED status and KERNEL_VERSION for {driver_version}-{kernel_version}"], check=True)

    # Push branch
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    # Create the PR for each commit
    url = api +"/repos/rh-ecosystem-edge/build-and-sign/pulls"
    headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"            
    }
    data = {
    "title": f"Automated build-and-sign PR for {branch_name}",
    "body": f"This PR was created automatically by GitHub Actions to trigger a new build and sign of {branch_name}.",
    "head": f"{branch_name}",
    "base": "main"
     }
    #print(f"REQUEST: {title} | Headers: {headers} | Data: {data} | URL: {url}")
    pr = requests.post(url, headers=headers, json=data)
    if pr.status_code == 201:
       print(pr.json)
    else:
       raise SystemExit(f'Error: Got Status {pr.status_code}.')
    
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
