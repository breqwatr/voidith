""" lib for arcus services """

import click
import datetime
import voithos.lib.docker as docker
import inspect
import voithos.lib.service.arcus.api as arcus_api
import voithos.lib.service.arcus.client as arcus_client
import voithos.lib.service.arcus.mgr as arcus_mgr

def update(release, arcus_service_type):
    """ Updates arcus container """
    image_name = "breqwatr/arcus-{}".format(arcus_service_type)
    container_name = "arcus_"+arcus_service_type
    docker.image_exists(image_name, release)
    env_variables = docker.get_container_env_variables(container_name)
    env_variables_dict = _get_env_variables_dict(env_variables)
    args = inspect.getargspec(eval("arcus_"+arcus_service_type).start)[0]
    args_dict = _verify_and_return_start_methods_args(release, arcus_service_type, env_variables_dict, args)
    old_container_image_tag = docker.get_container_image_tag(container_name)
    docker.container_action(container_name, "stop")
    arcus_rename = container_name+"_release_"+old_container_image_tag+"_datetime_"+datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    docker.container_action(container_name, "rename", name=arcus_rename)
    docker.container_action(arcus_rename, "update_container", restart_policy={"Name": "no"})
    eval("arcus_"+arcus_service_type).start(**args_dict)

def _get_env_variables_dict(env_variables):
    env_variables_dict = {}
    for env_variable in env_variables:
        key = env_variable.split("=")[0]
        value = env_variable.split("=")[1]
        env_variables_dict[key] = value
    return env_variables_dict

def _verify_and_return_start_methods_args(release, arcus_service_type, env_variables_dict, args):
    args_dict = {}
    if arcus_service_type == "api":
        args_dict = { "release": release,
                      "fqdn": env_variables_dict["OPENSTACK_VIP"],
                      "rabbit_pass": env_variables_dict["RABBITMQ_PASSWORD"],
                      "rabbit_ips_list": env_variables_dict["RABBIT_IPS_CSV"].split(","),
                      "sql_ip": env_variables_dict["SQL_IP"],
                      "sql_password": env_variables_dict["SQL_PASSWORD"],
                      "https": env_variables_dict["HTTPS_OPENSTACK_APIS"],
                      "port": env_variables_dict["ARCUS_API_PORT"],
                      "secret": env_variables_dict["ARCUS_INTEGRATION_SECRET"] }
    if arcus_service_type == "client":
        cert_paths = _get_cert_paths(arcus_service_type)
        cert_path = None if "/etc/nginx/haproxy.crt" not in cert_paths else cert_paths["/etc/nginx/haproxy.crt"]
        cert_key_path = None if "/etc/nginx/haproxy.key" not in cert_paths else cert_paths["/etc/nginx/haproxy.key"]
        args_dict = {"release": release,
                      "api_ip": env_variables_dict["ARCUS_API_IP"],
                      "openstack_ip": env_variables_dict["OPENSTACK_VIP"],
                      "glance_https": env_variables_dict["GLANCE_HTTPS"],
                      "arcus_https": env_variables_dict["ARCUS_USE_HTTPS"],
                      "cert_path": cert_path,
                      "cert_key_path": cert_key_path,
                      "http_port": env_variables_dict["ARCUS_CLIENT_HTTP_PORT"],
                      "https_port": env_variables_dict["ARCUS_CLIENT_HTTPS_PORT"]  }

    if arcus_service_type == "mgr":
        kolla_dir_path = _get_kolla_dir(arcus_service_type)
        args_dict = { "release": release,
                      "openstack_vip": env_variables_dict["OPENSTACK_VIP"],
                      "sql_pass": env_variables_dict["SQL_PASSWORD"],
                      "sql_ip": env_variables_dict["SQL_IP"],
                      "rabbit_ips_list": env_variables_dict["RABBIT_NODES_CSV"].split(","),
                      "rabbit_pass": env_variables_dict["RABBIT_PASSWORD"],
                      "enable_ceph": env_variables_dict["ENABLE_CEPH"],
                      "kolla_ansible_dir": kolla_dir_path,
                      "cloud_name": env_variables_dict["CLOUD_NAME"] }
    for key in args_dict:
        args.remove(key)
    if len(args) >  0:
        msg = "ERROR: New args {} aren't supported in running arcus_{} container. Please create new arcus_{} container.".format(args, arcus_service_type)
        error(msg, exit=True)
    return args_dict


def _get_cert_paths(arcus_service_type):
    bind_list = docker.get_container_inspect_info("arcus_"+arcus_service_type)["HostConfig"]["Binds"]
    cert_paths = {}
    for bind in bind_list:
        if "/etc/nginx/haproxy" in bind:
            cert_paths[bind.split(":")[1]] = bind.split(":")[0]
    return cert_paths

def _get_kolla_dir(arcus_service_type):
    bind_list = docker.get_container_inspect_info("arcus_"+arcus_service_type)["HostConfig"]["Binds"]
    cert_paths = {}
    for bind in bind_list:
        if ":/etc/kolla" in bind:
            return bind.split(":")[0]
