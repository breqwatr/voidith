""" Manage Grafana Dashboards """
import click

#import voithos.lib.service.grafana as grafana




@click.command()
def dashboard_create():
    """ Creates dashboards """
    #grafana.create()

def get_grafana_group():
    """ Return grafana group function  """

    @click.group(name="grafana")
    def grafana_group():
        """ Grafana service """

    grafana_group.add_command(dashboard_create)
    return grafana_group
