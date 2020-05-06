""" lib for arcus services """

from voithos.lib.docker import volume_opt
from voithos.lib.system import shell


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
    cmd = (
        "docker run -d "
        f"-p 0.0.0.0:{port}:1234 "
        "--name arcus_api "
        "--restart=always "
        f"{env_str} {image}"
    )
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
    https_port=443
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
