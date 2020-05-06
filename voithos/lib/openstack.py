""" OpenStack lib """

import os

from voithos.lib.system import shell, error
from voithos.lib.docker import volume_opt


def kolla_ansible_genpwd(release):
    """ Genereate passwords.yml and print to stdout """
    cwd = os.getcwd()
    path = "/var/repos/kolla-ansible/etc/kolla/passwords.yml"
    cmd = (
        f"docker run --rm "
        f"-v {cwd}:/etc/kolla "
        f"breqwatr/kolla-ansible:{release} "
        f'bash -c "kolla-genpwd --passwords {path} '
        f'&& cp {path} /etc/kolla/passwords.yml"'
    )
    shell(cmd)


def kolla_ansible_inventory(release):
    """ Print the inventory template for the given release """
    cwd = os.getcwd()
    inventory_file = "/var/repos/kolla-ansible/ansible/inventory/multinode"
    cmd = (
        f"docker run --rm "
        f"-v {cwd}:/etc/kolla "
        f"breqwatr/kolla-ansible:{release} "
        f"cp {inventory_file} /etc/kolla/inventory"
    )
    shell(cmd)


def kolla_ansible_generate_certificates(release, passwords_path, globals_path):
    """ Genereate certificates directory """
    cwd = os.getcwd()
    cmd = (
        "docker run --rm "
        + volume_opt(globals_path, "/etc/kolla/globals.yml")
        + volume_opt(passwords_path, "/etc/kolla/passwords.yml")
        + f"-v {cwd}/certificates:/etc/kolla/certificates "
        f"breqwatr/kolla-ansible:{release} "
        f"kolla-ansible certificates"
    )
    shell(cmd)


def kolla_ansible_exec(
    release,
    inventory_path,
    globals_path,
    passwords_path,
    ssh_key_path,
    certificates_dir,
    config_dir,
    command,
):
    """ Execute kolla-ansible commands """
    valid_cmds = [
        "deploy",
        "mariadb_recovery",
        "prechecks",
        "post-deploy",
        "pull",
        "reconfigure",
        "upgrade",
        "check",
        "stop",
        "deploy-containers",
        "prune-images",
        "bootstrap-servers",
        "destroy",
        "destroy --yes-i-really-really-mean-it",
        "DEBUG",
    ]
    if command not in valid_cmds:
        error('ERROR: Invalid command "{command}" - Valid commands: {valid_cmds}', exit=True)
    config_vol = " "
    if config_dir is not None:
        config_vol = volume_opt(config_dir, "/etc/kolla/config")
    if command == "DEBUG":
        name = f"kolla-ansible-{release}"
        rm_arg = f"-d --name {name}"
        run_cmd = "tail -f /dev/null"
        shell(f"docker rm -f {name} 2>/dev/null || true")
        print(f"Starting persistent container named {name} for debugging")
    else:
        run_cmd = f"kolla-ansible {command} -i /etc/kolla/inventory"
        rm_arg = "--rm"
    cmd = (
        f"docker run {rm_arg} --network host "
        + volume_opt(inventory_path, "/etc/kolla/inventory")
        + volume_opt(globals_path, "/etc/kolla/globals.yml")
        + volume_opt(passwords_path, "/etc/kolla/passwords.yml")
        + volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
        + volume_opt(certificates_dir, "/etc/kolla/certificates")
        + config_vol
        + f"breqwatr/kolla-ansible:{release} {run_cmd}"
    )
    shell(cmd)
