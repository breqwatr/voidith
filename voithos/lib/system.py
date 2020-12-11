""" Shared functions that operate outside of python on the local system """

import pathlib
import socket
import subprocess
import os
import sys
from contextlib import closing


def shell(cmd, print_error=True, print_cmd=True):
    """ Execute the given command """
    try:
        if print_cmd:
            sys.stdout.write(f"{cmd}\n")
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as error:
        # The OpenStack CLI in particular sets print_error=False
        if print_error:
            sys.stderr.write(f"\n\n{error}\n")
        sys.exit(12)


def run(cmd, exit_on_error=False):
    """ Runs a given shell command, returns a list of the stdout lines
        This uses the newer "run" subprocess command, requires later Python versions
    """
    cmd_list = cmd.split(" ")
    completed_process = subprocess.run(cmd_list, stdout=subprocess.PIPE)
    if completed_process.returncode != 0:
        error(f"ERROR - Command failed: {cmd}", exit=True)
    text = completed_process.stdout.decode('utf-8')
    return text.split("\n")


def error(msg, exit=False, code=1):
    """ Write an error to stderr, and exit with error code 'code' if exit=True """
    sys.stderr.write(f"{msg}\n")
    if exit:
        sys.exit(code)


def get_absolute_path(file_path):
    """ Return the absolute path of a potentially relative file path"""
    path = pathlib.Path(file_path)
    path = path.expanduser()
    path = path.absolute()
    return str(path)


def assert_block_device_exists(device):
    """ Gracefully exit if a device does not exist """
    if not pathlib.Path(device).is_block_device():
        error(f"ERROR: Block device not found - {device}", exit=True)

def assert_path_exists(file_path):
    """ Gracefully exit if a file does not exist """
    path = pathlib.Path(get_absolute_path(file_path))
    if not path.exists():
        err = f"ERROR: Expected {file_path} not found\n"
        sys.stderr.write(err)
        sys.exit(11)

class FailedMount(Exception):
    """ A mount operation has failed """


def mount(dev_path, mpoint, fail=True):
    """ Mount dev_path to mpoint.
        If fail is true, throw a nice error. Else raise an exception
    """
    ret = os.system(f"mount {dev_path} {mpoint}")
    if ret != 0:
        fail_msg = f"Failed to mount {dev_path} to {mpoint}"
        if fail:
            error(fail_msg, exit=True)
        else:
            raise FailedMount(fail_msg)


def unmount(mpoint, prompt=False, fail=True):
    """ Unmount a block device if it's mounted. Prompt if prompt=True """
    if not os.path.ismount(mpoint):
        return
    if prompt:
        print(f"WARNING: {mpoint} is currently mounted. Enter 'y' to unmount")
        confirm = input()
        if confirm != "y":
            if fail:
                error("Cannot continue with {mpoint} mounted", exit=True)
            else:
                return
        ret = os.system(f"umount {mpoint}")
        if ret != 0:
            error(f"ERROR: Failed to unmount {mpoint}", exit=True)


def get_file_contents(file_path, required=False):
    """ Return the contents of a file

        When required=True, exit if the file is not found
        When required=False, return '' when the file is not found
    """
    if required:
        assert_path_exists(file_path)
    file_data = ""
    try:
        with open(file_path) as file_:
            file_data = file_.read()
    except FileNotFoundError:
        pass
    return file_data


def set_file_contents(file_path, contents):
    """ Write contents to the file at file_path """
    with open(file_path, "w+") as file_:
        file_.write(contents)


def is_port_open(host, port):
    """ Return true of false if a port is open """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        is_open = sock.connect_ex((host, port)) == 0
    return is_open
