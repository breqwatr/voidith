""" Docker shell command runner """

from voidith.lib.system import assert_path_exists, get_absolute_path


def volume_opt(src, dest):
    """ Return a volume's argument for docker run """
    assert_path_exists(src)
    absolute_path = get_absolute_path(src)
    return f"-v {absolute_path}:{dest} "
