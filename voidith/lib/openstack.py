""" OpenStack lib """

import os

from voidith.lib.system import shell
from voidith.lib.docker import volume_opt


def kolla_ansible_genpwd(release):
    """ Genereate passwords.yml and print to stdout """
    cwd = os.getcwd()
    path = '/var/repos/kolla-ansible/etc/kolla/passwords.yml'
    cmd = (f'docker run --rm '
           f'-v {cwd}:/etc/kolla '
           f'breqwatr/kolla-ansible:{release} '
           f'bash -c "kolla-genpwd --passwords {path} '
           f'&& cp {path} /etc/kolla/passwords.yml"')
    shell(cmd)


def kolla_ansible_inventory(release):
    """ Print the inventory template for the given release """
    cwd = os.getcwd()
    inventory_file = '/var/repos/kolla-ansible/ansible/inventory/multinode'
    cmd = (f'docker run --rm '
           f'-v {cwd}:/etc/kolla '
           f'breqwatr/kolla-ansible:{release} '
           f'cp {inventory_file} /etc/kolla/inventory')
    shell(cmd)


def kolla_ansible_generate_certificates(release, passwords_path, globals_path):
    """ Genereate certificates directory """
    cwd = os.getcwd()
    cmd = ('docker run --rm '
           + volume_opt(globals_path, '/etc/kolla/globals.yml')
           + volume_opt(passwords_path, '/etc/kolla/passwords.yml') +
           f'-v {cwd}/certificates:/etc/kolla/certificates '
           f'breqwatr/kolla-ansible:{release} '
           f'kolla-ansible certificates')
    shell(cmd)
