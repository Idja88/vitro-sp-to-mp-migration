import requests
import json
import os
from requests_ntlm import HttpNtlmAuth

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(ROOT_DIR, 'config.json')

with open(config_path) as config_file:
    config = json.load(config_file)
    spconfig = config['sp']
    mpconfig = config['mp']

sp_login = HttpNtlmAuth(spconfig['user'], spconfig['password'])
sp_url = spconfig['url']
sp_list = spconfig['list']
sp_headers = {'Accept': 'application/json;odata=verbose',"content-type": "application/json;odata=verbose"}

mp_login = {'login': mpconfig['user'], 'password': mpconfig['password']}
mp_url = mpconfig['url']

def get_sp_token(sp_url, sp_login, sp_headers):
    url_string = f"{sp_url}/_api/contextinfo"
    try:
        with requests.post(url=url_string, auth=sp_login, headers=sp_headers) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            value = response_json['d']['GetContextWebInformation']['FormDigestValue']
            return value
    except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
            return None

def get_sp_list_item(sp_url, sp_login, sp_headers, sp_list):
    url_string = f"{sp_url}/_api/web/lists('{sp_list}')/items"
    get_headers = sp_headers.copy()
    get_headers['X-RequestDigest'] = get_sp_token(sp_url, sp_login, sp_headers)
    try:
        with requests.get(url=url_string, auth=sp_login, headers=get_headers) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            value = response_json["d"]["results"]
            return value
    except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
            return None

def get_mp_token(mp_url, mp_login):
    url_string = f"{mp_url}/api/security/login"
    try:
        with requests.post(url=url_string, json=mp_login) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            value = response_json['token']
            return value
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def update_mp_list(token, data):
    url_string = f"{mp_url}/api/item/update"
    item_list_json = json.dumps([data])
    item_update_request = {'itemListJson': item_list_json}
    try:
        with requests.post(url=url_string, headers={'Authorization': token}, data=item_update_request) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            return response_json
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

data_list = get_sp_list_item(sp_url, sp_headers, sp_list)

processed_data = []
for item in data_list:
    processed_item = {
        "list_id": mpconfig['list'],
        "content_type_id": mpconfig['content_type'],
        "name": item.get('Title'),
        "code": item.get('VitroBaseCode'),
        "translit": item.get('VitroBaseTranslit'),
        "is_for_cypher": item.get('DocumentTypeIsForCypher')
    }
    processed_data.append(processed_item)

mp_token = get_mp_token(mp_url, mp_login)

for element in processed_data:
    update_mp_list(mp_token, element)