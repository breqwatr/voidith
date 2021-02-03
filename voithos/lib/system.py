""" Shared functions that operate outside of python on the local system """

import pathlib
import socket
import subprocess
import os
import sys
from contextlib import closing
from time import sleep


def is_debug_on():
    """ Return if debug mode is on or not """
    arg = "VOITHOS_DEBUG"
    return arg in os.environ and os.environ[arg] == "true"


def debug(txt):
    """ Print text if debug mode is on """
    if is_debug_on():
        print(f"DEBUG:  {txt}")


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


def run(cmd, exit_on_error=False, print_cmd=False, silent=False):
    """Runs a given shell command, returns a list of the stdout lines
    This uses the newer "run" subprocess command, requires later Python versions
    """
    if not silent:
        debug(f"run:  {cmd}")
    cmd_list = cmd.split(" ")
    if is_debug_on():
        completed_process = subprocess.run(cmd_list, stdout=subprocess.PIPE)
    else:
        completed_process = subprocess.run(
            cmd_list, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
    if completed_process.returncode != 0:
        error(f"ERROR - Command failed: {cmd}", exit=True)
    text = completed_process.stdout.decode("utf-8")
    return text.split("\n")


def grep(cmd, expression):
    """ Run a command, return matching lines """
    lines = run(cmd)
    return [line for line in lines if expression in line]


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


def get_mount(mpoint):
    """ Return the device path of a mountpoint """
    mount_lines = run("mount", silent=True)
    mpoint_lines = [mpoint_line for mpoint_line in mount_lines if mpoint in mpoint_line]
    if not mpoint_lines:
        return None
    for line in mpoint_lines:
        split = line.split(" ")
        if len(split) < 3:
            return None
        if split[2] == mpoint:
            return {"device": split[0], "mpoint": split[2]}


def is_mounted(mpoint):
    """ os.path.ismount is not reliable - return bool if mpoint is mounted """
    mnt = get_mount(mpoint)
    return (mnt is not None)


def _strip_double_slash(path):
    """ Remove redundant double-slashes, they break the mounts """
    while "//" in path:
        path = path.replace("//","/")
    return path


def mount(dev_path, mpoint, fail=True, bind=False, mkdir=True):
    """Mount dev_path to mpoint.
    If fail is true, throw a nice error. Else raise an exception
    """
    dev_path = _strip_double_slash(dev_path)
    mpoint = _strip_double_slash(mpoint)
    if not dev_path or not mpoint:
        error("ERROR: Invalid mount arguments", exit=True)
    if mkdir:
      pathlib.Path(mpoint).mkdir(parents=True, exist_ok=True)
    if is_mounted(mpoint):
        debug(f"!!  not mounting {dev_path} to {mpoint} - {mpoint} is already mounted")
        return
    bind = "--bind" if bind else ""
    cmd = f"mount {bind} {dev_path} {mpoint}"
    debug(f"run:  {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        fail_msg = f"ERROR:  Failed to mount {dev_path} to {mpoint}"
        if fail:
            error(fail_msg, exit=True)
        else:
            raise FailedMount(fail_msg)


def unmount(mpoint, prompt=False, fail=True):
    """ Unmount a block device if it's mounted. Prompt if prompt=True """
    mpoint = _strip_double_slash(mpoint)
    # If its already not mounted, nothing to do
    if not is_mounted(mpoint):
        return
    # Sometimes we should check with the user first before doing anything
    if prompt:
        print(f"WARNING: {mpoint} is currently mounted. Enter 'y' to unmount")
        confirm = input()
        if confirm != "y":
            if fail:
                error(f"Cannot continue with {mpoint} mounted", exit=True)
            else:
                return
    # It can take a few retries before it works
    retries = 5
    for attempt in range(1, retries + 1):
        if attempt > 1:
            debug(f"Unmounting {mpoint} - try {attempt}/{retries}")
        run(f"umount {mpoint}")
        if not is_mounted(mpoint):
            break
        sleep(attempt)
    if is_mounted(mpoint):
        error(f"ERROR: Failed to unmount {mpoint}", exit=fail)


def get_file_contents(file_path, required=False):
    """Return the contents of a file

    When required=True, exit if the file is not found
    When required=False, return '' when the file is not found
    When split=True, return a list split by new-line chars
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


def set_file_contents(file_path, contents, append=False):
    """ Write contents to the file at file_path """
    operation = "a+" if append else "w+"
    with open(file_path, operation) as file_:
        file_.write(contents)


def is_port_open(host, port):
    """ Return true of false if a port is open """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        is_open = sock.connect_ex((host, port)) == 0
    return is_open
