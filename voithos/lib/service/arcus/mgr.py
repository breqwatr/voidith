""" lib for arcus services """

from voithos.lib.docker import env_string
from voithos.lib.system import shell


def start(release, openstack_vip, sql_pass, sql_ip, rabbit_ips_list, rabbit_pass, enable_ceph):
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
    }
    env_str = env_string(env_vars)
    cmd = f"docker run -d --restart=always --name arcus_mgr --network=host {env_str} {image}"
    shell(cmd)
