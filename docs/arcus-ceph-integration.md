# Arcus Ceph Integration

When Arcus is being used on an OpenStack cloud with volumes backed by Ceph, an **integration** can
be configured to expand Arcus' support for Ceph's features, such as storage capacity reporting and
snapshot restore.

## Determine the API Address

First, identify the IP address and port of your Arcus API service. While Arcus can run anywhere,
Breqwatr prefers to deploy it on the OpenStack control nodes so it leverages OpenStack's VIP. If
you've done the same, then the `--api-addr` used throughout this document is likely:
`http://<openstack-vip>:1234`.


## Show the Ceph integration-type

```bash
voithos service arcus api integrations show-type Ceph --api-addr http://example.com:1234
```

Note the fields list. These are going to be used with `--field` to define the integration
parameters. Those listed as passwords will be securely encrypted in the Arcus database.



---


## Collect field values


### display_name

This is a human readable value that can show up above the capacity report. Make it up.


### keyring_user

Often we'll just use the admin keyring, so this would be `admin`. You can optionally create a
dedicated service account or re-use Cinder's.


### keyring_key

On a Ceph node, show the keyring contents. For the `admin` keyring, execute:

```bash
cat /etc/ceph/ceph.client.admin.keyring
```

Find the line that looks like this:

```
        key = AQAoQTRf+50/HRAAQxQ+HPkqOGVAlL3Awrvx2Q==
```

The string to the right of `key =` is the value you're after.


### mon_host

Show your ceph.conf file:

```bash
cat /etc/ceph/ceph.conf
```

Look at the `mon_host` or `mon host` line. If it's using the `v2` format, it will be listed in
square brackets with a version identifier and ports. If using the older format, it's just a comma
delimited list of IP addresses. Arcus expects the old format.


### fsid

```bash
cat /etc/ceph/ceph.conf | grep fsid | awk '{print $3}'
```


### ratio

This is the near-full ratio at which Ceph will start going into read-only mode to prevent
**bad things** from happening. By default this is 0.85.


### pool

This is the name of the Ceph pool which Cinder's volume backend is configured to use. By default
we use `volumes` as the name of the pool.


### Set the SA in Arcus

- Note how the quotes are used to allow spaces in the display name.
- The `username` and `password` are your OpenStack administrator user's credentials. Arcus checks
  to make sure you have administrative access before allowing alterations to the Integrations data.
- You can also shorthard `--field` with `-f` to save time, if you like.

Here's a filled out example:

```bash
voithos service arcus api integrations create \
  --api-addr http://10.10.111.222:1234 \
  --username arcusadmin \
  --password password \
  --type Ceph \
  --field display_name "Ceph - volumes" \
  --field keyring_user admin \
  --field keyring_key "AQAoQTRf+50/HRAAQxQ+HPkqOGVAlL3Awrvx2Q==" \
  --field mon_host 10.10.111.222 \
  --field fsid 4a241f8b-203e-4941-90c4-6f4d93e8e0c3 \
  --field ratio 0.85 \
  --field pool volumes
```
