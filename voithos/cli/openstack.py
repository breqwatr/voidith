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
@click.command(name="get-globals-template")
def get_globals_template(release):
    """ Generate a template ./globals.yml """
    openstack.kolla_ansible_globals(release=release)
    click.echo("Generated ./globals.yml")


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


@click.option("--release", "-r", required=True, help="OpenStack release name (OS_RELEASE)")
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
@click.option("--debug/--no-debug", default=False, help="Show the docker command being ran")
@click.command(name="cli")
def cli(release, openrc_path, command, volume, debug):
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
    openstack.cli_exec(
        release=release, openrc_path=openrc_path, command=command, volume=volume, debug=debug
    )


@click.option("--release", "-r", required=True, help="OpenStack release name (OS_RELEASE)")
@click.option("--openrc", required=True, default=None, help="Openrc file path (OS_OPENRC_PATH)")
@click.option("--volume-type", "volume_type", required=True)
@click.option("--volume-backend", "volume_backend", required=True)
@click.option("--sa-user", "sa_user", required=True)
@click.option("--sa-password", "sa_password", required=True)
@click.option("--sa-project", "sa_project", required=True)
@click.option("--net-type", "net_type", required=True)
@click.option("--net-name", "net_name", required=True)
@click.option("--vlan-id", "vlan_id", required=False, default="", help="use with VLAN net-type")
@click.option("--dns", required=True)
@click.option("--cidr", required=True)
@click.option("--gateway", required=True)
@click.option("--pool-start", "pool_start", required=True)
@click.option("--pool-end", "pool_end", required=True)
@click.option("--image-path", "image_path", required=True)
@click.option("--image-name", "image_name", required=True)
@click.option("--flavor-name", "flavor_name", required=True)
@click.option("--ram", required=True, help="MB")
@click.option("--cpu", required=True, help="cores")
@click.option("--disk", required=True, help="GB")
@click.command(name="smoke-test")
def smoke_test(release, openrc, image_path, **kwargs):
    """ Run an initial test setup on a new cloud """
    if kwargs["net_type"] not in ("VLAN", "FLAT"):
        error("--net-type should be VLAN or FLAT")
    if kwargs["net_type"] == "VLAN" and kwargs["vlan_id"] == "":
        error("--vlan-id is required with --net-type VLAN", exit=True)
    openstack.smoke_test(release, openrc, image_path, **kwargs)


@click.option("--release", "-r", required=True, help="OpenStack release name (OS_RELEASE)")
@click.option("--keep/--delete-local", default=True, help="Keep or delete local images")
@click.argument("registry")
@click.command(name='sync-images-to-registry')
def sync_local_registry(release, keep, registry):
    """ Pull OpenStack images, push local registry """
    openstack.sync_local_registry(release, keep, registry)


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
    openstack_group.add_command(smoke_test)
    openstack_group.add_command(get_globals_template)
    openstack_group.add_command(sync_local_registry)
    return openstack_group
