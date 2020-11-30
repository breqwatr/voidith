# Installing Syslog

Syslog server container(s) can be deployed on one or more cloud servers.
They will allow cloud admins to monitor datacenter devices logs from cloud server(s).

---

## Configure logging on switches/routers
First we need to configure logging on devices of which we want to monitor logs.
Here are few examples of configuring logging:

### Arista
```
logging host <syslog-server-1-ip> <syslog-server-1-port>
.
.
.
logging host <syslog-server-n-ip> <syslog-server-n-port>
logging source-interface <Interface>
logging buffered <severity>
```

### Mellanox
```
logging <syslog-server-1-ip> <syslog-server-1-port>
.
.
.
logging <syslog-server-n-ip> <syslog-server-n-port>

logging monitor events notice
```

## Configure Syslog server(s)
Now ssh into the server(s) configured as syslog servers in previous step. 
Run this command to pull rsyslog container image:
```
voithos service rsyslog pull -r <tag>
```

Run this command to start rsyslog container:
```
# port -> syslog server port (should be same as one configured in previous step)
# syslog-client-ip -> client device ip address
voithos service rsyslog start -p <port> -s <syslog-client-ip-1> -s <syslog-client-ip-n> -r <tag>
```

Now you can see logs in `/var/log/networks/%HOSTNAME%.log`. Log files may not show up till the first
log is generated after syslog server creation. 
