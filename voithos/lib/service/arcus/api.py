""" lib for arcus services """

import os

import requests
import mysql.connector as connector

from voithos.lib.docker import env_string, volume_opt
from voithos.lib.system import shell, error, assert_path_exists
from voithos.constants import DEV_MODE


def start(
    release,
    fqdn,
    rabbit_pass,
    rabbit_ips_list,
    sql_ip,
    sql_password,
    https,
    port,
    secret,
):
    """ Start the arcus api """
    image = f"breqwatr/arcus-api:{release}"
    rabbit_ips_csv = ",".join(rabbit_ips_list)
    env_vars = {
        "OPENSTACK_VIP": fqdn,
        "PUBLIC_ENDPOINT": "true",
        "HTTPS_OPENSTACK_APIS": str(https).lower(),
        "RABBITMQ_USERNAME": "openstack",
        "RABBITMQ_PASSWORD": rabbit_pass,
        "RABBIT_IPS_CSV": rabbit_ips_csv,
        "SQL_USERNAME": "arcus",
        "SQL_PASSWORD": sql_password,
        "SQL_IP": sql_ip,
        "ARCUS_INTEGRATION_SECRET": secret,
    }
    env_str = env_string(env_vars)
    daemon = "-d --restart=always"
    run = ""
    dev_mount = ""
    ceph_mount = ""
    network = "--network host"
    log_mount = "-v /var/log/arcus-api:/var/log/arcusweb"
    hosts_mount = "-v /etc/hosts:/etc/hosts"
    if DEV_MODE:
        log_mount = ""
        hosts_mount = ""
        if "ARCUS_API_DIR" not in os.environ:
            error("ERROR: must set $ARCUS_API_DIR when $VOITHOS_DEV==true", exit=True)
        api_dir = os.environ["ARCUS_API_DIR"]
        assert_path_exists(api_dir)
        daemon = "-it --rm"
        dev_mount = volume_opt(api_dir, "/app")
        network = f"-p 0.0.0.0:{port}:{port}"
        run = (
            'bash -c "'
            "/env_config.py && "
            "pip install -e . && "
            "gunicorn --workers 4 --error-logfile=- --access-logfile '-' "
            "--reload "
            f"--bind 0.0.0.0:{port}"
            ' arcusapi.wsgi:app" '
        )
    name = "arcus_api"
    shell(f"docker rm -f {name} 2>/dev/null || true")
    cmd = (
        f"docker run --name {name} {daemon} {network} "
        f"{hosts_mount} {log_mount} "
        f"{env_str} {ceph_mount} {dev_mount} {image} {run}"
    )
    shell(cmd)


def _create_arcus_database(cursor):
    """ Create the database named arcus if it doesn't exist """
    cursor.execute("SHOW DATABASES;")
    databases = cursor.fetchall()
    if ("arcus",) in databases:
        return False
    cursor.execute("CREATE DATABASE arcus;")
    return True


def _create_arcus_dbuser(cursor, password):
    """ Create the arcus user in the DB """
    cursor.execute("SELECT user FROM mysql.user;")
    users = cursor.fetchall()
    if (bytearray(b"arcus"),) in users:
        return False
    create_cmd = f'CREATE USER arcus IDENTIFIED BY "{password}"'.format(password)
    cursor.execute(create_cmd)
    grant_cmd = 'GRANT ALL privileges ON arcus.* TO "arcus";'
    cursor.execute(grant_cmd)
    grant_cinder = 'GRANT ALL privileges ON cinder.* TO "arcus";'
    cursor.execute(grant_cinder)
    grant_nova = 'GRANT ALL privileges ON nova.* TO "arcus";'
    cursor.execute(grant_nova)
    return True


def init_database(host, admin_user, admin_passwd, arcus_passwd):
    """ Initialize the Arcus database """
    conn = connector.connect(host=host, user=admin_user, passwd=admin_passwd)
    cursor = conn.cursor()
    created_db = _create_arcus_database(cursor)
    created_user = _create_arcus_dbuser(cursor, arcus_passwd)
    return {"created_db": created_db, "created_user": created_user}


def _get_token(api_url, username, password):
    """ Get openstack token """
    token_url = f'{api_url}/auth/token'
    req_data = {
        'username': username,
        'password': password,
        'domain_name': "default"}
    token_response = requests.post(token_url, json=req_data, verify=False)
    response_headers = token_response.headers
    token_header_name = "X-Subject-Token"
    if token_header_name not in response_headers:
        error("ERROR: Failed to get token - Authentication failed.", exit=True)
    return response_headers[token_header_name]


def _get_projects(fqdn, token):
    """ Get the projects visible to this scope """
    projects_url = f"{fqdn}/auth/projects"
    projects_headers = {'X-Auth-Token': token}
    projects_response = requests.get(projects_url, headers=projects_headers, verify=False)
    return projects_response.json()["projects"]


def get_http_auth_headers(username, password, api_url):
    """ Return the headers for admin scope requests """
    token = _get_token(api_url, username, password)
    projects = _get_projects(api_url, token)
    admin_project = next((proj for proj in projects if proj["name"] == "admin"), None)
    if admin_project is None:
        error("ERROR: No 'admin' project found - check roles?", exit=True)
    return {"X-Auth-Token": token, "X-Project-ID": admin_project["id"]}


def set_service_account(auth_url, username, password, api_url):
    """ Set/create the openstack service account for Arcus API """
    headers = get_http_auth_headers(username, password, api_url)
    intgs_url = f"{api_url}/integrations"
    list_resp = requests.get(intgs_url, headers=headers, verify=False)
    intgs = list_resp.json()["integrations"] if "integrations" in list_resp.json() else []
    sa_intg = next((intg for intg in intgs if intg["type"] == "Openstacksa"), None)
    sa_exists = sa_intg is not None
    sa_data = {
        "type": "Openstacksa",
        "fields": {
            "display_name": "Openstack Service Account",
            "username": username,
            "password": password,
            "auth_url": auth_url
        }
    }
    if sa_exists:
        print("Updating existing SA record.")
        intg_id = sa_intg["id"]
        sa_data["id"] = intg_id
        patch_url = f"{intgs_url}/{intg_id}"
        requests.patch(patch_url, headers=headers, json=sa_data, verify=False)
        return
    print("No SA record found. Inserting new one.")
    requests.post(intgs_url, headers=headers, json=sa_data, verify=False)
