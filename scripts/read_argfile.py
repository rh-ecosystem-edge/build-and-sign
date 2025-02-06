import os
import urllib.request

def read_key_value_file(filename="argfile.conf"):
    data = {}
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    return data

def download_file(url, save_path):
    try:
        urllib.request.urlretrieve(url, save_path)
        return save_path
    except Exception as e:
        return f"Error downloading file: {e}"
