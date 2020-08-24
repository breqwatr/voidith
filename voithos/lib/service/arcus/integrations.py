""" Integrations library """

import requests

import voithos.lib.service.arcus.api as api


def _get_intg_dict(intg_type, fields):
    """ Return a dictionary-format integration. Fields is a multi-arg from Click with 2 elems """
    data = {
        "type": intg_type,
        "fields": {}
    }
    for field in fields:
        data['fields'][field[0]] = field[1]
    return data


def list_types(api_addr):
    """ Query a list of the available integration types """
    url = f"{api_addr}/integrations/types"
    resp = requests.get(url, verify=False)
    return resp.json()['integration_types']


def show_type(api_addr, type_name):
    """ Get information about a specific type """
    types = list_types(api_addr)
    return next((t for t in types if t['type'] == type_name), None)


def list_integrations(api_addr, username, password):
    """ List the current integrations """
    headers = api.get_http_auth_headers(username, password, api_addr)
    resp = requests.get(f"{api_addr}/integrations", headers=headers, verify=False)
    return resp.json()['integrations']


def create_integration(api_addr, username, password, intg_type, fields):
    """ Create an integration """
    headers = api.get_http_auth_headers(username, password, api_addr)
    data = _get_intg_dict(intg_type, fields)
    resp = requests.post(f"{api_addr}/integrations", headers=headers, json=data, verify=False)
    return resp.status_code == 201
