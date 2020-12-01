""" Library for rsyslog service """
import click
from voithos.lib.system import shell

def start(
    release,
    allowed_senders,
    rsyslog_port,
):
    """ Start rsyslog service """
    sender_ips_cs = ", ".join(allowed_senders)
    image = f"breqwatr/rsyslog:{release}"
    daemon = "-d --restart=always"
    mount = "-v /var/log/networks:/var/log/networks"
    ports = f"-p {rsyslog_port}:514 -p {rsyslog_port}:514/udp".format(rsyslog_port)
    env_variable = f'-e ALLOWEDSENDERS="{sender_ips_cs}"'.format(sender_ips_cs)
    cmd = (f" docker run {daemon} --name rsyslog {ports} {mount} {env_variable} {image}")
    shell(cmd)
