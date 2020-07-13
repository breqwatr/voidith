""" Operates grafana dashboard service """
import pathlib
import requests
from voithos.lib.system import assert_path_exists


def create(user, password, https, ip, port):
    """ Creates dashboards """
    current_file_parent_dir = pathlib.Path(__file__).parent.absolute()
    json_file_path = current_file_parent_dir / "../files/grafana/node_config.json"
    assert_path_exists(json_file_path)
    proto = "https" if https else "http"
    url = f"{proto}://{ip}:{port}/api/dashboards/import"
    with open(json_file_path) as json_file:
        post_request = requests.post(
            url,
            verify=False,
            auth=(user, password),
            headers={"Content-Type": "application/json"},
            data=json_file,
        )
        print(post_request.text)
