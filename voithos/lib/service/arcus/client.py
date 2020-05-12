""" lib for arcus services """

import os

from voithos.lib.docker import volume_opt, env_string
from voithos.lib.system import shell, error, compat_path
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
    }
    env_str = env_string(env_vars)
    vol_str = ""
    ports = f" -p 0.0.0.0:{http_port}:80 "
    if cert_path is not None and cert_key_path is not None:
        cert_mount = volume_opt(cert_path, "/etc/nginx/haproxy.crt")
        priv_key_mount = volume_opt(cert_key_path, "/etc/nginx/haproxy.key")
        vol_str = f" {cert_mount} {priv_key_mount} "
        ports += f" -p 0.0.0.0:{https_port}:443 "
    daemon = "-d --restart=always"
    run = ""
    dev_mount = ""
    if DEV_MODE:
        if "ARCUS_CLIENT_DIR" not in os.environ:
            error("ERROR: must set $ARCUS_CLIENT_DIR when $VOITHOS_DEV==true", exit=True)
        client_dir = compat_path(os.environ["ARCUS_CLIENT_DIR"])
        run = (
            'bash -c "'
            "/env_config.py && "
            "npm install && "
            "service nginx start && "
            "grunt && "
            'grunt watch-changes"'
        )
        daemon = "-it --rm"
        dev_mount = f"-v {client_dir}:/app"
    name = "arcus_client"
    shell(f"docker rm -f {name} || true")
    cmd = (
        f"docker run --name {name} -v /var/log/arcus-client:/var/log/nginx "
        f"{daemon} {ports} {env_str} "
        f"{vol_str} {dev_mount} -v /etc/hosts:/etc/hosts "
        f"{image} {run}"
    )
    shell(cmd)
