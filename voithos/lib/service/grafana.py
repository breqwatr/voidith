""" Operates grafana dashboard service """
import json
import os
from voithos.lib.system import shell, assert_path_exists, get_absolute_path


def create(user, password, https, ip, port):
    """ Creates dashboards """
    node_config_file = "voithos/lib/files/grafana/node_config.json"
    assert_path_exists(node_config_file)
    json_file_path = get_absolute_path(node_config_file)
    https_or_http = "https" if https else "http"
    cmd = (
        f"curl \'{https_or_http}://{user}:{password}@{ip}:{port}/api/dashboards/import\'"
        f"-X POST -H \'Content-Type: application/json;charset=UTF-8\' -d @{json_file_path}"
    )
    shell(cmd)
