""" Operate the OpenStack Horizon service """

from pathlib import Path

import voithos.lib.jinja2 as jinja2
from voithos.lib.system import shell, error


def start(
    ip_address, port, openstack_fqdn, keystone_url, enable_https=False, release="train"
):
    """ Generate Horizon's config files and start the container"""
    # TO DO: Support HTTPS by allowing mounts
    # ...cert: /etc/horizon/certs/horizon-cert.pem
    # ...key:  /etc/horizon/certs/horizon-key.pem
    try:
        Path("/etc/kolla/horizon").mkdir(parents=True, exist_ok=True)
    except PermissionError:
        error("ERROR: Permission denied creating /etc/kolla/horizon. Try sudo?", exit=True)
    jinja2.apply_template(
        jinja2_file="horizon/horizon.json.j2",
        output_file="/etc/kolla/horizon/config.json",
        replacements={},
    )
    jinja2.apply_template(
        jinja2_file="horizon/horizon.conf.j2",
        output_file="/etc/kolla/horizon/horizon.conf",
        replacements={"horizon_enable_tls_backend": enable_https},
    )
    jinja2.apply_template(
        jinja2_file="horizon/local_settings.j2",
        output_file="/etc/kolla/horizon/local_settings",
        replacements={"openstack_host": openstack_fqdn, "keystone_url": keystone_url},
    )
    jinja2.apply_template(
        jinja2_file="horizon/custom_local_settings.j2",
        output_file="/etc/kolla/horizon/custom_local_settings",
        replacements={},
    )
    run_cmd = (
        "docker run --name=horizon "
        f"-p {ip_address}:{port}:8088 "
        "--detach=true "
        "--env=ENABLE_CLOUDKITTY=no "
        "--env=KOLLA_BASE_DISTRO=ubuntu "
        "--env=KOLLA_DISTRO_PYTHON_VERSION=3.6 "
        "--env=ENABLE_MISTRAL=no "
        "--env=ENABLE_HEAT=yes "
        "--env=ENABLE_MAGNUM=no "
        "--env=ENABLE_SENLIN=no "
        "--env=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "
        "--env=ENABLE_FREEZER=no "
        "--env=ENABLE_SAHARA=no "
        "--env=ENABLE_CONGRESS=no "
        "--env=ENABLE_QINLING=no "
        "--env=ENABLE_SOLUM=no "
        "--env=ENABLE_MASAKARI=no "
        "--env=KOLLA_INSTALL_METATYPE=mixed "
        "--env=ENABLE_OCTAVIA=no "
        "--env=ENABLE_VITRAGE=no "
        "--env=ENABLE_FWAAS=no "
        "--env=KOLLA_CONFIG_STRATEGY=COPY_ALWAYS "
        "--env=KOLLA_INSTALL_TYPE=binary "
        "--env=DEBIAN_FRONTEND=noninteractive "
        "--env=ENABLE_NEUTRON_VPNAAS=no "
        "--env=ENABLE_SEARCHLIGHT=no "
        "--env=ENABLE_ZUN=no "
        "--env=ENABLE_MANILA=no "
        "--env=ENABLE_MURANO=no "
        "--env=ENABLE_TROVE=no "
        "--env=ENABLE_WATCHER=no "
        "--env=KOLLA_SERVICE_NAME=horizon "
        "--env=KOLLA_BASE_ARCH=x86_64 "
        "--env=PIP_TRUSTED_HOST=mirror.dfw.rax.opendev.org "
        "--env=ENABLE_KARBOR=no "
        "--env=FORCE_GENERATE=no "
        "--env=ENABLE_BLAZAR=no "
        "--env=ENABLE_IRONIC=no "
        "--env=LANG=en_US.UTF-8 "
        "--env=PIP_INDEX_URL=http://mirror.dfw.rax.opendev.org:8080/pypi/simple "
        "--env=ENABLE_DESIGNATE=no "
        "--env=ENABLE_TACKER=no "
        "--volume=kolla_logs:/var/log/kolla/:rw "
        "--volume=/etc/kolla/horizon/:/var/lib/kolla/config_files/:ro "
        "--restart=unless-stopped "
        "--log-opt max-size=50m "
        "--log-opt max-file=5 "
        f"breqwatr/ubuntu-binary-horizon:{release} "
        "kolla_start"
    )
    shell(run_cmd)
