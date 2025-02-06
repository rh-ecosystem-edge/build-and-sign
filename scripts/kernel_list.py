import requests
import json
dtk_registry_api = "https://quay.io/v1/repositories/build-and-sign/pa-driver-toolkit/tags"
response = requests.get(dtk_registry_api)
print(response.json())

