""" Command-group: voithos util migrate """
import click
import voithos.cli.migrate.rhel as rhel


def get_migrate_group():
    """ Return the migrate click group """

    @click.group()
    def migrate():
        """ Migrate VMs to OpenStack """

    migrate.add_command(rhel.get_rhel_group())
    return migrate
