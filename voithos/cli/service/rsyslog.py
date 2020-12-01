""" Manage Rsyslog service"""

import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.rsyslog as rsyslog

@click.option("--release", "-r", required=True, help="Version of breqwatr rsyslog to pull")
@click.command(name="pull")
def pull(release):
    """ pull breqwatr rsyslog image"""
    image = f"breqwatr/rsyslog:{release}"
    ecr.pull(image)


@click.option("--release", "-r", required=True, help="Version of breqwater rsyslog to run")
@click.option("--allowed-senders", "-s", multiple=True, help="Allowed sender ip address. All ip address are allowed by default",)
@click.option("--port", "-p",  default=514, help="rsyslog server listen port")
@click.command(name="start")
def start(
    release,
    allowed_senders,
    port,
):
   """ Launch rsyslog service """

   if not allowed_senders:
       click.echo("Starting rsyslog server for logs from any client")
   else:
       click.echo("Starting rsyslog server for logs from client(s) {}".format(str(allowed_senders)))
   rsyslog.start(release, allowed_senders, port)

def get_rsyslog_group():
    """ Return rsyslog group function  """

    @click.group(name="rsyslog")
    def rsyslog_group():
        """ rsyslog service """

    rsyslog_group.add_command(pull)
    rsyslog_group.add_command(start)
    return rsyslog_group
