""" lib for arcus services """

from voithos.lib.docker import env_string, volume_opt
from voithos.lib.system import shell
from voithos.constants import DEV_MODE


def start(
    release,
    openstack_vip,
    sql_pass,
    sql_ip,
    rabbit_ips_list,
    rabbit_pass,
    enable_ceph,
    kolla_ansible_dir,
    cloud_name
):
    """ Start the arcus api """
    rabbit_ips_csv = ",".join(rabbit_ips_list)
    image = f"breqwatr/arcus-mgr:{release}"
    env_vars = {
        "OPENSTACK_VIP": openstack_vip,
        "SQL_USERNAME": "arcus",
        "SQL_PASSWORD": sql_pass,
        "SQL_IP": sql_ip,
        "DR_SQL_USERNAME": "arcus",
        "DR_SQL_PASSWORD": sql_pass,
        "DR_SQL_IP": sql_ip,
        "RABBIT_NODES_CSV": rabbit_ips_csv,
        "RABBIT_USERNAME": "openstack",
        "RABBIT_PASSWORD": rabbit_pass,
        "ENABLE_CEPH": str(enable_ceph).lower(),
        "CLOUD_NAME": cloud_name
    }
    network = "--network=host"
    if DEV_MODE:
        network = ""
    env_str = env_string(env_vars)
    vols = volume_opt(kolla_ansible_dir, "/etc/kolla")
    name = "arcus_mgr"
    shell(f"docker rm -f {name} 2>/dev/null || true")
    cmd = f"docker run -d --restart=always --name {name} {network} {env_str} {vols} {image}"
    shell(cmd)
