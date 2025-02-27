import os
import sys
import json
import subprocess
import requests
import read_argfile

MATRIX_JSON_FILE = "data/combined_output.json"
TOKEN = os.getenv("TOKEN", "test token")
ARTIFACT_TOKEN = os.getenv("ARTIFACT_TOKEN", "gitlab token")
API = os.getenv("GITHUB_API_URL", "http://example.com")
REPO = os.getenv("GITHUB_REPOSITORY", "rh-ecosystem-edge/build-and-sign")
DEBUG = False
if "debug" in sys.argv:
    DEBUG = True

URL = API + f"/repos/{REPO}/pulls"
#DTK_REG = "quay.io/build-and-sign/pa-driver-toolkit"

if not DEBUG and TOKEN == "test token":
    raise ValueError("GITHUB_TOKEN is missing!")

if not DEBUG and ARTIFACT_TOKEN == "gitlab token":
    raise ValueError("ARTIFACT_TOKEN is missing!")

def call_git(*args, **kwargs):
    """
        wrapper for calls to git
        *args: one or more strings to be arguements to the git command
    """
    if not DEBUG:
        subprocess.run(["git"] + args, check=True)
    else:
        print(f"git {' '.join(args)}")

# Function to update the DRIVER_PUBLISHED field and DRIVER_VERSION file
def update_files(config, driver_version, kernel_version):
    """ 
        update the DRIVER_PUBLISHED field and DRIVER_VERSION file
        config: dict of config key/value pairs
    """
    # Update DRIVER_PUBLISHED field in combined JSON
    with open(MATRIX_JSON_FILE, "r") as f:
        matrix_data = json.load(f)

    for e in matrix_data:
        if e["DRIVER_VERSION"] == driver_version and e["KERNEL_VERSION"] == kernel_version:
            e["DRIVER_PUBLISHED"] = "Y"
            break

    if DEBUG:
        print(f"writing to {MATRIX_JSON_FILE} and {ARGSFILE}")

    with open(MATRIX_JSON_FILE, "w") as f:
        json.dump(matrix_data, f, indent=4)

    dtk_reg = config['DTK_IMAGE'].split(":")[0]
    with open(ARGSFILE, "w") as f:
        for k,v in config.items():
            if k == "DRIVER_VERSION":
                f.write(f"DRIVER_VERSION={driver_version}\n")
            elif k == "DTK_IMAGE":
                dtk_image = f"{dtk_reg}:{kernel_version}"
                f.write(f"DTK_IMAGE={dtk_image}\n")
            else:
                f.write(f"{k}={v}\n")


# Function to create a new branch, commit changes, and push
def create_branch_and_pr(config, driver_version, kernel_version):
    """
        create a new branch in the build-and-sign repo for the kernel-driver combination
        and create a PR in it with updated versions of data/combined_output.json and argfile.conf
        this should then trigger a Konflux job via the .tekton/pull-request pipeline
    """
    branch_name = driver_version + "-" + kernel_version

    call_git("checkout", "-b", branch_name, check=True)

    # Config git identity
    call_git("config", "user.name", "github-actions[bot]")
    call_git("config", "user.email", "github-actions[bot]@users.noreply.github.com")

    # Update files
    update_files(config, driver_version, kernel_version)

    # Commit changes
    call_git("add", MATRIX_JSON_FILE, ARGSFILE)
    call_git("commit", "-m",
             f"Update DRIVER_PUBLISHED status and KERNEL_VERSION for {driver_version}-{kernel_version}")

    # Push branch
    call_git("push", "origin", branch_name)

    # Create the PR for each commit
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "title": f"Automated build-and-sign PR for {branch_name}",
        "body": f"This PR was created automatically by GitHub Actions to \
                    trigger a new build and sign of {branch_name}.",
        "head": f"{branch_name}",
        "base": "main"
     }
    if not DEBUG:
        pr = requests.post(URL, headers=headers, json=data, timeout=300)
        if pr.status_code == 201:
            print(pr.json)
        else:
            raise SystemExit(f'Error: Got Status {pr.status_code}.')
    else:
        print(f"REQUEST: {data} | Headers: {headers} | Data: {data} | URL: {URL}\n")


def get_entries_to_process(config, combined_data):
    """
    Calculate which entries need to be (re)built and published
    """
    if DEBUG:
        return combined_data

    to_build = {combo['DRIVER_VERSION'] + "-" + combo['KERNEL_VERSION']: combo
                                    for combo in combined_data}

    repo_url = config["UPLOAD_ARTIFACT_REPO_API"]
    response = call_gitlab(repo_url, page=True)

    repo_files = [file['name'] for file in response]

    kmod_name = config['DRIVER_VENDOR']
    kmod_name_len = len(kmod_name)+1
    for file in repo_files:
        if file.startswith(kmod_name):
            out=file[kmod_name_len:-7]
            if to_build.get(out):
                print(f"already built {out}")
                del to_build[out]

    return to_build.values()


def call_gitlab(repo_url, page=False):
    """
        make a gitlab api call and returns the raw json it gets back
        if page=True deal with multiple potential pages coming back from the api
    """
    orig_url = repo_url

    headers = {
        "Accept": "*/*",
        "PRIVATE-TOKEN": ARTIFACT_TOKEN,
    }
    if page is True:
        repo_url+="?per_page=50"

    all_results=[]
    page_number = 1
    while True:
        pr = requests.get(repo_url, headers=headers, timeout=300)

        if pr.status_code > 299:
            raise SystemExit(f'Error: Got Status {pr.status_code} from {repo_url}')
        all_results += pr.json()

        ## if not paging OR this is the last page, then break
        if page is False or pr.headers.get('x-page',1) >= pr.headers.get('x-total-pages',0):
            break

        page_number += 1
        repo_url =f"{orig_url}?per_page=50&page={page_number}"

    return all_results


# Main script
if __name__ == "__main__":
    config_dict = read_argfile.read_key_value_file()

    # Load current combined JSON data
    with open(MATRIX_JSON_FILE, "r") as matrix_fh:
        combined_data = json.load(matrix_fh)

    # Find entries ithat have not yet been built
    entries_to_process = get_entries_to_process(config_dict, combined_data)

    if not entries_to_process:
        print("No entries found needing building. Exiting.")
        sys.exit(0)

    # Process each entry
    for entry in entries_to_process:
        driver = entry["DRIVER_VERSION"]
        kernel = entry["KERNEL_VERSION"]
        print(f"Processing entry: {driver}-{kernel}")

        # Create a new branch, update files, and push changes
        create_branch_and_pr(config_dict, driver, kernel)
