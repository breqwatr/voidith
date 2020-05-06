""" Configure Voithos """

import click

import voithos.lib.config as config


@click.option("--set", "new_key", default=None, help="Apply a new license key")
@click.command()
def license(new_key):
    """ Show or apply the license key """
    if new_key is not None:
        # click.echo('Saving key to configuration')
        config.set_license(new_key)
    license_key = config.get_license()
    if license_key:
        click.echo(license_key)
    else:
        click.echo("No license found: Use --set to configure the key")


def get_config_group():
    """ Return the config click group """

    @click.group(name="config")
    def config_group():
        """ Configure Voithos """

    config_group.add_command(license)
    return config_group
