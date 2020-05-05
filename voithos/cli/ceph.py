""" Commands for Ceph """

import click

import voithos.lib.ceph as ceph
import voithos.lib.system as system


@click.option(
    "--release", "-r", required=True, help="Ceph-Ansible stable branch [3.2, 4.0, 5.0]",
)
@click.option("--inventory", "-i", required=True, help="Ceph-Ansible inventory file path")
@click.option(
    "--group-vars", "-g", "group_vars", required=True, help="Ceph-Ansible grou_vars directory path",
)
@click.option(
    "--ssh-key", "-s", "ssh_key", required=True, help="Ceph-Ansible grou_vars directory path",
)
@click.option(
    "--verbose/--no-verbose", default=False, help="Run ansible-playbook with -vvvv",
)
@click.option(
    "--debug/--no-debug", default=False, help="Start the container as an idle daemon instead",
)
@click.command(name="ceph-ansible")
def ceph_ansible(release, inventory, group_vars, ssh_key, verbose, debug):
    """ Run Ceph-Ansible's ansible-playbook command """
    ceph.ceph_ansible_exec(release, inventory, group_vars, ssh_key, verbose=verbose, debug=debug)


@click.argument("disk")
@click.option(
    "--force/--ask",
    required=False,
    default=False,
    help="Skip the prompt asking you to type the drive name",
)
@click.command(name="zap-disk")
def zap_disk(disk, force):
    """ Erase filesystem from given disk """
    if not force:
        click.echo("")
        click.echo(f"WARNING: This will destroy any filesystem on the drive: {disk}")
        click.echo("Type the drive name again to continue:")
        user_in = input()
        if user_in != disk:
            system.error(f"ERROR: Confirm does not match {disk}", exit=True)
    system.assert_path_exists(disk)
    ceph.zap_disk(disk)


def get_ceph_group():
    """ Return the Ceph click group """

    @click.group(name="ceph")
    def ceph_group():
        """ Deploy and manage Ceph """

    ceph_group.add_command(ceph_ansible)
    ceph_group.add_command(zap_disk)
    return ceph_group
