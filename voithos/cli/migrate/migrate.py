""" Command-group: voithos util migrate """
import click
import voithos.cli.migrate.rhel as rhel
import voithos.cli.migrate.ubuntu as ubuntu


def get_migrate_group():
    """ Return the migrate click group """

    @click.group()
    def migrate():
        """ Migrate VMs to OpenStack """

    migrate.add_command(rhel.get_rhel_group())
    migrate.add_command(ubuntu.get_ubuntu_group())
    return migrate
