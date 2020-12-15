# Voithos VMware Utilities

## Optional - Set VMware environment variables

The `voithos vmware` commands can be used in two ways. Either every call can set the `--username`,
`--password` and `--ip-addr` options, or environment variables can be defined. If you lead the
`export` commands with a space, they won't be saved to your bash history.

```bash
 export VMWARE_USERNAME=
 export VMWARE_PASSWORD=
 export VMWARE_IP_ADDR=
```

## Show VMs: voithos vmware show-vm

Voithos can query a VMware service to list useful information about the virtual machines hosted
upon it.

### --format: Output Formats
Thee output formats are supported:

1. `pprint`: "Pretty print", nicely formatted, human readable output showing all of the information
   that Breqwatr considers useful about each VM.
1. `json`: Machine-readable output useful for scripting with the `jq` command
1. `csv`: Ideal for creating spreadsheets, for use in migration planning

### --name: Search argument

The `--name` or `-n` argument can be used multiple times. For each value given, the search results
will filter to VM's who's names contain the given search string. If any name is provided that
equals `*`, all results will be displayed.

### Help

The options of show-vm can be seen with `--help`

```bash
voithos vmware show-vm --help

Usage: voithos vmware show-vm [OPTIONS]

  Show data about provided VMs

Options:
  -i, --ip-addr TEXT   (optional) Overrides environment variable
                       VMWARE_IP_ADDR

  -p, --password TEXT  (optional) Overrides environment variable
                       VMWARE_PASSWORD

  -u, --username TEXT  (optional) Overrides environment variable
                       VMWARE_USERNAME

  -f, --format TEXT    Output format: pprint,json,csv
  -n, --name TEXT      Repetable - names of VMs to display  [required]
  --help               Show this message and exit.
```

## Download VM: voithos vmware download-vm

The `download-vm` command will create an export job in VMware and then download the VMDK files
that make up the selected VM. The VM is chosen using the UUID, which can be collected using
`show-vm`. The saved VMDK files are thin provisioned, so they won't take up any more space than is
required.

### Help

```
voithos vmware download-vm --help
Usage: voithos vmware download-vm [OPTIONS] VM_UUID

  Download a VM with a given UUID

Options:
  --interval TEXT        Optional CLI Print interval override - 0 disables
                         updates

  -i, --ip-addr TEXT     (optional) Overrides environment variable
                         VMWARE_IP_ADDR

  -p, --password TEXT    (optional) Overrides environment variable
                         VMWARE_PASSWORD

  -u, --username TEXT    (optional) Overrides environment variable
                         VMWARE_USERNAME

  -o, --output-dir TEXT  Optional destination directory
  --help                 Show this message and exit.
```
