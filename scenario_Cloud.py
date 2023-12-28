#!/usr/bin/python

"""
create a ContainerNet topology and connect it to the internet via NAT
through and interface on the host.
"""

from mininet.cli import CLI
from mininet.log import lg, info
from mininet.node import Node, Docker
from mininet.util import quietRun
from mininet.node import Controller
import time
from mininet.topo import Topo
#from mininet.node import OVSSwitch
from mininet.net import Containernet
from mininet.log import lg, info
from mininet.link import Link, TCLink
import os
#################################
def startNAT( root, inetIntf='enp0s6f1u4', subnet='10.0/8' ):
    """Start NAT/forwarding between Mininet and external network
    root: node to access iptables from
    inetIntf: interface for internet access
    subnet: Mininet subnet (default 10.0/8)="""

    # Identify the interface connecting to the mininet network
    localIntf =  root.defaultIntf()
    print ("interface is :", localIntf)
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Create default entries for unmatched traffic
    root.cmd( 'iptables -P INPUT ACCEPT' )
    root.cmd( 'iptables -P OUTPUT ACCEPT' )
    root.cmd( 'iptables -P FORWARD DROP' )

    # Configure NAT
    root.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
    root.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )

    # Instruct the kernel to perform forwarding
    #root.cmd( 'sysctl net.ipv4.ip_forward=1' )

def stopNAT( root ):
    """Stop NAT/forwarding between Mininet and external network"""
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Instruct the kernel to stop forwarding
    #root.cmd( 'sysctl net.ipv4.ip_forward=0' )

def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
       by specifying manual configuration in /etc/network/interfaces
       root: a node in the root namespace (for running commands)
       intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if ( line ) not in config:
        print '*** Adding', line.strip(), 'to', cfile
        with open( cfile, 'a' ) as f:
            f.write( line )
    # Probably need to restart network-manager to be safe -
    # hopefully this won't disconnect you
    root.cmd( 'service network-manager restart' )

def connectToInternet( network, switch='s0', rootip='10.254.0.0', subnet='10.0/8'):
    """Connect the network to the internet
       switch: switch to connect to root namespace
       rootip: address for interface in root namespace
       subnet: Mininet subnet"""
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]
    routes = [ subnet ]  # host networks to route to

    # Create a node in root namespace
    root = Node( 'root', inNamespace=False )

    # Prevent network-manager from interfering with our interface
    fixNetworkManager( root, 'enp0s6f1u4')

    # Create link between root NS and switch
    link = network.addLink( root, switch, delay='0ms')
    link.intf1.setIP( rootip, prefixLen )

    # Start network that now includes link to root namespace
    network.start()

    # Start NAT and establish forwarding
    startNAT( root )

    # Establish routes from end hosts
    for host in network.hosts:
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'route add -net', subnet, 'dev', host.defaultIntf() )
        host.cmd( 'route add default gw', rootip )

    return root

if __name__ == '__main__':

    lg.setLogLevel( 'info')

    net = Containernet(controller=Controller)

    info('*** Adding controller\n')
    net.addController('c0')
    #topo = Topo()
    info('*** Adding docker containers\n')
    d1 = net.addDocker("d1", ip="10.0.0.251", dimage="last-lightning-rode:latest", ports=[50001], port_bindings={50001:50001}, publish_all_ports=True)
    d2 = net.addDocker("d2", ip="10.0.0.252", dimage="last-lightning-rode:latest", ports=[50002], port_bindings={50002:50002}, publish_all_ports=True)
    d3 = net.addDocker("d3", ip="10.0.0.253", dimage="last-lightning-rode:latest", ports=[50003], port_bindings={50003:50003}, publish_all_ports=True)
    # d1.sendCmd("export NGINX_VAR=50001")
    info('*** Adding switches\n')
    s0 = net.addSwitch("s0")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")
    #s2 = net.addSwitch("s2")
    info('*** Creating links\n')
    net.addLink(s1, s0, cls=TCLink, delay='0ms')
    net.addLink(s2, s0, cls=TCLink, delay='0ms')
    net.addLink(s3, s0, cls=TCLink, delay='0ms')
    net.addLink(d1, s1,cls=TCLink, delay='30ms', bw=2)
    net.addLink(d2, s2,cls=TCLink, delay='120ms', bw=1)
    net.addLink(d3, s3,cls=TCLink, delay='70ms', bw=4)
    #net = Containernet(topo)
    #net = TreeNet( depth=1, fanout=4 )
    # Configure and start NATted connectivity
    #d1.sendCmd("ifconfig")
    rootnode = connectToInternet( net )
    print "*** Hosts are running and should have internet connectivity"
    print "*** Type 'exit' or control-D to shut down network"
    string1 = "touch "+str(50001)
    os.system("sudo docker exec -it mn.d1 "+string1)
    os.system("sudo docker exec -it mn.d1 ./script_conf.py")
    string2 = "touch "+str(50002)
    os.system("sudo docker exec -it mn.d2 "+string2)
    os.system("sudo docker exec -it mn.d2 ./script_conf.py")
    string3 = "touch "+str(50003)
    os.system("sudo docker exec -it mn.d3 "+string3)
    os.system("sudo docker exec -it mn.d3 ./script_conf.py")
    #d1.sendCmd("touch file")
    #d1.cmd("PORT_p=700")
    CLI( net )
    # Shut down NAT
    stopNAT( rootnode )
    net.stop()
