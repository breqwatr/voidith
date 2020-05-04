""" Entrypoint for voidith CLI """

import sys

import click

import voidith.constants as constants

# Requires python 3
if sys.version_info[0] != 3:
    sys.stderr.write('ERROR: Python 3 required \n')
    sys.exit(42)


@click.command(name='version')
def version():
    """ Print the current major version of this CLI """
    click.echo(constants.VOIDITH_VERSION)
    invalid


def get_entrypoint():
    """ Return the entrypoint click group """
    @click.group()
    def entrypoint():
        """ Entrypoint for Click """
    entrypoint.add_command(version)
    return entrypoint


def main():
    """ Entrypoint defined in setup.py for voidith command """
    try:
        entrypoint = get_entrypoint()
        entrypoint()
    except KeyboardInterrupt:
        # Handle ctrl+C without dumping a stack-trace
        sys.exit(100)
