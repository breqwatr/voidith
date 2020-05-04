""" Commands for Ceph """

import click

import voidith.lib.ceph as ceph


@click.option(
    "--release", "-r", required=True, help="Ceph-Ansible stable branch [3.2, 4.0, 5.0]",
)
@click.option(
    "--inventory", "-i", required=True, help="Ceph-Ansible inventory file path"
)
@click.option(
    "--group-vars",
    "-g",
    "group_vars",
    required=True,
    help="Ceph-Ansible grou_vars directory path",
)
@click.option(
    "--ssh-key",
    "-s",
    "ssh_key",
    required=True,
    help="Ceph-Ansible grou_vars directory path",
)
@click.command(name="ceph-ansible")
def ceph_ansible(release, inventory, group_vars, ssh_key):
    """ Run Ceph-Ansible's ansible-playbook command """
    ceph.ceph_ansible_exec(release, inventory, group_vars, ssh_key)


def get_ceph_group():
    """ Return the Ceph click group """

    @click.group(name="ceph")
    def ceph_group():
        """ Deploy and manage Ceph """

    ceph_group.add_command(ceph_ansible)
    return ceph_group
