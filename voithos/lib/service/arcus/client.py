""" lib for arcus services """
import sys
import os

from voithos.lib.docker import volume_opt, env_string
from voithos.lib.system import shell, error, assert_path_exists
from voithos.constants import DEV_MODE


def start(
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
        "ARCUS_CLIENT_HTTP_PORT": http_port,
        "ARCUS_CLIENT_HTTPS_PORT": https_port,
    }
    env_str = env_string(env_vars)
    cert_vol_mounts = ""
    if cert_path is not None and cert_key_path is not None:
        cert_mount = volume_opt(cert_path, "/etc/nginx/haproxy.crt")
        priv_key_mount = volume_opt(cert_key_path, "/etc/nginx/haproxy.key")
        cert_vol_mounts = f" {cert_mount} {priv_key_mount} "
    daemon = "-d --restart=always"
    run = ""
    dev_mount = ""
    if DEV_MODE:
        if "ARCUS_CLIENT_DIR" not in os.environ:
            error("ERROR: must set $ARCUS_CLIENT_DIR when $VOITHOS_DEV==true", exit=True)
        client_dir = os.environ["ARCUS_CLIENT_DIR"]
        assert_path_exists(client_dir)
        run = (
            'bash -c "'
            "/env_config.py && "
            "npm install && "
            "service nginx start && "
            "grunt && "
            'tail -f /dev/null"'
        )
        sys.stdout.write("TO REBUILD, EXECUTE:\n docker exec -it arcus_client grunt rebuild\n")
        dev_mount = volume_opt(client_dir, "/app")
    name = "arcus_client"
    shell(f"docker rm -f {name} || true")
    log_mount = "-v /var/log/arcus-client:/var/log/nginx"
    hosts_mount = "-v /etc/hosts:/etc/hosts"
    cmd = (
        f"docker run --name {name} "
        f"{daemon} --network host {env_str} "
        f"{cert_vol_mounts} {dev_mount} {log_mount} {hosts_mount} "
        f"{image} {run}"
    )
    shell(cmd)


def rebuild():
    shell("docker exec -it arcus_client grunt rebuild")
