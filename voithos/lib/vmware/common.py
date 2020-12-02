""" Common funnctions for VMware lib """
import os


def debug(msg):
    """ Print a debug message when VMWARE_DEBUG = 'true' """
    env_var = "VMWARE_DEBUG"
    if env_var not in os.environ or os.environ[env_var] != "true":
        return
    print(f"VMWARE_DEBUG: {msg}")
