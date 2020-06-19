""" Ceph library """

import voithos.lib.docker as docker
from voithos.lib.system import shell
import yaml


def ceph_ansible_exec(
    release, inventory_path, group_vars_path, ssh_key_path, verbose=False, debug=False
):
    """ Execute ceph-ansible """
    verbose_str = " -vvvv " if verbose else ""
    image = f"breqwatr/ceph-ansible:{release}"
    rm_or_daemon = "--rm"
    if debug:
        rm_or_daemon = " -d --name ceph_ansible "
        run_cmd = "tail -f /dev/null"
        print("Starting container named ceph_ansible for debug")
    else:
        run_cmd = "ansible-playbook -i /ceph-inventory.yml /var/repos/ceph-ansible/site.yml"
    cmd = (
        f"docker run {rm_or_daemon} --network host --workdir /var/repos/ceph-ansible "
        + docker.volume_opt(inventory_path, "/ceph-inventory.yml")
        + docker.volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
        + docker.volume_opt(group_vars_path, "/var/repos/ceph-ansible/group_vars")
        + f"{verbose_str} {image} {run_cmd}"
    )
    shell(cmd)


def zap_disk(disk):
    """ Erase filesystem from a given disk """
    shell(f"wipefs -a {disk}")
    shell(f"dd if=/dev/zero of={disk} bs=4096k count=100")


def ceph_destroy(inventory):
    """ Uninstall ceph and remove ceph related data"""
    ceph_hosts = _get_parsed_ceph_hosts(inventory)
    for key, ceph_host in ceph_hosts.items():
        host_ip = ceph_host["ansible_host"]
        shell(f"ceph-deploy purge {host_ip}")
        shell(f"ceph-deploy purgedata {host_ip}")
        shell(f"ssh {host_ip} 'ls /dev/mapper/ceph-* | xargs -I% -- dmsetup remove %'")
        for osd in ceph_host["devices"]:
            cmd = (
                f"ssh {host_ip} wipefs -a {osd} && "
                + f"dd if=/dev/zero of={osd} bs=4096k count=100"
            )
            shell(cmd)
        if "dedicated_devices" in ceph_host:
            for dedicated_device in ceph_host["dedicated_devices"]:
                cmd = (
                    f"ssh {host_ip} wipefs -a {dedicated_device} && "
                    + f"dd if=/dev/zero of={dedicated_device} bs=4096k count=100"
                )
                shell(cmd)


def _get_parsed_ceph_hosts(inventory):
    """ Provides osd hosts data """
    try:
        with open(inventory) as inventory_file:
            inventory_file_data = inventory_file.read()
    except FileNotFoundError:
        print("Please check path and name of inventory file")
    parsed_inventory = yaml.load(inventory_file_data, Loader=yaml.FullLoader)
    return parsed_inventory["all"]["children"]["osds"]["hosts"]
