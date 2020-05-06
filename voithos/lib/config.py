""" Config lib """

import json

import voithos.lib.system as system


DEFAULT_CONFIG = {"license": ""}


def get_config_path():
    """ Return the path to the configuration file """
    return system.get_absolute_path("~/.voithos")


def get_config():
    """ Return the configuration as found either in ~/.voithos or the default """
    conf_file = get_config_path()
    conf_json = system.get_file_contents(conf_file, required=False)
    conf_data = DEFAULT_CONFIG
    try:
        conf_data = json.loads(conf_json)
    except ValueError:
        pass
    return conf_data


def set_config(key, value):
    """ Set a configuration value """
    config = get_config()
    config[key] = value
    config_json = json.dumps(config)
    config_path = get_config_path()
    system.set_file_contents(config_path, config_json)


def get_license():
    """ Return the license key - Return an empty string if not found """
    config = get_config()
    return config["license"]


def require_license():
    """ Raise an error an exit if there is no license """
    license = get_license()
    if license == "":
        system.error("ERROR: This action requires a license", exit=True)


def set_license(license):
    """ Save the given license key to the config """
    set_config("license", license)
