""" OpenStack commands """

import click

import voithos.lib.openstack as openstack


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
    "--passwords-file", "-p", "passwords_file", required=True, help="Path of passwords.yml file"
)
@click.option(
    "--globals-file", "-g", "globals_file", required=True, help="Path of globals.yml file"
)
@click.command(name="get-certificates")
def get_certificates(release, passwords_file, globals_file):
    """ Generate certificates, save to ./certificates/ """
    openstack.kolla_ansible_generate_certificates(
        release=release, passwords_path=passwords_file, globals_path=globals_file
    )
    click.echo("Generated ./certificates/")


@click.option('--release', '-r', help='OpenStack release name', required=True)
@click.option('--ssh-private-key-file', '-s', 'ssh_private_key_file',
              required=True, help='Path of SSH private key file')
@click.option('--inventory-file', '-i', 'inventory_file', required=True,
              help='Path of Ansible inventory file')
@click.option('--passwords-file', '-p', 'passwords_file', required=True,
              help='Path of passwords.yml file')
@click.option('--globals-file', '-g', 'globals_file', required=True,
              help='Path of globals.yml file')
@click.option('--certificates-dir', '-d', 'certificates_dir', required=True,
              help='Path of certificates/ directory')
@click.option('--config-dir', '-c', 'config_dir', required=False, default=None,
              help='Path of config/ directory  [optional]')
@click.argument('command')
@click.command(name='kolla-ansible')
def kolla_ansible(release, ssh_private_key_file, inventory_file, globals_file,
                  passwords_file, certificates_dir, config_dir, command):
    """ Execute Kolla-Ansible command  """
    openstack.kolla_ansible_exec(
        release=release,
        ssh_key_path=ssh_private_key_file,
        inventory_path=inventory_file,
        globals_path=globals_file,
        passwords_path=passwords_file,
        certificates_dir=certificates_dir,
        config_dir=config_dir,
        command=command)


def get_openstack_group():
    """ Return the OpenStack click group """

    @click.group(name="openstack")
    def openstack_group():
        """ Deploy and manage OpenStack """

    openstack_group.add_command(get_passwords)
    openstack_group.add_command(get_inventory_template)
    openstack_group.add_command(get_certificates)
    # openstack_group.add_command(get_admin_openrc)
    openstack_group.add_command(kolla_ansible)
    # openstack_group.add_command(cli)
    return openstack_group
