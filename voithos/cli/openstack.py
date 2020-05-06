""" OpenStack commands """

import os

import click

import voithos.lib.openstack as openstack
from voithos.lib.system import error


@click.option("--release", "-r", help="OpenStack release name", required=True)
@click.command(name="get-passwords")
def get_passwords(release):
    """ Generate Kolla-Ansible's ./passwords.yml file """
    openstack.kolla_ansible_genpwd(release)
    click.echo("")
    click.echo("Creatied password file: ./passwords.yml")


@click.option("--release", "-r", help="OpenStack release name", required=True)
@click.command(name="get-inventory-template")
def get_inventory_template(release):
    """ Generate inventory template, save to ./inventory """
    openstack.kolla_ansible_inventory(release)
    click.echo("Created inventory template: ./inventory")


@click.option("--release", "-r", help="OpenStack release name", required=True)
@click.option(
    "--passwords", "-p", "passwords_file", required=True, help="Path of passwords.yml file"
)
@click.option("--globals", "-g", "globals_file", required=True, help="Path of globals.yml file")
@click.command(name="get-certificates")
def get_certificates(release, passwords_file, globals_file):
    """ Generate certificates, save to ./certificates/ """
    openstack.kolla_ansible_generate_certificates(
        release=release, passwords_path=passwords_file, globals_path=globals_file
    )
    click.echo("Generated ./certificates/")


@click.option("--release", "-r", help="OpenStack release name", required=True)
@click.option(
    "--ssh-key", "-s", "ssh_private_key_file", required=True, help="Path of SSH private key file",
)
@click.option(
    "--inventory", "-i", "inventory_file", required=True, help="Path of Ansible inventory file"
)
@click.option(
    "--passwords", "-p", "passwords_file", required=True, help="Path of passwords.yml file"
)
@click.option("--globals", "-g", "globals_file", required=True, help="Path of globals.yml file")
@click.option(
    "--certificates",
    "-d",
    "certificates_dir",
    required=True,
    help="Path of certificates/ directory",
)
@click.option(
    "--config",
    "-c",
    "config_dir",
    required=False,
    default=None,
    help="Path of config/ directory  [optional]",
)
@click.argument("command")
@click.command(name="kolla-ansible")
def kolla_ansible(
    release,
    ssh_private_key_file,
    inventory_file,
    globals_file,
    passwords_file,
    certificates_dir,
    config_dir,
    command,
):
    """ Execute Kolla-Ansible command  """
    openstack.kolla_ansible_exec(
        release=release,
        ssh_key_path=ssh_private_key_file,
        inventory_path=inventory_file,
        globals_path=globals_file,
        passwords_path=passwords_file,
        certificates_dir=certificates_dir,
        config_dir=config_dir,
        command=command,
    )


@click.option("--release", "-r", help="OpenStack release name", required=True)
@click.option(
    "--inventory", "-i", "inventory_file", required=True, help="Path of Ansible inventory file"
)
@click.option(
    "--passwords", "-p", "passwords_file", required=True, help="Path of passwords.yml file"
)
@click.option("--globals", "-g", "globals_file", required=True, help="Path of globals.yml file")
@click.command(name="get-admin-openrc")
def get_admin_openrc(release, inventory_file, globals_file, passwords_file):
    """ Generate & save ./admin-openrc.sh"""
    click.echo("Generating ./admin-openrc.sh")
    openstack.kolla_ansible_get_admin_openrc(
        release=release,
        inventory_path=inventory_file,
        globals_path=globals_file,
        passwords_path=passwords_file,
    )
    click.echo("Created ./admin-openrc.sh")


@click.option(
    "--release", "-r", required=False, default=None, help="OpenStack release name (OS_RELEASE)"
)
@click.option(
    "--openrc",
    "-o",
    "openrc_path",
    required=False,
    default=None,
    help="Openrc file path (OS_OPENRC_PATH)",
)
@click.option(
    "--command",
    "-c",
    required=False,
    default=None,
    help="Execute this command (non-interactive mode) [optional]",
)
@click.option(
    "--volume",
    "-v",
    required=False,
    default=None,
    help="Mount a file to the client container [optional]",
)
@click.command(name="cli")
def cli(release, openrc_path, command, volume):
    """ Launch then OpenStack client CLI """
    if release is None:
        if "OS_RELEASE" not in os.environ:
            error("ERROR: Release not found", exit=False)
            error("       use --release or set $OS_RELEASE", exit=True)
        release = os.environ["OS_RELEASE"]
    if openrc_path is None:
        if "OS_OPENRC_PATH" not in os.environ:
            error("ERROR: OpenRC file not found", exit=False)
            error("       Use --openrc-path / -o or set $OS_OPENRC_PATH", exit=True)
        openrc_path = os.environ["OS_OPENRC_PATH"]
    openstack.cli_exec(release=release, openrc_path=openrc_path, command=command, volume=volume)


def get_openstack_group():
    """ Return the OpenStack click group """

    @click.group(name="openstack")
    def openstack_group():
        """ Deploy and manage OpenStack """

    openstack_group.add_command(get_passwords)
    openstack_group.add_command(get_inventory_template)
    openstack_group.add_command(get_certificates)
    openstack_group.add_command(get_admin_openrc)
    openstack_group.add_command(kolla_ansible)
    openstack_group.add_command(cli)
    return openstack_group
