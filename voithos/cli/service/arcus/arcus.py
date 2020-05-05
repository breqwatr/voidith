""" Manage Arcus services """


import click


def get_arcus_group():
    """ return the arcus group function """

    @click.group(name="arcus")
    def arcus_group():
        """ Arcus services """

    # arcus_group.add_command(start)
    return arcus_group
