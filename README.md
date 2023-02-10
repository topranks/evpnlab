# evpnlab

![evpnlab topology](https://raw.githubusercontent.com/topranks/evpnlab/main/diagram.png)

This is a Juniper lab to test some EVPN/VXLAN stuff built using vQFX running on qemu on Linux, orchestrated with [containerlab](https://containerlab.srlinux.dev/).  The vQFX configuration is automated through [PyEZ](https://github.com/Juniper/py-junos-eznc) and [Homer](https://doc.wikimedia.org/homer/master/introduction.html)

## Installation

The lab is designed to be run on Linux.  As it uses virtual machines to emualte the Juniper devices it is better running directly on bare metal, however it should in theory work in a VM as long as nested virtualization is enabled.

#### 1. Install Docker

Installer docker using [their instructions](https://docs.docker.com/engine/install/).


#### 2. Create docker container image that runs the vQFX VMs

Firstly you'll need to have Juniper's [vQFX](https://www.juniper.net/us/en/dm/free-vqfx10000-software.html) images downloaded.  The vQFX runs as two separate virtual machines, one which takes care of packet forwarding (PFE) and one that manages the device's control plane (vCP).

To run vQFX in containerlab we need to wrap the VM execution in a container that can be run with docker (see [here](https://containerlab.dev/manual/vrnetlab/)).  Once you have the vQFX qemu images you can create this container by using [vrnetlab](https://github.com/vrnetlab/vrnetlab) following the instructions below:

[Juniper vQFX and Containerlab Tutorial](https://www.theasciiconstruct.com/post/junos-vqfx-containerlab/)

When complete you should see the vqfx container image when running 'docker ps'
```
cathal@officepc:~$ sudo docker images 
REPOSITORY           TAG             IMAGE ID       CREATED         SIZE
vrnetlab/vr-vqfx     20.2R1.10       c4402f8ebcbd   24 hours ago    1.83GB
```

#### 3. Create docker container to simulate connected servers

Each of the LEAF switches in the lab has a test server connected.  These are simulated using a docker container.  Any kind of Linux container will work, I typically use "debian:stable-slim".  

Given this is a networking lab it helps to have some networking tools available inside the container.  So I typically run a shell in the container, install the tools I need, then save the updated container as a new image which the lab runs:
```
docker run -it debian:stable-slim bash
```
Then inside the container install whatever packages might be useful:
```
apt update
apt install tcpdump iproute2 iputils-ping mtr-tiny arping traceroute nmap netcat tshark iptables iperf iperf3
```

When the install is finished open another shell on the same machine, and commit the running container as a new image:
```
root@debiantemp:~# docker ps
CONTAINER ID   IMAGE                COMMAND   CREATED         STATUS         PORTS     NAMES
226ce85f24f4   debian:stable-slim   "bash"    7 minutes ago   Up 7 minutes             naughty_goldstine
root@debiantemp:~# 
root@debiantemp:~# docker commit 226ce85f24f4 debian:clab 
sha256:3229de033420148cbbbbce37d5f1415719c173916bea40563a0e5873e483ca08
root@debiantemp:~# 
```

Either way the containerlab topology file will run an image called "debian:clab".  The above process creates an image with this name, if you use another container you can alias it to this name using "docker tag <image_id> debian:clab".

#### 4. Install containerlab

Follow the instructions to [install containerlab](https://containerlab.dev/install/)

#### 5. Install Homer

Install WMF Homer and Ansible using pip:
```
pip3 install homer ansible
```

Ansible isn't used in this project, however the Ansible-provided 'ipaddr' filter for Jinja2 templating is used.  This is a very useful tool when using Homer without the WMF Netbox plugin (which transforms data in advance for use with templates).

TODO: Create fork of Homer which includes the ipaddr module

Until that's done we need to change Homer to import the ipaddr module and make it available to plugins.  To do so locate the "tempaltes.py" Homer file on your system and add this to the top:

```
from ansible_collections.ansible.utils.plugins.filter import ipaddr
```

And then add this line at the end of the __init__ function in the Renderer class:

```
        self._env.filters.update(ipaddr.FilterModule().filters())
```

#### 6. Clone this repo

Clone this repo to your machine:
```
git clone https://github.com/topranks/evpnlab.git
cd evpnlab
```

#### 7. Run the lab

Before running the lab check the docker images are look correct, you should at least have two with names as shown below:
```
root@debiantemp:~# docker images
REPOSITORY           TAG             IMAGE ID       CREATED         SIZE
debian               clab            3229de033420   7 seconds ago   298MB
vrnetlab/vr-vqfx     20.2R1.10       c4402f8ebcbd   24 hours ago    1.83GB
```

You should then be able to run the lab:
```
cathal@officepc:~/evpnlab$ sudo clab deploy -t evpnlab.yaml 
INFO[0000] Containerlab v0.36.1 started                 
INFO[0000] Parsing & checking topology file: evpnlab.yaml 
INFO[0000] Creating lab directory: /home/cathal/evpnlab/clab-evpnlab 
INFO[0000] Creating docker network: Name="evpnlab", IPv4Subnet="172.20.20.0/24", IPv6Subnet="2001:172:20:20::/64", MTU="1500" 
INFO[0000] Creating container: "server3"                
INFO[0000] Creating container: "leaf2"                  
INFO[0000] Creating container: "server2"                
INFO[0000] Creating container: "leaf1"                  
INFO[0000] Creating container: "spine2"                 
INFO[0000] Creating container: "leaf3"                  
INFO[0000] Creating container: "spine1"                 
INFO[0000] Creating container: "server1"                
INFO[0001] Creating virtual wire: leaf1:eth1 <--> spine1:eth1 
INFO[0001] Creating virtual wire: server2:eth1 <--> leaf2:eth3 
INFO[0001] Creating virtual wire: server3:eth1 <--> leaf3:eth3 
INFO[0001] Creating virtual wire: leaf2:eth1 <--> spine1:eth2 
INFO[0001] Creating virtual wire: leaf3:eth2 <--> spine2:eth3 
INFO[0001] Creating virtual wire: leaf3:eth1 <--> spine1:eth3 
INFO[0001] Creating virtual wire: leaf1:eth2 <--> spine2:eth1 
INFO[0001] Creating virtual wire: leaf2:eth2 <--> spine2:eth2 
INFO[0001] Creating virtual wire: server1:eth1 <--> leaf1:eth3 
INFO[0003] Adding containerlab host entries to /etc/hosts file 
+---+----------------------+--------------+----------------------------+---------+---------+----------------+----------------------+
| # |         Name         | Container ID |           Image            |  Kind   |  State  |  IPv4 Address  |     IPv6 Address     |
+---+----------------------+--------------+----------------------------+---------+---------+----------------+----------------------+
| 1 | clab-evpnlab-leaf1   | f115b5bc73e7 | vrnetlab/vr-vqfx:20.2R1.10 | vr-vqfx | running | 172.20.20.8/24 | 2001:172:20:20::8/64 |
| 2 | clab-evpnlab-leaf2   | 53723bff71fa | vrnetlab/vr-vqfx:20.2R1.10 | vr-vqfx | running | 172.20.20.7/24 | 2001:172:20:20::7/64 |
| 3 | clab-evpnlab-leaf3   | 7cffb6ae8930 | vrnetlab/vr-vqfx:20.2R1.10 | vr-vqfx | running | 172.20.20.6/24 | 2001:172:20:20::6/64 |
| 4 | clab-evpnlab-server1 | 2d10d0181162 | debian:clab                | linux   | running | 172.20.20.2/24 | 2001:172:20:20::2/64 |
| 5 | clab-evpnlab-server2 | bd0252f0bf09 | debian:clab                | linux   | running | 172.20.20.5/24 | 2001:172:20:20::5/64 |
| 6 | clab-evpnlab-server3 | ed5b1ec9a01f | debian:clab                | linux   | running | 172.20.20.4/24 | 2001:172:20:20::4/64 |
| 7 | clab-evpnlab-spine1  | 1132c6861d25 | vrnetlab/vr-vqfx:20.2R1.10 | vr-vqfx | running | 172.20.20.9/24 | 2001:172:20:20::9/64 |
| 8 | clab-evpnlab-spine2  | 1fd53e43adfe | vrnetlab/vr-vqfx:20.2R1.10 | vr-vqfx | running | 172.20.20.3/24 | 2001:172:20:20::3/64 |
+---+----------------------+--------------+----------------------------+---------+---------+----------------+----------------------+
```
Then run the attached script to add simple entries for all nodes to your hosts file:
```
cathal@officepc:~/evpnlab$ sudo ./add_fqdn_hosts.py 
removed '/etc/hosts'
renamed '/tmp/new_hosts' -> '/etc/hosts'
```

The vQFX images take a few minutes to boot up.  It's best to wait for maybe 5 minutes before proceeding.  To ensure things are ready SSH into one of the vQFX nodes, and check that you can see the "xe-" interfaces (indicating PFE is connected).  Default pass for the vQFX root user is "Juniper".
```
cathal@officepc:~/evpnlab$ ssh root@leaf1
(root@leaf1) Password:
--- JUNOS 19.4R1.10 built 2019-12-19 03:54:05 UTC
root@vqfx-re:RE:0% 
root@vqfx-re:RE:0% cli
{master:0}
root@vqfx-re> 

{master:0}
root@vqfx-re> show interfaces terse | match "xe-" 
xe-0/0/0                up    up
xe-0/0/0.0              up    up   inet    
xe-0/0/1                up    up
xe-0/0/1.0              up    up   inet    
xe-0/0/2                up    up
xe-0/0/2.0              up    up   inet    
xe-0/0/3                up    up
xe-0/0/3.0              up    up   inet    
xe-0/0/4                up    up
xe-0/0/4.0              up    up   inet    
xe-0/0/5                up    up
xe-0/0/5.0              up    up   inet    
xe-0/0/6                up    up
xe-0/0/6.0              up    up   inet    
xe-0/0/7                up    up
xe-0/0/7.0              up    up   inet    
xe-0/0/8                up    up
xe-0/0/8.0              up    up   inet    
xe-0/0/9                up    up
xe-0/0/9.0              up    up   inet    
xe-0/0/10               up    up
xe-0/0/10.0             up    up   inet    
xe-0/0/11               up    up
xe-0/0/11.0             up    up   inet    

{master:0}
root@vqfx-re> 
```

#### 8. Add JunOS user and SSH key to devices, and remove junk interface config

To use Homer we need to have passwordless SSH working.  The username for the user should match your shell username on the system you are using.  You need to add an SSH pubkey which this user has already added (via 'ssh-keygen -t ed25519' for example).

The included script will do this (run 'sudo false' first just cos):
```
cathal@officepc:~/evpnlab$ sudo false
[sudo] password for cathal: 
cathal@officepc:~/evpnlab$ ./vqfx_prep.py --user cathal --key "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8GQKaT22CZdxJcpLNsq1LYm9bTeI7xnblYrrx8HXQH cathal@officepc"
cathal@officepc:~/evpnlab$ ./vqfx_prep.py
Trying to conenct to leaf1 at 172.20.20.8... connected.
Adding user cathal with CLI... done.
Trying to commit config change removing interfaces (wait 20 sec)...  done.

Trying to conenct to leaf2 at 172.20.20.7... connected.
Adding user cathal with CLI... done.
Trying to commit config change removing interfaces (wait 20 sec)...  done.

Trying to conenct to leaf3 at 172.20.20.6... connected.
Adding user cathal with CLI... done.
Trying to commit config change removing interfaces (wait 20 sec)...  done.

Trying to conenct to spine1 at 172.20.20.9... connected.
Adding user cathal with CLI... done.
Trying to commit config change removing interfaces (wait 20 sec)...  done.

Trying to conenct to spine2 at 172.20.20.3... connected.
Adding user cathal with CLI... done.
Trying to commit config change removing interfaces (wait 20 sec)...  done.
```

NOTE: This takes a *long* time.  For some reason the Juniper [StartShell](https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-program-shell-accessing.html) takes ages to run on the vQFX, at least on my system.  But it works ok.

Once done verify you can SSH on without a password as the user you added:
```
cathal@officepc:~/evpnlab$ ssh leaf1
Last login: Fri Feb 10 11:49:46 2023 from 10.0.0.2
--- JUNOS 19.4R1.10 built 2019-12-19 03:54:05 UTC
{master:0}
cathal@vqfx-re> 
```

#### 9. Add Homer confiuration file

You'll need to add a homer configuration file at **/etc/homer/config.yaml**, contents should be similar to below:
```
base_paths:
  # Base path of public configuration.
  public: /home/cathal/evpnlab/homer_public
  # Base path for the output files generated on the 'generate' action. The directory will be cleaned from all '*.out' files.
  output: /tmp

# Transpors configuration. [optional]
transports:
  username: cathal
  ssh_config: ~/.ssh/config
  junos:
    ignore_warning:
      - statement must contain additional statements
      - statement has no contents
      - config will be applied to ports
```

#### 10. Run Homer to add configuration to JunOS devices
```
homer '*' commit "Add config to lab devices"
```

Type 'yes' to apply the config to each device when prompted.  Once done give it a minute or two and you should see the config is there and protocol adjacencies start coming up.

```
cathal@LEAF1> show ospf neighbor    
Address          Interface              State           ID               Pri  Dead
10.1.1.0         xe-0/0/0.0             Full            1.1.1.1          128    33
10.1.2.0         xe-0/0/1.0             Full            2.2.2.2          128    36
```

#### Connect to servers

To connect to any of the 'server' containers run bash in them with docker:
```
cathal@officepc:~/evpnlab$ docker exec -it clab-evpnlab-server1 bash
root@server1:/# 
root@server1:/# ip -br addr show 
lo               UNKNOWN        127.0.0.1/8 ::1/128 
eth0@if170       UP             172.20.20.2/24 2001:172:20:20::2/64 fe80::42:acff:fe14:1402/64 
eth1@if201       UP             fe80::a8c1:abff:fe6f:256a/64 
```

Interfaces, vlans or whatever can be configured using stardard ip command syntax.
