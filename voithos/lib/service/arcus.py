""" lib for arcus services """

from voithos.lib.system import shell


def start_api(release, fqdn, rabbit_pass, rabbit_ips_list, sql_ip, sql_password, ceph_enabled,
              https):
    """ Start the arcus api """
    image = f'breqwatr/arcus-api:{release}'
    rabbit_ips_csv = ','.join(rabbit_ips_list)
    env_vars = {
        'OPENSTACK_VIP': fqdn,
        'PUBLIC_ENDPOINT': 'true',
        'HTTPS_OPENSTACK_APIS': str(https).lower(),
        'RABBITMQ_USERNAME': 'openstack',
        'RABBITMQ_PASSWORD': rabbit_pass,
        'RABBIT_IPS_CSV': rabbit_ips_csv,
        'SQL_USERNAME': 'arcus',
        'SQL_PASSWORD': sql_password,
        'SQL_IP': sql_ip,
        'CEPH_ENABLED': str(ceph_enabled).lower()
    }
    env_str = ''
    for env_var in env_vars:
        value = env_vars[env_var]
        env_str += f' -e {env_var}={value} '
    cmd = ('docker run -d '
           '-p 0.0.0.0:1234:1234 '
           '--name arcus_api '
           '--restart=always '
           f'{env_str} {image}')
    shell(cmd)
