""" Operate the OpenStack Horizon service """

from pathlib import Path

import voithos.lib.jinja2 as jinja2
from voithos.lib.system import shell, error


def start(
    ip_address,
    port,
    internal_vip,
    control_node_ip,
    release="train",
    conf_dir="/etc/kolla/horizon",
    name="horizon",
):
    """ Generate Horizon's config files and start the container"""
    # TO DO: Support HTTPS by allowing mounts
    # ...cert: /etc/horizon/certs/horizon-cert.pem
    # ...key:  /etc/horizon/certs/horizon-key.pem
    try:
        Path(conf_dir).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        error("ERROR: Permission denied creating /etc/kolla/horizon. Try sudo?", exit=True)
    jinja2.apply_template(
        jinja2_file="horizon/horizon.json.j2",
        output_file=f"{conf_dir}/config.json",
        replacements={},
    )
    jinja2.apply_template(
        jinja2_file="horizon/horizon.conf.j2",
        output_file=f"{conf_dir}/horizon.conf",
        replacements={
            "ip_address": ip_address,
            "port": port
        },
    )
    jinja2.apply_template(
        jinja2_file="horizon/local_settings.j2",
        output_file=f"{conf_dir}/local_settings",
        replacements={"internal_vip": internal_vip, "control_node_ip": control_node_ip},
    )
    jinja2.apply_template(
        jinja2_file="horizon/custom_local_settings.j2",
        output_file=f"{conf_dir}/custom_local_settings",
        replacements={},
    )
    run_cmd = (
        f"docker run --name={name} "
        "--hostname=voithos "
        "--env=ENABLE_CLOUDKITTY=no "
        "--env=ENABLE_MANILA=no "
        "--env=ENABLE_SENLIN=no "
        "--env=ENABLE_OCTAVIA=no "
        "--env=ENABLE_MISTRAL=no "
        "--env=KOLLA_INSTALL_TYPE=binary "
        "--env='PS1=$(tput bold)($(printenv KOLLA_SERVICE_NAME))$(tput sgr0)[$(id -un)@$(hostname -s) $(pwd)]$ ' "
        "--env=ENABLE_FREEZER=no "
        "--env=ENABLE_HEAT=yes "
        "--env=KOLLA_INSTALL_METATYPE=rdo "
        "--env=KOLLA_DISTRO_PYTHON_VERSION=3.6 "
        "--env=ENABLE_FWAAS=no "
        "--env=KOLLA_CONFIG_STRATEGY=COPY_ALWAYS "
        "--env=ENABLE_SOLUM=no "
        "--env=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "
        "--env=KOLLA_BASE_ARCH=x86_64 "
        "--env=ENABLE_NEUTRON_VPNAAS=no "
        "--env=ENABLE_BLAZAR=no "
        "--env=ENABLE_MASAKARI=no "
        "--env=ENABLE_QINLING=no "
        "--env=ENABLE_ZUN=no "
        "--env=ENABLE_SAHARA=no "
        "--env=ENABLE_CONGRESS=no "
        "--env=ENABLE_IRONIC=no "
        "--env=ENABLE_WATCHER=no "
        "--env=KOLLA_SERVICE_NAME=horizon "
        "--env=PIP_INDEX_URL=http://mirror.bhs1.ovh.opendev.org:8080/pypi/simple "
        "--env=ENABLE_TROVE=no "
        "--env=ENABLE_VITRAGE=no "
        "--env=KOLLA_BASE_DISTRO=ubuntu "
        "--env=DEBIAN_FRONTEND=noninteractive "
        "--env=ENABLE_DESIGNATE=no "
        "--env=ENABLE_MAGNUM=no "
        "--env=ENABLE_TACKER=no "
        "--env=PIP_TRUSTED_HOST=mirror.bhs1.ovh.opendev.org "
        "--env=PIP_EXTRA_INDEX_URL=https://mirror.bhs1.ovh.opendev.org/wheel/ubuntu-18.04-x86_64 "
        "--env=ENABLE_KARBOR=no "
        "--env=ENABLE_SEARCHLIGHT=no "
        "--env=LANG=en_US.UTF-8 "
        "--env=ENABLE_MURANO=no "
        "--env=FORCE_GENERATE=no "
        "--volume=/etc/timezone:/etc/timezone:ro "
        "--volume=/tmp:/tmp:rw "
        "--volume=kolla_logs:/var/log/kolla/:rw "
        "--volume=/etc/localtime:/etc/localtime:ro "
        f"--volume={conf_dir}/:/var/lib/kolla/config_files/:ro "
        "--volume=/etc/localtime "
        "--volume=/etc/timezone "
        "--volume=/tmp "
        "--volume=/var/lib/kolla/config_files/ "
        "--volume=/var/log/kolla/ "
        "--network=host "
        "--restart=unless-stopped "
        "--label kolla_version=9.2.1 "
        "--label build-date=20200812 "
        "--label maintainer='Kolla Project (https://launchpad.net/kolla)' "
        "--label name=horizon "
        "--log-opt max-size=50m "
        "--log-opt max-file=5 "
        "--detach=true "
        f"kolla/ubuntu-binary-horizon:{release} "
        "kolla_start "
    )
    shell(run_cmd)
