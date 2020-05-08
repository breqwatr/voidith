""" lib for arcus services """

import os

import mysql.connector as connector

from voithos.lib.docker import env_string
from voithos.lib.system import shell, error, assert_path_exists
from voithos.constants import DEV_MODE


def start(
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
    env_str = env_string(env_vars)
    daemon = "-d --restart=always"
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
    cmd = (
        f"docker run --name arcus_api {daemon} "
        f"-p 0.0.0.0:{port}:1234 "
        "-v /etc/hosts:/etc/hosts -v /var/log/arcus-api:/var/log/arcusweb "
        f"{env_str} {dev_mount} {image} {run}"
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
