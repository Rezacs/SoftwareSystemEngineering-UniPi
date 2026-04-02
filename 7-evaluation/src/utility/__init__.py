import ipaddress
"""
This module offers some utility variables nd functions
"""
def ip_to_float(ip_string):
    """
    Convert an IP address string to a normalized float.
    """
    try:
        return float(int(ipaddress.ip_address(ip_string))) / float(int(ipaddress.ip_address("255.255.255.255")))
    except ValueError:
        return 0.0  # Return 0.0 if the IP is invalid

import os

project_root = os.path.realpath(__file__ + "/../../..")
data_folder = os.path.join(project_root, "data")

