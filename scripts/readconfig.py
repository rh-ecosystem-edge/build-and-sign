import os
import requests
import json

def call_gitlab(repo_url, token=None, page=False):
    """
        make a gitlab api call and returns the raw json it gets back
        if page=True deal with multiple potential pages coming back from the api
    """
    orig_url = repo_url

    headers = {
        "Accept": "*/*",
    }

    if token:
        headers["PRIVATE-TOKEN"] = ARTIFACT_TOKEN

    if page is True:
        repo_url+="?per_page=50"

    all_results=None
    page_number = 1
    while True:
        pr = requests.get(repo_url, headers=headers, timeout=300)

        if pr.status_code > 299:
            raise SystemExit(f'Error: Got Status {pr.status_code} from {repo_url}')

        if all_results==None:
            all_results = pr.json()
        elif isinstance(all_results, list):
            all_results += pr.json()
        elif isinstance(all_results, dict):
            all_results |= pr.json()

        ## if not paging OR this is the last page, then break
        if page is False or pr.headers.get('x-page',1) >= pr.headers.get('x-total-pages',0):
            break

        page_number += 1
        repo_url =f"{orig_url}?per_page=50&page={page_number}"

    return all_results


class KeyValueFile(dict):
    def __init__(self, filename):
        super().__init__()
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    self[key.strip()] = value.strip()

    def add_dict(self, d):
        if d is None: return
        for k,v in d.items():
            self.setdefault(k,v)



class JsonDict(dict):
    def __init__(self, file, token=None):

        if file.startswith("http"):
            data= call_gitlab(file, token=token, page=False)
        else:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    data = json.load(f)

        print(data)
        super().__init__(data)


class JsonList(list):
    def __init__(self, file, token=None):
        if file.startswith("http"):
            data = call_gitlab(file, token=token, page=False)
        else:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    data = json.load(f)
        print(data)
        #breakpoint()
        super().__init__(data)

