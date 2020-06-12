""" lib for arcus services """

import os

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
    ceph_enabled,
    ceph_dir,
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
        "CEPH_ENABLED": str(ceph_enabled).lower(),
        "ARCUS_INTEGRATION_SECRET": secret,
    }
    env_str = env_string(env_vars)
    daemon = "-d --restart=always"
    run = ""
    dev_mount = ""
    ceph_mount = ""
    if ceph_enabled:
        if ceph_dir is None:
            error("ERROR: --ceph-dir is required for --ceph", exit=True)
        ceph_mount = volume_opt(ceph_dir, "/etc/ceph")
    if DEV_MODE:
        if "ARCUS_API_DIR" not in os.environ:
            error("ERROR: must set $ARCUS_API_DIR when $VOITHOS_DEV==true", exit=True)
        api_dir = os.environ["ARCUS_API_DIR"]
        assert_path_exists(api_dir)
        daemon = "-it --rm"
        dev_mount = volume_opt(api_dir, "/app")
        run = (
            'bash -c "'
            "/env_config.py && "
            "pip install -e . && "
            "gunicorn --workers 4 --error-logfile=- --access-logfile '-' "
            '--reload --bind 0.0.0.0:1234 arcusapi.wsgi:app" '
        )
    name = "arcus_api"
    shell(f"docker rm -f {name} 2>/dev/null || true")
    log_mount = "-v /var/log/arcus-api:/var/log/arcusweb"
    hosts_mount = "-v /etc/hosts:/etc/hosts"
    cmd = (
        f"docker run --name {name} {daemon} "
        f"-p 0.0.0.0:{port}:1234 "
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
