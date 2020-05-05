""" Operate the registry service """

from voidith.lib.system import shell


def start(ip, port):
    """ Start the local registry """
    shell(f"docker run -d --name registry -p {ip}:{port}:5000 registry:2")
