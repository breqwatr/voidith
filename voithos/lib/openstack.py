""" OpenStack lib """

import os

from click import echo

from voithos.lib.system import shell, error, assert_path_exists
from voithos.lib.docker import volume_opt
from voithos.constants import KOLLA_IMAGE_REPOS


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
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    password_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    certs_vol = f"-v {cwd}/certificates:/etc/kolla/certificates"
    cmd = (
        f"docker run --rm {globals_vol} {password_vol} {certs_vol} "
        f"breqwatr/kolla-ansible:{release} "
        "kolla-ansible certificates"
    )
    shell(cmd)


def kolla_ansible_globals(release):
    """ Genereate certificates directory """
    cwd = os.getcwd()
    cmd = (
        f"docker run --rm -v {cwd}:/temp-dir "
        f"breqwatr/kolla-ansible:{release} "
        "cp /var/repos/kolla-ansible/etc/kolla/globals.yml temp-dir/"
    )
    shell(cmd)


def kolla_ansible_get_admin_openrc(release, inventory_path, globals_path, passwords_path):
    """ Save the admin-openrc.sh file to current working directory """
    cwd = os.getcwd()
    inv_vol = volume_opt(inventory_path, "/etc/kolla/inventory")
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    passwords_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    cwd_vol = f"-v {cwd}:/target "
    cmd = (
        "docker run --rm --network host "
        f"{inv_vol} {globals_vol} {passwords_vol} {cwd_vol} "
        f"breqwatr/kolla-ansible:{release} "
        'bash -c "kolla-ansible post-deploy -i /etc/kolla/inventory && '
        'cp /etc/kolla/admin-openrc.sh /target/"'
    )
    shell(cmd)


def cli_exec(release, openrc_path, command, volume=None, debug=False):
    """ Execute <command> using breqwatr/openstack-client:<release>

        Optionally, mount file(s) into the client with the volume arg
    """
    command = "openstack" if command is None else command
    mount = f"-v {volume} " if volume is not None else " "
    openrc_vol = volume_opt(openrc_path, "/admin-openrc.sh")
    image = f"breqwatr/openstack-client:{release}"
    run = f'bash -c "source /admin-openrc.sh && . /var/repos/env/bin/activate && {command}"'
    cmd = f"docker run -it --rm --network host {openrc_vol} {mount} {image} {run}"
    shell(cmd, print_error=False, print_cmd=debug)


def smoke_test(release, openrc, image_path, **kwargs):
    """ Run the smoke test """
    assert_path_exists(image_path)
    image_vol = volume_opt(image_path, "/image.qcow2")
    openrc_vol = volume_opt(openrc, "/admin-openrc.sh")
    env_var_list = []
    for kwarg in kwargs:
        key = kwarg.upper()
        value = kwargs[kwarg]
        var = f"-e {key}={value}"
        env_var_list.append(var)
    env_vars_str = " ".join(env_var_list)
    run = (
        'bash -c "'
        "source /admin-openrc.sh && "
        ". /var/repos/env/bin/activate && "
        'bash /smoke-test.sh"'
    )
    cmd = (
        "docker run --rm "
        f"{openrc_vol} {image_vol} {env_vars_str} "
        f"breqwatr/openstack-client:{release} {run}"
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
        error(f'ERROR: Invalid command "{command}" - Valid commands: {valid_cmds}', exit=True)
    config_vol = " "
    if config_dir is not None:
        config_vol = volume_opt(config_dir, "/etc/kolla/config")
    rm_arg = ""
    inv_vol = volume_opt(inventory_path, "/etc/kolla/inventory")
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    passwd_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    ssh_vol = volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
    cert_vol = volume_opt(certificates_dir, "/etc/kolla/certificates")
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
        f"{inv_vol} {globals_vol} {passwd_vol} {ssh_vol} {cert_vol} {config_vol}"
        f"breqwatr/kolla-ansible:{release} {run_cmd}"
    )
    shell(cmd)


def sync_local_registry(release, keep, registry):
    """ Pull Kolla docker images and push them to local registry """
    if release not in KOLLA_IMAGE_REPOS:
        error(f"ERROR: release {release} is not supported", exit=True)
    total_images = len(KOLLA_IMAGE_REPOS[release])
    index = 1
    for repo in KOLLA_IMAGE_REPOS[release]:
        dh_image = f"breqwatr/{repo}:{release}"
        echo(f"Progress: {index}/{total_images} - Image: {dh_image}")
        local_image = f"{registry}/{dh_image}"
        shell(f"docker pull {dh_image}")
        shell(f"docker tag {dh_image} {local_image}")
        shell(f"docker push {local_image}")
        if not keep:
            echo("Deleting local image")
            shell(f"docker rmi {dh_image}")
            shell(f"docker rmi {local_image}")
