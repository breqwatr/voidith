""" Commands for VMWare """

import click
import os
import json
from pprint import pprint
from voithos.lib.system import error
import voithos.lib.vmware as vmware


def _escape_csv(value):
    """ Format a CSV value to be safe to use in a CSV (string, escape commas, quotes) """
    str_val = str(value)
    str_val = str_val.replace('"', '""')
    str_val = str_val.replace(",", '","')
    return str_val


def _print_csv(vms):
    """ Print the CSV format output of a list of VMs """
    columns = [
        "uuid",
        "name",
        "os",
        "cores",
        "ram_mb",
        "num_disks",
        "total_storage_gb",
        "used_storage_gb",
        "num_nics",
        "net_list",
        "shared_storage",
    ]
    columns_str = ",".join(columns)
    print(columns_str)
    for vm in vms:
        line = []
        line.append(_escape_csv(vm["uuid"]))
        line.append(_escape_csv(vm["name"]))
        line.append(_escape_csv(vm["guest_os"]))
        line.append(_escape_csv(vm["num_cpu"]))
        line.append(_escape_csv(vm["ram"]["total_mb"]))
        line.append(_escape_csv(vm["storage"]["num_disks"]))
        capacity_gb = sum(disk["capacity_gb"] for disk in vm["storage"]["disks"])
        line.append(_escape_csv(capacity_gb))
        line.append(_escape_csv(vm["storage"]["partitions"]["total_used_gb"]))
        line.append(_escape_csv(vm["network"]["num_interfaces"]))
        net_list = []
        for network in vm["network"]["networks"]:
            net_list.append(network["vswitch_name"])
        net_list_str = " ||| ".join(net_list)
        line.append(net_list_str)
        shared_storage = "no"
        for disk in vm["storage"]["disks"]:
            if disk["shared"]:
                shared_storage = "yes"
        line.append(shared_storage)
        print(",".join(line))


@click.option(
    "--name", "-n", multiple=True, help="Repetable - names of VMs to display", required=True
)
@click.option("--format", "-f", "output", default="pprint", help="Output format: pprint,json,csv")
@click.command(name="show-vm")
def show_vm(name, output):
    """ Show data about provided VMs """
    allowed_outputs = ["pprint", "json", "csv"]
    if output not in allowed_outputs:
        error(f"Invalid output format chosen. Supported outputs: {allowed_outputs}", exit=True)
    vms = vmware.filter_vms(names=name)
    if output == "pprint":
        for vm in vms:
            pprint(vm)
    elif output == "json":
        print(json.dumps(vms))
    elif output == "csv":
        _print_csv(vms)


def get_vmware_group():
    """ Return the VMware click group """

    @click.group(name="vmware")
    def vmware_group():
        """ VMWare utilities """

    vmware_group.add_command(show_vm)
    return vmware_group
