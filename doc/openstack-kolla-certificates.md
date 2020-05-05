[Index](/)
\> Configure HTTPS for OpenStack APIs

# Configure HTTPS for OpenStack APIs

OpenStack uses instances a combination of HAProxy and keepalived to
provide load-balancing and failover to its HTTP APIs. HAProxy can be configured
to use HTTPS by providing it with certificate files.

Breqwatr does not support non-HTTPS cloud deployments.

In Kolla-Ansible, HTTPS is enabled by setting `kolla_enable_tls_external` to
 `yes` `globals.yml`. Once enabled, Kolla-Ansible will configure HAProxy to use
the provided certificates and  attempt to copy them to the correct paths.

```yml
# globals.yml
kolla_enable_tls_external: yes
```

Certificates are deployed in a `certificates/` directory.

By default Kolla-Ansible will look for the following two files:

- **certificates/haproxy.pem**: This is the public and private certificate
  combined.
- **certificates/ca/haproxy.crt**: When applicable, this is the certificate
  authority certificate.

The filenames can be modified in `globals.yml`.


## Generate self-signed certificates

Use Voidith's `generate-certificates` command to generate new self-signed
certificates. A new directory named `certificates/` will be created in the
directory specified by `--config-dir`.

```bash
# creates ./certificates/
voidith openstack get-certificates \
  --release stein \
  --globals-file globals.yml \
  --passwords-file passwords.yml
```

## Using your own certificates

Instead of generating the self-signed certificates, copy your valid ones into
the `config/certificates/` directory with the correct filenames.

```bash
mkdir certificates/
cp <valid certificate file path> haproxy.pem
```

Note that haproxy expects to have both the certificate and the private key
text in `haproxy.pem`. You can simply concatenate those two files and rename
them.
