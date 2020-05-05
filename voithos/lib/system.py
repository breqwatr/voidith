""" Shared functions that operate outside of python on the local system """

import pathlib
import subprocess
import sys


def shell(cmd, print_error=True):
    """ Execute the given command """
    try:
        sys.stdout.write(f"{cmd}\n")
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as error:
        # The OpenStack CLI in particular sets print_error=False
        if print_error:
            sys.stderr.write(f"\n\n{error}\n")
        sys.exit(12)


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


def assert_path_exists(file_path):
    """ Gracefully exist if a file does not exist """
    path = pathlib.Path(get_absolute_path(file_path))
    if not path.exists():
        err = f"ERROR: Expected {file_path} not found\n"
        sys.stderr.write(err)
        sys.exit(11)
