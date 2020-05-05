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


def get_openstack_group():
    """ Return the OpenStack click group """
    @click.group(name='openstack')
    def openstack_group():
        """ Deploy and manage OpenStack """
    openstack_group.add_command(get_passwords)
    openstack_group.add_command(get_inventory_template)
    # openstack_group.add_command(get_certificates)
    # openstack_group.add_command(get_admin_openrc)
    # openstack_group.add_command(kolla_ansible)
    # openstack_group.add_command(cli)
    return openstack_group
