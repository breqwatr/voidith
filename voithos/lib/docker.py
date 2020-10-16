""" Docker shell command runner """

from voithos.lib.system import assert_path_exists, get_absolute_path, error
import docker
import click


def volume_opt(src, dest, require=True):
    """Return a volume's argument for docker run

    Don't use volume_opt with hard-coded linux paths, it will make Windows try and mkdir in
    C:\\WINDOWS\\system32 and fail. volume_opt can handle C:\\... syntax correctly. Instead,
    just use '-v /linux/path:/mount/point and the docker vm on Windows will handle it.
    """
    if require:
        assert_path_exists(src)
    absolute_path = get_absolute_path(src)
    return f'-v "{absolute_path}:{dest}" '


def env_string(env_vars):
    """ return a string of docker -e calls for use in docker run given a dict of env vars """
    env_str = ""
    for env_var in env_vars:
        value = env_vars[env_var]
        env_str += f" -e {env_var}='{value}' "
    return env_str


def image_exists(image_name, image_tag):
    """ Checks if image with image_name and tag exists else throw error "Image not found" """
    docker_client = docker.from_env()
    arcus_image = image_name + ":" + image_tag
    image_list = docker_client.images.list()
    for image in image_list:
        if arcus_image in image.tags:
            click.echo("Image {} exists.".format(arcus_image))
            return
    error(
        "ERROR: Image: {} not found. Please pull {} before running update command.".format(
            arcus_image, arcus_image
        ),
        exit=True,
    )


def get_container_inspect_info(container_name):
    """  Returns container inspect info"""
    docker_client = docker.from_env()
    _container_exists(container_name)
    container_info = docker_client.api.inspect_container(container_name)
    return container_info


def get_container_env_variables(container_name):
    """ Checks if container exists and returns container env variables """
    container_info = get_container_inspect_info(container_name)
    return container_info["Config"]["Env"]


def get_container_image_tag(container_name):
    """ Returns image tag of container """
    docker_client = docker.from_env()
    _container_exists(container_name)
    image_tag = docker_client.api.inspect_container(container_name)["Config"]["Image"].split(":")[1]
    return image_tag


def _container_exists(container_name):
    """ Checks and throws error if container doesn't exist """
    docker_client = docker.from_env()
    containers_list = docker_client.containers.list()
    exist = any(container.name == container_name for container in containers_list)
    if not exist:
        error("ERROR: Container: {} not found".format(container_name), exit=True)


def container_action(container_name, operation, **kwargs):
    """ Runs docker operations """
    docker_client = docker.from_env()
    action_method = getattr(docker_client.api, operation)
    action_method(container_name, **kwargs)
