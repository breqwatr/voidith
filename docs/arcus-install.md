# Installing Arcus

Arcus is ran as a few Docker containers. Deploy Voithos to install Arcus.


---


## Apply license key

Voithos can't download Arcus without the license

```bash
voithos config license --set <license>
```


---


## Collect Information

- `--secret`: Encryption key for stored passwords
- `--sql-ip`: IP address for the SQL cluster
- `--sql-password`: Password for the `arcus` user in SQL
- `--rabbit-ip`: IP address(es) of the RabbitMQ servers
- `--rabbit-pass`: Password for RabbitMQ
- `--openstack-fqdn`: Address of the Openstack API endpoints
- `--openstack-ip` Unlike `openstack-fqdn`, this cannot be a domain name and must be the public VIP
- `--cert-key`: HTTPS private key file's absolute path
- `--cert-path`: HTTPS public certificate file absolute path
- `--api-ip`: Generally this is also the public VIP - this is where Arcus API can be reached

### secret

Make the value up yourself and save it somewhere. Be sure to use the same one on all API services
deployed to a cluster.

### sql-ip

This is the internal VIP as defined in globals.yml.

```bash
cat globals.yml | grep kolla_internal_vip_address
```

### sql-password

This is the password that was chosen when executing the `voithos service arcus api database-init`
command in the `--arcus-pass` option.

### rabbit-ip

This is actually a repeated option, for instance if you have three nodes you might run:

```bash
--rabbit-ip 192.168.0.11 --rabbit-ip 192.168.0.12 --rabbit-ip 192.168.0.13
```

The IP address is the internal interfaces IP address. This is the address of the interface defined
by `network_interface` in the globals.yml file.

### rabbit-pass

This is the password for RabbitMQ as defined by the `passwords.yml` file.

```bash
cat passwords.yml | grep rabbitmq_password
```

### openstack-fqdn

This is either the domain name or VIP of the cloud, depending on your `globals.yml` settings.

If `kolla_external_fqdn` in `globals.yml` is defined and does not equal
`kolla_external_vip_address` then use the value of `kolla_external_fqdn`. Otherwise there is no DNS
entry for this cloud's VIP, so you should use the value of `kolla_external_vip_address`.

```bash
cat globals.yml | grep kolla_external_fqdn
# or
cat globals.yml | grep kolla_external_vip_address
```

### openstack-ip

This is always the external VIP IP address.

```bash
cat globals.yml | grep kolla_external_vip_address
```

### cert-key & cert-path

This file might not be present on the server yet. It was created in the `certificates/` folder when
you ran `voithos openstack get-certificates`. You'll need to SCP that certificates folder to the
server which is running Arcus.

```bash
scp -r certificates/  <hostname>@<ip>:/etc/kolla/

# Note that often the SSH user doesn't have access to /etc/kolla, so you may need to put it in the
# user's home directory then move it there as root inside an SSH session.
```

Once you've gotten the `certificates/` folder onto the host running Arcus, the relative paths
are:
- `--cert-key`: `/etc/kolla/certificates/private/haproxy.key`
- `--cert-path`: `/etc/kolla/certificates/private/haproxy.crt`


### api-ip

`api-ip` points to the IP address of Arcus-API. Typically this is a VIP.

When you're deploying Arcus on the control plane servers of a Kolla-Ansible based cloud (as is the
current recommended setup), this is the external VIP in `globals.yml`.

```bash
cat globals.yml  | grep kolla_external_vip_address
```


---


## Arcus Client

Arcus Client (arcus-client) is the web UI built to leverage the Arcus API.


Pull the image from Breqwatr's private registry

```bash
voithos service arcus client pull --release 7.5
```

Start the client. When prompted for the API IP, enter the address the API will listen on, even if
it isn't there yet.

```bash
voithos service arcus client start --help
```


---


## Arcus API

Arcus API (arcus-api)is the orchestration agent that operates against OpenStack Ceph, and other
private cloud services.

Initialize the database

- `--arcus-pass`: Make up this password yourself and save it in a password manager
- `--admin-pass`: Use the root password from the passwords.yml. It's defined by `database_password`
  and can be queried like this: `cat ~/clouds/mds1/passwords.yml  | grep ^database`
- `--admin-user`: For Kolla-Ansible based clouds, just use `root`
- `--host`: The internal vip - run `cat globals.yml  | grep kolla_internal_vip_address`

```
voithos service arcus api database-init \
  --arcus-pass <password to set for the arcus database user> \
  --admin-pass <database password from passwords.yml> \
  --admin-user root \
  --host <internal vip>
```

Pull the image from Breqwatr's private registry

```bash
voithos service arcus api pull --release 7.5
```

Start the service

```bash
voithos service arcus api start --help
```


### LDAP Config

If Active Directory LDAP will be used, follow the [Arcus LDAP config guide](/arcus-ldap-config.html).



---



## Arcus Manager

Arcus Manager (arcus-mgr) is a distributed task-runner that operates Arcus's periodic automation.

Pull the image from Breqwatr's private registry

```bash
voithos service arcus mgr pull --release 7.5
```

Launch the arcus-mgr service

```bash
voithos service arcus mgr start --help
```


---


## Configure the service account

### Create the SA in OpenStack

This requires that the openstack client be set up somewhere, and assumes you have an openrc
file located at `/etc/kolla/admin-openrc.sh`. Adjust accordingly.

```bash
openstack user create arcusadmin --password <service account password>
openstack role add --user arcusadmin --project admin admin
openstack role add --user arcusadmin --project admin _member_
openstack role add --user arcusadmin --domain default admin
```

---


## Configure a volume type

Arcus works best when a custom volume type is defined (instead of using `__DEFAULT__`).

```bash
openstack volume type create --public --property volume_backend_name='<backend-name>' <name>
```
