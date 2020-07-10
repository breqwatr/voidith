""" Manage Grafana Dashboards """

import click
import voithos.lib.service.grafana as grafana


@click.option("--user", required=True, help="Target grafana setup username")
@click.option("--password", required=True, help="Target grafana setup password")
@click.option("--https/--http", default=True, required=True, help="Does Grafana use HTTPS or HTTP")
@click.option("--ip", required=True, help="Grafana server IP")
@click.option("--port", required=True, help="Grafana server port")
@click.command()
def dashboard_create(user, password, https, ip, port):
    """ Creates dashboards """
    grafana.create(user, password, https, ip, port)


def get_grafana_group():
    """ Return grafana group function  """

    @click.group(name="grafana")
    def grafana_group():
        """ Grafana service """

    grafana_group.add_command(dashboard_create)
    return grafana_group
