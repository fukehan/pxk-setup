#!/usr/bin/python
#encoding: utf-8
import os
import requests
import json
from subprocess import Popen, PIPE
from time import sleep

def getIP():
    p = Popen(['ifconfig'], stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    data = [i for i in stdout.split('\n') if i]
    return data

def genIP(data):
    new_line = ''
    lines = []
    for line in data:
        if line[0].strip():
            lines.append(new_line)
            new_line = line + '\n'
        else:
            new_line += line + '\n'
    lines.append(new_line)
    return [i for i in lines if i and not i.startswith('lo')]

def parseIP(data):
    ethArry = []
    for devs in data:
        lines = devs.split('\n')
        print lines[0]
        if 'RUNNING' in lines[0]:
            if 'inet 192.168.100' in lines[1]:
                devname = lines[0].split()[0]
                #macaddr = lines[3].split()[1]
                ethArry.append(devname.strip(':'))
    return ethArry

def getMac(data):
    mac = []
    macaddr = ''
    for devs in data:
        lines = devs.split('\n')
        for line in lines:
            if 'ether' in line:
                macaddr = line.split()[1]
        if 'RUNNING' in lines[0]:
            if 'inet 192.168.100' in lines[1]:
                mac.append(macaddr)
    return mac

def getPxkStatus():
    url = "http://192.168.100.20:5050/pxk/api/v1.0/online"
    r = requests.get(url)
    print r.json()

def setup_dhcp(ip,mac):
    url = "http://192.168.100.20:5050/pxk/setup_dhcp"
    data = {'id':'1','ip':str(ip), 'mac':mac}
    r = requests.post(url, data)
    print r.text

if __name__ == '__main__':
    data = getIP()
    nics = genIP(data)
    ethArry = parseIP(nics)
    print ethArry
    mac = getMac(nics)
    print mac
    #getPxkStatus()
    #setup_dhcp()
    #step 1: down all eth*
    for eth in ethArry:
        os.environ['eth'] = eth
        os.system('ifconfig $eth down')

    #step 1, up on by on, and post to nxp
    ip = 100
    ethmap = {}
    i = 0;
    for eth in ethArry:
        print eth
        print ip
        print mac[i]
        os.environ['eth'] = eth
        os.system('ifconfig $eth up')
        os.system('ifconfig $eth 192.168.100.200')
        sleep(10)
        setup_dhcp(ip, mac[i])
        os.system('ifconfig $eth down')
        ethmap[eth] = ip
        ip = ip + 1
        i = i + 1

    for ethname in ethmap:
        print("ifconfig up " + ethname + str(ethmap[ethname]))
        os.environ['eth'] = ethname
        os.environ['ip'] = str(ethmap[ethname])
        os.system('ifconfig $eth up')
        os.system('ifconfig $eth 192.168.$ip.200')

        ## neet wait some time
