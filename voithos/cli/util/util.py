""" Voithos Utilities """

import click
from voithos.cli.util.qemu_img import get_qemu_img_group


def get_util_group():
    """ Return the util group """

    @click.group(name="util")
    def util_group():
        """ Voithos utilities """

    util_group.add_command(get_qemu_img_group())
    return util_group
