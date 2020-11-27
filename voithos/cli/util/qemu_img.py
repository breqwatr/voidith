"""" CLI handlers for qemu-img commands """
from pathlib import Path

import click

import voithos.lib.util.qemu_img as qemu_img
from voithos.lib.system import error

# NOTE: vpc is for HyperV VHD files
FORMATS = ["qcow2", "qed", "raw", "vdi", "vpc", "vmdk"]


@click.option("--input-format", "-f", "input_format", help=f"Allowed={FORMATS}", required=True)
@click.option("--output-format", "-O", "output_format", help=f"Allowed={FORMATS}", required=True)
@click.argument("output_path")
@click.argument("input_path")
@click.command(name="convert")
def convert(input_format, output_format, input_path, output_path):
    """ Run: qemu-img -f <input-format> -O <output-format> <input-path> <output-path> """
    print(f"qemu-img -f {input_format} -O {output_format} {input_path} {output_path}")
    if input_format not in FORMATS or output_format not in FORMATS:
        error("ERROR - Invalid format provided. Valid formats: {FORMATS}", exit=True)
    if not Path(input_path).is_file():
        error(f"ERROR - File not found: {input_path}", exit=True)
    qemu_img.convert(input_format, output_format, input_path, output_path)


def get_qemu_img_group():
    """ Return the qemu_img group """

    @click.group(name="qemu-img")
    def qemu_img_group():
        """ containerized qemu-img commands """

    qemu_img_group.add_command(convert)
    return qemu_img_group
