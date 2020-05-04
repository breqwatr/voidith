""" Ceph library """

import voidith.lib.docker as docker
from voidith.lib.system import shell


def ceph_ansible_exec(release, inventory_path, group_vars_path, ssh_key_path):
    """ Execute ceph-ansible """
    image = f"breqwatr/ceph-ansible:{release}"
    shell(f"docker pull {image}")
    run_cmd = "ansible-playbook -i /ceph-inventory.yml /var/repos/ceph-ansible/site.yml"
    cmd = (
        "docker run --rm --network host --workdir /var/repos/ceph-ansible "
        + docker.volume_opt(inventory_path, "/ceph-inventory.yml")
        + docker.volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
        + docker.volume_opt(group_vars_path, "/var/repos/ceph-ansible/group_vars")
        + f"{image} {run_cmd}"
    )
    shell(cmd)
