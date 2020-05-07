""" lib for arcus services """

import os

import mysql.connector as connector

from voithos.lib.docker import volume_opt
from voithos.lib.system import shell, error, assert_path_exists
from voithos.constants import DEV_MODE


def _get_env_string(env_vars):
    """ return a string of docker -e calls for use in docker run given a dict of env vars """
    env_str = ""
    for env_var in env_vars:
        value = env_vars[env_var]
        env_str += f" -e {env_var}={value} "
    return env_str


def start_api(
    release, fqdn, rabbit_pass, rabbit_ips_list, sql_ip, sql_password, ceph_enabled, https, port
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
        "CEPH_ENABLED": str(ceph_enabled).lower(),
    }
    env_str = _get_env_string(env_vars)
    daemon = "-d --restart=always --name arcus_api"
    run = ""
    dev_mount = ""
    if DEV_MODE:
        if "ARCUS_API_DIR" not in os.environ:
            error("ERROR: must set $ARCUS_API_DIR when $VOITHOS_DEV==true", exit=True)
        daemon = "-it --rm"
        api_dir = os.environ["ARCUS_API_DIR"]
        assert_path_exists(api_dir)
        package_dir = "/usr/local/lib/python2.7/dist-packages"
        dev_mount = (
            f"-v {api_dir}/arcusapi/:{package_dir}/arcusapi/ "
            f"-v {api_dir}/arcusctrl/:{package_dir}/arcusctrl "
            f"-v {api_dir}/lib/arcuslib:{package_dir}/lib/arcuslib "
        )
        run = (
            'bash -c "'
            "/env_config.py && "
            f"cd {package_dir} && "
            "gunicorn --timeout 7200 --error-logfile=- --access-logfile '-' "
            '--reload --bind 0.0.0.0:1234 arcusapi.wsgi:app"'
        )
    cmd = f"docker run {daemon} " f"-p 0.0.0.0:{port}:1234 " f"{env_str} {dev_mount} {image} {run}"
    shell(cmd)


def start_client(
    release,
    api_ip,
    openstack_ip,
    glance_https,
    arcus_https=False,
    cert_path=None,
    cert_key_path=None,
    http_port=80,
    https_port=443,
):
    """ Start the arcus api """
    image = f"breqwatr/arcus-client:{release}"
    env_vars = {
        "ARCUS_API_IP": api_ip,
        "ARCUS_API_PORT": "1234",
        "OPENSTACK_VIP": openstack_ip,
        "ARCUS_USE_HTTPS": arcus_https,
        "GLANCE_HTTPS": str(glance_https).lower(),
        "VERSION": release,
    }
    env_str = _get_env_string(env_vars)
    vol_str = ""
    ports = f" -p 0.0.0.0:{http_port}:80 "
    if cert_path is not None and cert_key_path is not None:
        cert_mount = volume_opt(cert_path, "/etc/nginx/haproxy.crt")
        priv_key_mount = volume_opt(cert_key_path, "/etc/nginx/haproxy.key")
        vol_str = f" {cert_mount} {priv_key_mount} "
        ports += f" -p 0.0.0.0:{https_port}:443 "
    cmd = (
        "docker run -d "
        "--name arcus_client "
        "--restart=always "
        f"{ports} {vol_str} {env_str} {image}"
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
    create_cmd = 'CREATE USER arcus IDENTIFIED BY "{}"'.format(password)
    cursor.execute(create_cmd)
    grant_cmd = 'GRANT ALL privileges ON arcus.* TO "arcus";'
    cursor.execute(grant_cmd)
    return True


def init_database(host, admin_user, admin_passwd, arcus_passwd):
    """ Initialize the Arcus database """
    conn = connector.connect(host=host, user=admin_user, passwd=admin_passwd)
    cursor = conn.cursor()
    created_db = _create_arcus_database(cursor)
    created_user = _create_arcus_dbuser(cursor, arcus_passwd)
    return {"created_db": created_db, "created_user": created_user}
