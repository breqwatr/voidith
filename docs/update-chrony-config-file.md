# Update chrony config file.
After the deployment is complete. Chrony container keeps restarting. 
In order to make it work, correct `chrony.conf` permission in `config.json` file from 0600 to 0666.
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
            "perm": "0600"
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
Change it on all the nodes. If you have huge number of nodes, you can also `scp` updated file to all nodes at correct locations.
