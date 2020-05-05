""" Ceph library """

import voidith.lib.docker as docker
from voidith.lib.system import shell


def ceph_ansible_exec(release, inventory_path, group_vars_path, ssh_key_path, debug=False):
    """ Execute ceph-ansible """
    debug_str = ' -vvvv ' if debug else ''
    image = f"breqwatr/ceph-ansible:{release}"
    run_cmd = "ansible-playbook -i /ceph-inventory.yml /var/repos/ceph-ansible/site.yml"
    cmd = (
        "docker run --rm --network host --workdir /var/repos/ceph-ansible "
        + docker.volume_opt(inventory_path, "/ceph-inventory.yml")
        + docker.volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
        + docker.volume_opt(group_vars_path, "/var/repos/ceph-ansible/group_vars")
        + f"{debug_str} {image} {run_cmd}"
    )
    shell(cmd)


def zap_disk(disk):
    """ Erase filesystem from a given disk """
    shell(f'wipefs -a {disk}')
    shell(f'dd if=/dev/zero of={disk} bs=4096k count=100')
