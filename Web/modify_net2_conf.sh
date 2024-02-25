#!/bin/bash

# Check if correct number of arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <ip_address> <netmask> <gateway>"
    exit 1
fi

# Define parameters
ip_address=$1
netmask=$2
gateway=$3

# Modify /etc/net2.conf file
echo "METHOD=STATIC" > /etc/net2.conf
echo "IPADDR=$ip_address" >> /etc/net2.conf
echo "NETMASK=$netmask" >> /etc/net2.conf
echo "GATEWAY=$gateway" >> /etc/net2.conf

# Restart system
echo "Restarting system..."
reboot

