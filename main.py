import requests
import json
import os
from requests_ntlm import HttpNtlmAuth

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

def get_sp_list_item(sp_url, sp_login, sp_headers, sp_list, sp_token, sp_content_type_id):
    url_string = f"{sp_url}/_api/web/lists('{sp_list}')/items?$filter=ContentTypeId eq '{sp_content_type_id}'"
    get_headers = sp_headers.copy()
    get_headers['X-RequestDigest'] = sp_token
    try:
        with requests.get(url=url_string, auth=sp_login, headers=get_headers) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            value = response_json["d"]["results"]
            return value
    except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
            return None

def get_sp_list_item_name(sp_url, sp_login, sp_headers, sp_list, sp_token, item_id):
    list_url = f"{sp_url}/_api/web/lists('{sp_list}')/items?$filter=ID eq '{item_id}'"
    get_headers = sp_headers.copy()
    get_headers['X-RequestDigest'] = sp_token
    try:
            with requests.get(list_url, auth=sp_login, headers=get_headers) as response:
                    response.raise_for_status()
                    response_json = json.loads(response.text)
                    value = response_json["d"]["results"]
                    return value[0]["Title"]
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

def get_mp_list_item_lookup_id(token, name, mp_list):
    url_string = f"{mp_url}/api/item/getRecursive/{mp_list}"
    filter_string = f'item => item.GetValueAsString("name") == "{name}"'
    payload = {"query": filter_string}
    try:
         with requests.post(url=url_string, headers={'Authorization': token}, json=payload) as response:
            response.raise_for_status()
            response_json = json.loads(response.text)
            if len(response_json) == 0:
                return None
            else:
                value = response_json[0]["id"]
                return value
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None
    
def process_field(item, field_config, sp_token, mp_token):
    if field_config['type'] == 'direct':
        return item.get(field_config['sp_source'])
    elif field_config['type'] == 'lookup':
        sp_lookup_id = item.get(field_config['sp_source'])
        if sp_lookup_id:
            sp_title = get_sp_list_item_name(sp_url, sp_login, sp_headers, field_config['sp_list'], sp_token, sp_lookup_id)
            return get_mp_list_item_lookup_id(mp_token, sp_title, field_config['mp_list'])
    return None

def main():
    sp_token = get_sp_token(sp_url, sp_login, sp_headers)
    mp_token = get_mp_token(mp_url, mp_login)
    
    data_list = get_sp_list_item(sp_url, sp_login, sp_headers, sp_list, sp_token, sp_content_type)

    if data_list is not None:
        processed_data = []
        for item in data_list:
            processed_item = {
                "list_id": mp_list,
                "content_type_id": mp_content_type,
            }
            for field_name, field_config in mapping_config['fields'].items():
                processed_item[field_name] = process_field(item, field_config, sp_token, mp_token)
            processed_data.append(processed_item)

        for element in processed_data:
            update_mp_list(mp_token, element)

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, 'config.json')

    with open(config_path) as config_file:
        config = json.load(config_file)
        spconfig = config['sp']
        mpconfig = config['mp']
        mapping_config = config['content_type_mapping']

    sp_login = HttpNtlmAuth(spconfig['user'], spconfig['password'])
    sp_url = spconfig['url']
    sp_list = mapping_config['sp_list']
    sp_content_type = mapping_config['sp_content']
    sp_headers = {'Accept': 'application/json;odata=verbose',"content-type": "application/json;odata=verbose"}

    mp_login = {'login': mpconfig['user'], 'password': mpconfig['password']}
    mp_url = mpconfig['url']
    mp_list = mapping_config['mp_list']
    mp_content_type = mapping_config['mp_content']

    main()