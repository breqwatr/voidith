""" Common arcus functions """

import voithos.cli.service.arcus.api as api
import voithos.cli.service.arcus.client as client
import voithos.cli.service.arcus.mgr as mgr


def save(config_file_path):
    """ Save the launch parameters to a config file """
    # ... create an arcus service config file


def load(config_file_path):
    """ Start a container using a configuration file """
    start_functions = {
        "api": api.start,
        "client": client.start,
        "mgr": mgr.start
    }
    # ... load the config file and get the arcus service name
    # start_functions[service]
