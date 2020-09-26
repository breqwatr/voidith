# Grafana Graphs and Alerts Setup
As you have done the initial setup for grafana and prometheus in the previous section,
 it's time to test out graphs and alerts for cloud servers resources. There are two ways
 to do that.
* Use voithos command
* Do it manually

# Voithos Command for Graphs and Alerts Creation
By running this command, you will create all the graphs and alerts mentioned in the manual
 section. You can change graphs and alerts settings manually afterwards if you want to try
 different settings.
```bash
# ip: ip address to access grafana.
# port: port being used by grafana.
# http/https: Is it using http or https?
# password: admin-user password that can be found in passwords.yml file.

voithos service grafana dashboard-create \
 --ip <grafana-ip> \
 --port <grafana-port> \
 --<http/https> \
 --user admin \
 --password <admin-password>
```  

# Manual Creation of Graphs and Alerts

## Create Dashboard
* Hover over `Dashboards` symbol (2nd symbol) on the left hand side and click on `Manage`.
* Click on `New Dashboard` button.
* Now click on save button (2nd symbol on top right corner). Enter the name of dashboard and
click on `Save` button

## Create Panels
**For creating a new graph follow these steps**
* Click on `Add panel` button (1st button on top right). It will open a new panel.
* Click on `Add Query` button inside new panel.
* Click datasource dropdown next to `Query` and choose `Prometheus`.
* In the `Metric` field put the query for monitoring a resource.
* Check queries for different resources in section below.
* Click on `General` symbol (2nd symbol) on left side and add panel title.
* Click on back button on top left corner.
* Click save button (4th symbol) on top right corner and save it.

## Example Queries
**Note**: Time period for any query using irate function must be atleast more than twice the
`scrape_interval`.

### CPU Idle
* **Query:** (avg by (instance) (irate(node_cpu_seconds_total{job="node",mode="idle"}[5m])) * 100)

### Free Memory
* **Query:** node_memory_MemFree_bytes
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.

### Available Memory
* **Query:** node_memory_MemAvailable_bytes
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.

### Boot Disk Free
* **Query:** node_filesystem_avail_bytes{mountpoint="/"}

### Network Bytes Received 
* **Query:** irate((node_network_receive_bytes_total{device=~"en.*"}[5m]))
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.
**Note**: In device part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc

### Network Bytes Transmitted
* **Query:** irate((node_network_transmit_bytes_total{device=~"en.*"}[5m]))
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.
**Note**: In device part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc

### Node State
* **Query:** up{job="node"}

### Network Interface State
* **Query:** node_network_up{job="node", interface=~"eno.*"}
**Note**: In interface part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc


## Alerts Setup

### CPU Idle
* Hover over the name of graph for cpu idle.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name 
    * evaluation interval: `1m`
    * time: `5m`
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun percent of cpu idle to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message 

### Free Memory
* Hover over the name of graph for free memory.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun bytes of free memory to trigger alert. Multiply with `1073741824` for GBs.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message


### Boot Disk Free
* Hover over the name of graph for free boot disk.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun bytes of free disk to trigger alert. Multiply with `1073741824` for GBs.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Bytes Received
* Hover over the name of graph for network bytes received.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `max()`
    * OF: `query (A, 5m, now)`
    * Keep `IS ABOVE`
    * Add maximum bytes received to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Bytes Transmitted
* Hover over the name of graph for network bytes transmitted.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `max()`
    * OF: `query (A, 5m, now)`
    * Keep`IS ABOVE`
    * Add maximum bytes transmitted to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Node State
* Hover over the name of graph for nodes state.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Put 1 to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Interface State
* Hover over the name of graph for network interfaces state.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add 1 to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message
