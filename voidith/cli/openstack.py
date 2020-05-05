""" OpenStack commands """

import click

import voidith.lib.openstack as openstack


@click.option('--release', '-r', help='OpenStack release name', required=True)
@click.command(name='get-passwords')
def get_passwords(release):
    """ Generate Kolla-Ansible's ./passwords.yml file """
    openstack.kolla_ansible_genpwd(release)
    click.echo('')
    click.echo('Creatied password file: ./passwords.yml')


@click.option('--release', '-r', help='OpenStack release name', required=True)
@click.command(name='get-inventory-template')
def get_inventory_template(release):
    """ Generate inventory template, save to ./inventory """
    openstack.kolla_ansible_inventory(release)
    click.echo('Created inventory template: ./inventory')


@click.option('--release', '-r', help='OpenStack release name', required=True)
@click.option('--passwords-file', '-p', 'passwords_file', required=True,
              help='Path of passwords.yml file')
@click.option('--globals-file', '-g', 'globals_file', required=True,
              help='Path of globals.yml file')
@click.command(name='get-certificates')
def get_certificates(release, passwords_file, globals_file):
    """ Generate certificates, save to ./certificates/ """
    openstack.kolla_ansible_generate_certificates(
        release=release,
        passwords_path=passwords_file,
        globals_path=globals_file)
    click.echo(f'Generated ./certificates/')


def get_openstack_group():
    """ Return the OpenStack click group """
    @click.group(name='openstack')
    def openstack_group():
        """ Deploy and manage OpenStack """
    openstack_group.add_command(get_passwords)
    openstack_group.add_command(get_inventory_template)
    openstack_group.add_command(get_certificates)
    # openstack_group.add_command(get_admin_openrc)
    # openstack_group.add_command(kolla_ansible)
    # openstack_group.add_command(cli)
    return openstack_group
