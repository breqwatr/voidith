""" qemu-img library: Manages conversions of vDisk types and mapping them to raw devices """
from pathlib import Path

from voithos.lib.system import shell, assert_path_exists


def convert(input_format, output_format, input_path, output_path):
    """ Execute qemu-img inside a container that mounts input_path and output_path to itself """
    # mount the input file to /work/<filename> inside the container
    path_in = Path(input_path)
    input_abspath = path_in.absolute().__str__()
    assert_path_exists(input_abspath)
    internal_input_path = f"/input/{path_in.name}"
    in_mount = f"-v {input_abspath}:{internal_input_path}"
    # The mount for the output dir varies depending on if its a file or block device
    path_out = Path(output_path)
    if path_out.is_block_device():
        # directly map the block device to the container
        assert_path_exists(path_out)
        out_mount = "-v {path_out}"
        internal_output_path = path_out
    else:
        # output is a file (or about to be), so mount the folder it exists in
        output_abspath = path_out.absolute().__str__()
        output_dir = Path(output_abspath).parent.__str__()
        assert_path_exists(output_dir)
        internal_output_dir = "/output"
        internal_output_path = f"{internal_output_dir}/{path_out.name}"
        out_mount = f"-v {output_dir}:/output"
    name = "qemu-img"
    image = "breqwatr/qemu-img:latest"
    run = (
        f"qemu-img convert -f {input_format} -O {output_format} "
        f"{internal_input_path} {internal_output_path}"
    )
    cmd = f"docker run -it --name {name} --rm {in_mount} {out_mount} {image} {run}"
    shell(cmd)
