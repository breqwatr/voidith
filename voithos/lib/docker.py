""" Docker shell command runner """

from voithos.lib.system import assert_path_exists, get_absolute_path


def volume_opt(src, dest):
    """ Return a volume's argument for docker run """
    assert_path_exists(src)
    absolute_path = get_absolute_path(src)
    return f"-v {absolute_path}:{dest} "


def env_string(env_vars):
    """ return a string of docker -e calls for use in docker run given a dict of env vars """
    env_str = ""
    for env_var in env_vars:
        value = env_vars[env_var]
        env_str += f" -e {env_var}={value} "
    return env_str
