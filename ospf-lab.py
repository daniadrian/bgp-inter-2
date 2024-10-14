#!/usr/bin/env python3

from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import shutil
import time
from pathlib import Path
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.nodelib import LinuxBridge
import argparse

class LinuxRouter( Node ):
	def config( self, **params ):
		super( LinuxRouter, self).config( **params )
		self.cmd( 'sysctl -w net.ipv4.ip_forward=1' )
		self.cmd('/usr/lib/frr/zebra -A 127.0.0.1 -s 90000000 -f /etc/frr/frr.conf -d')
		self.cmd('/usr/lib/frr/staticd -A 127.0.0.1 -f /etc/frr/frr.conf -d')
		self.cmd('/usr/lib/frr/ospfd -A 127.0.0.1 -f /etc/frr/frr.conf -d')
		self.cmd('/usr/lib/frr/bgpd -A 127.0.0.1 -f /etc/frr/frr.conf -d')
		
		# region
		# self.cmd( 'sysctl -w net.ipv6.conf.all.forwarding=1' )
		# self.cmd('/usr/lib/frr/pimd -A 127.0.0.1 -f /etc/frr/frr.conf -d')
		# self.cmd('/usr/lib/frr/pim6d -A ::1 -f /etc/frr/frr.conf -d')
		# self.cmd('/usr/lib/frr/isisd -A 127.0.0.1 -f /etc/frr/frr.conf -d')
		# self.cmd('/usr/lib/frr/ospf6d -A ::1 -f /etc/frr/frr.conf -d')
		# endregion

	def terminate( self ):
		self.cmd( 'killall zebra staticd ospfd ospf6d bgpd pathd pimd pim6d ldpd isisd nhrpd vrrpd fabricd' )
		super( LinuxRouter, self ).terminate()
	
	def start (self):
		return

class OSPFLab(Topo):

	def generate_config(self, router_name, path):
		""" Generate an empty config for each router.\n
			path: the path of router configs directory
		"""
		router = {"name":router_name}
		path = path % router
		#print(path)
		#config template directory path
		template_path = Path("Template/router") 
		Path(path).mkdir(exist_ok=True, parents=True)

		#copy files from the config template folder
		for file in template_path.iterdir():
			shutil.copy(file, path)
		
		#modify hostname
		self.replace_hostname(path+"/frr.conf", "dummy", router_name)
		self.replace_hostname(path+"/vtysh.conf", "dummy", router_name)
		
		self.add_ospf_configuration(path+"/frr.conf", router_name)

		return
	
	def replace_hostname(self, filepath, toReplace, replacement):
		""" Replace hostname in a router config \n
			filepath: path to the config file\n
			toReplace: the hostname to replace\n
			replacement: the new hostname\n
		"""
		with open(filepath, 'r') as f:
			content = f.readlines()
			for linenum in range (len(content)):
				if (content[linenum] == "hostname "+toReplace+"\n"):
					content[linenum] = "hostname "+ replacement+"\n"
		with open(filepath, "w") as f:
			f.writelines(content)
		return	
	
	def parse_argument(self ):
		parser = argparse.ArgumentParser()
		parser.add_argument( "-g","--generateConfig", 
											help="Generate router config files.\n"
											+"This will overwrite existing files",
											action="store_true")
		parser.add_argument("-v", "--verbose", 
											help="Prints detailed logs during network creation and stop",
											action="store_true")
		flags = parser.parse_args()
		return flags
	
	def build(self, *args, **kwargs):
		flags = self.parse_argument()
		if(flags.verbose):
			setLogLevel( 'info' )
		
		# directory to keep the configurations
		config_path = "/home/USER/bgp/bgp-route/inter-domain-routing/frr-config/%(name)s"

		# private directory that will useed by the routers by bind mounting
		privateDirs = [ ( '/var/log' ),
						( '/etc/frr', config_path),
						( '/var/run' ),
						'/var/mn' ]
		
		#  R1 subnet
		C1_1 = self.addHost('C1_1', ip="172.16.1.2/24", defaultRoute="via 172.16.1.1")
		C1_2 = self.addHost('C1_2', ip="172.16.2.2/24", defaultRoute="via 172.16.2.1")
		R1 = self.addNode("R1", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		S1 = self.addSwitch("S1", inNamespace=True)
		R1_1 = self.addNode("R1_1", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		R1_2 = self.addNode("R1_2", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)

		# add links for subnet 1
		self.addLink(S1, R1,  intfName2="R1-eth0") 
		self.addLink(S1, R1_1, intfName2="R1_1-eth0")
		self.addLink(S1, R1_2, intfName2="R1_2-eth0")

		#region
		# Do not manually set the interface name of a switch's interface
		# mininet will not be able to automatically add the interfaces to its bridge
		#endregion

		self.addLink(C1_1,R1_1, intfName2="R1_1-eth1")
		self.addLink(C1_2,R1_2, intfName2="R1_2-eth1")

		# R2 Subnet
		C2_1 = self.addHost('C2_1', ip="172.17.1.2/24", defaultRoute="via 172.17.1.1")
		C2_2 = self.addHost('C2_2', ip="172.17.2.2/24", defaultRoute="via 172.17.2.1")
		R2 = self.addNode("R2", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		S2 = self.addSwitch("S2", inNamespace=True)
		
		R2_1 = self.addNode("R2_1", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		R2_2 = self.addNode("R2_2", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)

		# add links for subnet 2
		self.addLink(S2, R2, intfName2="R2-eth0") 
		self.addLink(S2, R2_1, intfName2="R2_1-eth0")
		self.addLink(S2, R2_2, intfName2="R2_2-eth0")

		self.addLink(C2_1,R2_1, intfName2="R2_1-eth1")
		self.addLink(C2_2,R2_2, intfName2="R2_2-eth1")

		# R3 Subnet
		C3_1 = self.addHost('C3_1', ip="172.18.1.2/24", defaultRoute="via 172.18.1.1")
		C3_2 = self.addHost('C3_2', ip="172.18.2.2/24", defaultRoute="via 172.18.2.1")
		R3 = self.addNode("R3", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		S3 = self.addSwitch("S3", inNamespace=True)
		R3_1 = self.addNode("R3_1", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
		R3_2 = self.addNode("R3_2", cls=LinuxRouter, ip=None, privateDirs=privateDirs, inNamespace=True)
	
		# add links for subnet 3
		self.addLink(S3,R3, intfName2="R3-eth0")
		self.addLink(S3,R3_1, intfName2="R3_1-eth0")
		self.addLink(S3,R3_2, intfName2="R3_2-eth0")

		self.addLink(C3_1,R3_1, intfName2="R3_1-eth1")
		self.addLink(C3_2,R3_2, intfName2="R3_2-eth1")

		# Add links between backbone routers		
		self.addLink(R1,R2, intfName1="R1-eth1", intfName2="R2-eth1")
		self.addLink(R1,R3, intfName1="R1-eth2", intfName2="R3-eth1")
		self.addLink(R2,R3, intfName1="R2-eth2", intfName2="R3-eth2")

		confdir = Path(config_path % {"name": ""})
		if (not flags.generateConfig):
			if (not Path.exists(confdir)):
				# Automatically set to generate config files if config Path doesn't exists, such as when first time running the program
				print("If this is your first time running the program, ")
				print("consider running the program with \"-h\" to see the options")
				print("="*40)
				flags.generateConfig=True
				
		if (flags.generateConfig):
			# Configuration files will be created for each routers
			for n in self.nodes():
				print(n)
				if "cls" in self.nodeInfo(n):
					node_info = self.nodeInfo(n)
					if node_info["cls"].__name__ == "LinuxRouter":
						self.generate_config(n, config_path)
						pass

		super().build(*args, **kwargs)


start = time.time()
print("This the topology for the OSPF lab")
print("="*40)
net = Mininet(topo=OSPFLab(), switch=LinuxBridge, controller=None)
finish = time.time()
print("Finished initializing network in:", finish-start, "seconds")

try:
	pass
	net.start()
	CLI(net)
	
finally:
	start = time.time()
	net.stop()
	finish = time.time()
	print("Finished stopping network in:", finish-start, "seconds")
