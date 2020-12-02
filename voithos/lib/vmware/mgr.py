""" VMware command lib """

import os
import ssl

from pyVim import connect
from pyVmomi import vim

from voithos.lib.system import error
from voithos.lib.vmware.common import debug


def _environ(name, value=None):
    """Safely return the value of an environment variable, else throw nice error
    If value!=None then it is used instead of checking the env var
    """
    ENV_VARS = ["VMWARE_USERNAME", "VMWARE_PASSWORD", "VMWARE_IP_ADDR"]
    if name not in ENV_VARS:
        raise (f"unsupported _environ name {name}")
    if value is not None:
        return value
    if name not in os.environ:
        error(f"Env var {name} is required,missing. REQUIRED={ENV_VARS}", exit=True)
    return os.environ[name]


def _get_ssl_error():
    """ Different versions of Python (3.6 vs 3.8) throw different SSL exceptions """
    if hasattr(ssl, "SSLCertVerificationError"):
        return ssl.SSLCertVerificationError
    else:
        return ssl.SSLError


class VMWareMgr:
    """ Object used to manage VMWare interactions """

    def __init__(self, username=None, password=None, ip_addr=None):
        """ Constructor the exporter, loading creds from env vars if needed """
        self.username = _environ("VMWARE_USERNAME", username)
        self.password = _environ("VMWARE_PASSWORD", password)
        self.ip_addr = _environ("VMWARE_IP_ADDR", ip_addr)
        self.conn = None
        self.connect()
        self.vms = []
        self.load_vms()

    conn = None  # Required for __del__

    def __del__(self):
        """ Clean up the conenction when the object is GC'd """
        connect.Disconnect(self.conn)

    def connect(self):
        """ Connect to the configured VMWare service & set self.conn """
        try:
            SSLVerificationError = _get_ssl_error()
            try:
                self.conn = connect.SmartConnect(
                    host=self.ip_addr, user=self.username, pwd=self.password
                )
            except SSLVerificationError:
                try:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                    ctx.verify_mode = ssl.CERT_NONE
                    self.conn = connect.SmartConnect(
                        host=self.ip_addr, user=self.username, pwd=self.password, sslContext=ctx
                    )
                except (ssl.SSLEOFError, OSError):
                    self.conn = connect.SmartConnectNoSSL(
                        host=self.ip_addr, user=self.username, pwd=self.password
                    )
        except vim.fault.InvalidLogin:
            error(f"ERROR: Invalid login for VMware server {self.ip_addr}", exit=True)

    def load_vms(self, entity=None):
        """Return a list of each VM from all datacenters connected to self.conn
        This function is recursive, since the VMs can be in a tree-like directory structure
        """
        if entity is None:
            debug("Starting recursive VM search")
            self.load_vms(entity=self.conn.content.rootFolder)
            return
        if isinstance(entity, vim.VirtualMachine):
            debug(f"VM:         {entity}  -  {entity.name}")
            self.vms.append(entity)
            return
        if isinstance(entity, vim.Folder):
            debug(f"FOLDER:     {entity}  -  {entity.name}")
        if isinstance(entity, vim.Datacenter):
            debug(f"DATACENTER: {entity}  -  {entity.name}")
        if hasattr(entity, "vmFolder"):
            self.load_vms(entity.vmFolder)
        if hasattr(entity, "childEntity"):
            for child in entity.childEntity:
                self.load_vms(child)

    def find_vms_by_name(self, names):
        """Return a list of VMs who's names contain any element found in names.
        Return all VMs if "*" is an element in names
        """
        if "*" in names:
            return self.vms
        return (vm for vm in self.vms if any(name in vm.name for name in names))

    def find_vm_by_uuid(self, uuid):
        """ Return a single VM with a given UUID, or None """
        return next((vm for vm in self.vms if vm.config.uuid == uuid), None)
