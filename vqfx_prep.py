#!/usr/bin/python3

import pynetbox

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectError
from jnpr.junos.utils.start_shell import StartShell

import argparse
import os
import subprocess
import sys
import re

from pathlib import Path
import json
import yaml

import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')

from time import sleep
from pprintpp import pprint as pp

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--sshconfig', help='SSH config file', default='/home/cathal/.ssh/config')
parser.add_argument('-u', '--user', help='User to add to devices', default='cathal')
parser.add_argument('-k', '--key', help='SSH pubkey for user', default='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8GQKaT22CZdxJcpLNsq1LYm9bTeI7xnblYrrx8HXQH cathal@officepc')
args = parser.parse_args()

def main():
    """ Removes all the vQFX junk that is there at startup. """

    # add_user_config()

    devices = get_clab_vqfx()

    for device_name, dev_conf in devices.items():
        add_user_config(device_name, dev_conf['ip'])

        vqfx = get_junos_dev(dev_conf['ip'])
        clear_int_config(vqfx)
        vqfx.close()


def get_clab_vqfx():
    devices = {}
    labname = ""
    clab_vqfx = subprocess.getoutput("sudo clab inspect -a | grep vqfx")
    for line in clab_vqfx.split('\n'):
        split_line = line.split()
        if len(split_line) == 21:
            # Line has lab name in it
            labname = split_line[5]
        nodename = split_line[-14].removeprefix(f"clab-{labname}-")
        ip = split_line[-4].split("/")[0]

        devices[nodename] = {
            "ip": ip
        }

    return devices


def add_user_config(dev_name, dev_ip):
    """ Adds configured user and ssh key using CLI to allow key-based SSH for Homer """

    print(f"Trying to conenct to {dev_name} at {dev_ip}... ", end="", flush=True)   
    vqfx = Device(host=f"{dev_ip}", port=22, user="root", password="Juniper")
    ss = StartShell(vqfx)
    ss.open()
    print("connected.")

    ret_val, lines = ss.run('cli')
    getprompt(lines)
    print(f"Adding user {args.user} with CLI... ", end="", flush=True)
    ret_val, lines = ss.run('configure')
    getprompt(lines)
    ret_val, lines = ss.run(f"set system login user {args.user} class super-user")
    getprompt(lines)
    ssh_key_type = args.key.split()[0]
    ret_val, lines = ss.run(f"set system login user {args.user} authentication {ssh_key_type} \"{args.key}\"")
    getprompt(lines)
    ret_val, lines = ss.run("commit")
    getprompt(lines)
    ret_val, lines = ss.run("exit")
    getprompt(lines)
    print("done.")

    vqfx.close()


def getprompt(lines):
    """ Returns when it gets CLI promot, if none found exits with error. """
    for line in lines.split('\n'):
        if line.endswith("> ") or line.endswith("# "):
            return line

    print(f"Never got prompt - quitting - output receieved:\n{lines}")
    sys.exit(1)


def clear_int_config(vqfx):
    """ Removes all the junk / non-existant interface configuration that is 
        on vQFX out of the box. """

    # Get list of real interfaces on device
    real_ints = set()
    device_ints = vqfx.rpc.get_interface_information({'format':'json'}, terse=True)
    for real_int in device_ints['interface-information'][0]['physical-interface']:
        real_ints.add(real_int['name'][0]['data'])

    # Get interface configuration from device
    config = vqfx.rpc.get_config(options={'format':'json', 'database' : 'committed'})
    del config['configuration']['@']
    int_confs = config['configuration']['interfaces']['interface']

    new_int_confs = []
    for int_conf in int_confs:
        if int_conf['name'].startswith("em"):
            new_int_confs.append(int_conf)
        elif ":" in int_conf['name'] or int_conf['name'] not in real_ints:
            continue
        else:
            new_int_confs.append(int_conf)
            for unit in new_int_confs[-1]['unit']:
                if "family" in unit:
                    del(unit['family'])
        
    config['configuration']['interfaces']['interface'] = new_int_confs
    # Load the config to the device
    vqfx.config.load(json.dumps(config), format="json", overwrite=True)
    vqfx.config.commit_check()
    config_diff = vqfx.config.diff()

    if config_diff != None:
#        for line in config_diff.split('\n'):
#            print(line)
#        print()
#        user_input = input("Apply changes (y/n): ")
#        if user_input.lower() == "y" or user_input.lower() == "ye" or user_input.lower() == "yes":  
        print("Trying to commit config change removing interfaces (wait 20 sec)... ", end="", flush=True)
        vqfx.config.commit(confirm=1)
        sleep(20)
        vqfx.config.commit()
        print(" done.\n")
#        else:
#            print("Rolling back...", end="", flush=True)
#            vqfx.config.rollback()
#            print(" done.")
    else:
        print("No interface config needs to be removed... skipping.\n")
    

def get_junos_dev(dev_name):
    # Initiates NETCONF session to router
    try:
        device = Device(dev_name, username=args.user, ssh_config=args.sshconfig, port=22)
        device.open()
    except ConnectError as err:
        print(f"Cannot connect to device: {err}")
        sys.exit(1)

    # Get config object
    device.bind(config=Config)

    return device


if __name__ == '__main__':
    main()
