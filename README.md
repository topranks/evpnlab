# evpnlab

![evpnlab topology](https://raw.githubusercontent.com/topranks/evpnlab/main/diagram.png)

This is a Juniper lab to test some EVPN/VXLAN stuff built using vQFX running on qemu on Linux, orchestrated with [containerlab](https://containerlab.srlinux.dev/).  The vQFX configuration is automated through [PyEZ](https://github.com/Juniper/py-junos-eznc) and [Homer](https://doc.wikimedia.org/homer/master/introduction.html).

## Install & Run Lab

The lab is designed to be run on Linux.  As it uses virtual machines to emualte the Juniper devices it is better running directly on bare metal, however it should in theory work in a VM; as long as nested virtualization is enabled.

#### 1. Install Docker

Installer docker using [their instructions](https://docs.docker.com/engine/install/).


#### 2. Create docker container image that runs the vQFX VMs

Firstly you'll need to have Juniper's [vQFX](https://www.juniper.net/us/en/dm/free-vqfx10000-software.html) images downloaded.  The vQFX runs as two separate virtual machines, one which takes care of packet forwarding (PFE) and one that manages the device's control plane (vCP).

To run vQFX in containerlab we need to wrap the VM execution in a container that can be run with docker (see [here](https://containerlab.dev/manual/vrnetlab/)).  Once you have the vQFX qemu images you can create this container by using [vrnetlab](https://github.com/vrnetlab/vrnetlab) following the instructions below:

[Juniper vQFX and Containerlab Tutorial](https://www.theasciiconstruct.com/post/junos-vqfx-containerlab/)


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

Either way the containerlab topology file will run an image called "**debian:clab**".  The above process creates an image with this name, if you use another container you can alias it to this name using "docker tag <image_id> debian:clab".

#### 4. Install containerlab

Follow the instructions to [install containerlab](https://containerlab.dev/install/)

#### 5. Clone this repo

Clone this repo to your machine:
```
git clone https://github.com/topranks/evpnlab.git
cd evpnlab
```

#### 6. Run the lab

Before running the lab check the docker images look correct, you should at least have the two shown below:
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

The vQFX VMs take a few minutes to boot and initialize.  It's best to wait for maybe 5 minutes before proceeding.  To check if a vQFX is ready you can SSH into it, and check that you can see the "xe-" interfaces (this indicates PFE is connected).  Default pass for the vQFX root user is "Juniper".
```
cathal@officepc:~/evpnlab$ ssh root@leaf1
(root@leaf1) Password:
--- JUNOS 19.4R1.10 built 2019-12-19 03:54:05 UTC
root@vqfx-re:RE:0% 
root@vqfx-re:RE:0% cli
{master:0}
root@vqfx-re> 

{master:0}
root@vqfx-re> show interfaces terse | match "xe-0/0/0" 
xe-0/0/0                up    up
xe-0/0/0.0              up    up   inet    
```

**At this point the lab is up and running, and we can configure the nodes.**

### A note on interface naming

Containerlab / vrnetlab requires us to use interface names in the form "ethX".  Vrnetlab builds the vQFX container image with a TC rule to map traffic from the first of these (eth0) to the "em0" interface on the vQFX vCP.  This is used for management access.

The 'eth1' interface in each container is mapped to 'xe-0/0/0' on the vQFX using a similar rule, 'eth2' is mapped to 'xe-0/0/1', and so on.  For the containerlab topology file we need to use the "ethX" interface naming, when we configure with Homer or something that is talking to JunOS we instead need to use the 'xe-0/0/x' convention.

## Configure vQFX devices using Homer

#### 1. Install Homer

Install WMF Homer and Ansible using pip:
```
pip3 install homer ansible
```

Ansible isn't used in this project, however the Ansible-provided 'ipaddr' filter is used in some of the Jinja2 templates.  This is a very useful tool when using Homer with only YAML files (i.e. without the Netbox plugin or similar to transform data in advance).

TODO: Create fork of Homer which includes the ipaddr module

For now you'll need to change Homer to import the ipaddr module and make it usable in templates.  To do so locate the "tempaltes.py" Homer file on your system and add this to the top:

```python
from ansible_collections.ansible.utils.plugins.filter import ipaddr
```

And then add this line at the end of the __init__ function in the Renderer class:

```python
        self._env.filters.update(ipaddr.FilterModule().filters())
```

#### 2. Add Homer confiuration file

You'll need to create a homer configuration file at **/etc/homer/config.yaml**, contents should be similar to below.  The critical part is that the path beside 'public:' points to the "homer_public" directory inside the evpnlab dir cloned from this repo.
```yaml
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

#### 3. Set up JunOS user with ssh public key

To use Homer we need to have passwordless SSH working, so we need to add a user and SSH public key for them.  The username should be the same as on the local system where you're running homer.  That user will need an ed25519 ssh keypair in ~/.ssh/ already, if not create one with 'ssh-keygen -t ed25519'.

The included script will add a user to all containerlab vQFX devices it finds:
```
cathal@officepc:~/evpnlab$ sudo ./vqfx_prep.py --user cathal --key "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8GQKaT22CZdxJcpLNsq1LYm9bTeI7xnblYrrx8HXQH cathal@officepc"
Trying to conenct to leaf1 at 172.20.20.8... connected.
Adding user cathal with CLI... done.
```

NOTE: This takes a *long* time.  For some reason the Juniper [StartShell](https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-program-shell-accessing.html) takes ages to run on the vQFX, at least on my system.  But it works ok, I need to revisit to see why it goes so slow.

Once done verify you can SSH on without a password as the user you added:
```
cathal@officepc:~/evpnlab$ ssh leaf1
Last login: Fri Feb 10 11:49:46 2023 from 10.0.0.2
--- JUNOS 19.4R1.10 built 2019-12-19 03:54:05 UTC
{master:0}
cathal@vqfx-re> 
```

#### 4. Run Homer to add configuration to JunOS devices
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

## Connect to and configure servers

To connect to any of the 'server' containers run bash in them with docker:
```
cathal@officepc:~/evpnlab$ docker exec -it clab-evpnlab-server1 bash
root@server1:/# 
```

Interfaces, vlans or whatever can be configured using stardard ip command syntax.  For example:

Server1:
```
ip addr add 198.18.100.11/24 dev eth1
ip route add 198.18.0.0/16 via 198.18.100.254
```
Server2:
```
ip addr add 198.18.100.12/24 dev eth1
ip route add 198.18.0.0/16 via 198.18.100.254
```
Server3:
```
ip addr add 198.18.200.13/24 dev eth1
ip route add 198.18.0.0/16 via 198.18.200.254
```

Networking should work if all going well!
```
root@server3:~# mtr -b -r -c 3 198.18.100.11
Start: 2023-02-10T12:38:03+0000
HOST: server3                     Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 198.18.200.254             0.0%     3  101.3 123.1 101.2 166.7  37.8
  2.|-- ???                       100.0     3    0.0   0.0   0.0   0.0   0.0
  3.|-- 198.18.100.11              0.0%     3  134.4 280.6 105.9 601.4 278.2
```

NOTE: Lack of response from hop2 in the above (leaf1) happens with vQFX.  In production on QFX5120 devices this is not observed with the same configuration, a response is generated from the irb.100 unicast address and is received by the server doing the traceroute.
