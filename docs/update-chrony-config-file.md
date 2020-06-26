# Update chrony config file.
After the deployment is complete, Chrony container will keep restarting. 
In order to make it work, correct `chrony.conf` permissions in `/etc/kolla/chrony/config.json` file from 0600 to 0666.
It should look like this:
```
cat /etc/kolla/chrony/config.json 
{
    "command": "/usr/sbin/chronyd -d -f /etc/chrony/chrony.conf",
    "config_files": [
        {
            "source": "/var/lib/kolla/config_files/chrony.conf",
            "dest": "/etc/chrony/chrony.conf",
            "owner": "chrony",
            "perm": "0666"
        }
    ],
    "permissions": [
        {
            "path": "/var/log/kolla/chrony",
            "owner": "chrony:kolla",
            "recurse": true
        },
        {
            "path": "/var/lib/chrony",
            "owner": "chrony:chrony",
            "recurse": true
        }
    ]
}
```
Change it on all nodes and restart chrony containers by running `docker restart chrony`.
