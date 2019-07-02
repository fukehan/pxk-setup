#!/usr/bin/python
#encoding: utf-8
import os
import sys
import requests
import json
import urllib2
from subprocess import Popen, PIPE
from time import sleep
from collections import Counter

ip_support = ['100', '101', '102', '103', '104', '105','106', '107', '108','109', '110', '111', '112', '113', '114', '115']

def get_ifconfig_stream():
    p = Popen(['ifconfig'], stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    data = [i for i in stdout.split('\n') if i]
    return data

def split_ip_stream(data):
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

def get_pxk_interface(data):
    ethArry = {}
    for devs in data:
        lines = devs.split('\n')
        if 'RUNNING' in lines[0]:
            devname = (lines[0].split()[0]).strip(':')
            macaddr = lines[3].split()[1]
            ipaddr  = lines[1].split()[1]
            if 'inet 192.168.100' in lines[1]:
                ethArry[devname] = [ipaddr, macaddr]
            elif is_pxk_running(ipaddr) != -1 :
                ethArry[devname] = [ipaddr, macaddr]
    return ethArry

def get_all_running_interface(data):
    interface = {}
    for devs in data:
        lines = devs.split('\n')
        if 'RUNNING' in lines[0]:
            devname = (lines[0].split()[0]).strip(':')
            macaddr = lines[3].split()[1]
            ipaddr  = lines[1].split()[1]
            interface[devname] = [ipaddr, macaddr]
    return interface

def get_all_running_ip(data):
    interface = {}
    for devs in data:
        lines = devs.split('\n')
        if 'RUNNING' in lines[0]:
            devname = (lines[0].split()[0]).strip(':')
            #macaddr = lines[3].split()[1]
            ipaddr  = lines[1].split()[1]
            interface[devname] = ipaddr
    return interface

def get_all_running_mac(data):
    interface = {}
    for devs in data:
        lines = devs.split('\n')
        if 'RUNNING' in lines[0]:
            devname = (lines[0].split()[0]).strip(':')
            macaddr = lines[3].split()[1]
            #ipaddr  = lines[1].split()[1]
            interface[devname] = macaddr
    return interface

def is_pxk_running(ip):
    if '192.168.' not in ip:
        return -1
    try:
        ipsplit = ip.split('.')
        mcu_ip = ipsplit[0] + '.' + ipsplit[1] + '.' + ipsplit[2] + '.' + '20'
        url = 'http://' + mcu_ip + ':5050/pxk/info/all'
        print("url = ",url)
        status = urllib2.urlopen(url, timeout=10).code
        print("run status = ", status)
        return status
    except:
        print("run status = -1")
        return -1

def parseIP(data):
    ethArry = {}
    for devs in data:
        lines = devs.split('\n')
        if 'RUNNING' in lines[0]:
            if 'inet 192.168.100' in lines[1]:
                devname = (lines[0].split()[0]).strip(':')
                macaddr = lines[3].split()[1]
                ipaddr  = lines[1].split()[1]
                ethArry[devname] = [ipaddr, macaddr]
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

def setup_dhcp(ipaddr, ip, mac):
    ipsplit = ipaddr.split('.')
    mcu_ip = ipsplit[0] + '.' + ipsplit[1] + '.' + ipsplit[2] + '.' + '20'
    print ("mcu_ip", mcu_ip)
    url = 'http://' + mcu_ip + ':5050/pxk/setup_dhcp'
    data = {'id':'1','ip':str(ip), 'mac':mac}
    r = requests.post(url, data)
    print r.text

def setup_dhcp_init(ip,mac):
    url = "http://192.168.100.20:5050/pxk/setup_dhcp"
    data = {'id':'1','ip':str(ip), 'mac':mac}
    r = requests.post(url, data)
    print r.text

def down_interface(etharry):
    for eth in etharry:
        os.environ['eth'] = eth
        os.system('ifconfig $eth down')

def setup_first():
    stream = get_ifconfig_stream()
    split_stream = split_ip_stream(stream)
    ethArry = parseIP(split_stream)

    down_interface(ethArry)

    #step 1, up and post to nxp
    ip = 100
    ethmap = {}
    retrylist = {}
    for eth in ethArry:
        print ("setup-first-eth",eth)
        os.environ['eth'] = eth
        os.system('ifconfig $eth up')
        os.system('ifconfig $eth 192.168.100.200')
        sleep(25)
        try:
            setup_dhcp_init(ip, ethArry[eth][1])
            ethmap[eth] = ip
        except:
            print("reytry setup" + eth + "!!!!")
            retrylist[eth] = [ip, ethArry[eth][1]]
        ip = ip + 1
        down_interface(ethArry)

    if len(retrylist) > 0:
        for retry_item in retrylist:
            os.environ['eth'] = retry_item
            os.system('ifconfig $eth up')
            os.system('ifconfig $eth 192.168.100.200')
            sleep(25)
            setup_dhcp_init(retrylist[retry_item][0], retrylist[retry_item][1])
            ethmap[retry_item] = retrylist[retry_item][0]
            os.system('ifconfig $eth down')

    for ethname in ethmap:
        print("ifconfig up " + ethname + str(ethmap[ethname]))
        os.environ['eth'] = ethname
        os.environ['ip'] = str(ethmap[ethname])
        os.system('ifconfig $eth up')
        os.system('ifconfig $eth 192.168.$ip.200')
        sleep(10)

    sleep(10)
    pxk_save_running()

def pxk_save_running():
    stream = get_ifconfig_stream()
    split_stream = split_ip_stream(stream)
    running_interface = get_all_running_interface(split_stream)
    pxkinfo = []
    for interface in running_interface:
        if is_pxk_running(running_interface[interface][0]) != -1:
            info = {
                "interface": interface,
                "ip": running_interface[interface][0],
                "mac": running_interface[interface][1],
            }
            pxkinfo.append(info)
            with open("pxkinfo.json","w") as f:
                json.dump(pxkinfo,f,indent=4, sort_keys=True)

if __name__ == '__main__':
    is_first_setup = 0
    is_setup_done = 1
    stream = get_ifconfig_stream()
    split_stream = split_ip_stream(stream)
    all_running_mac = get_all_running_mac(split_stream)
    all_running = get_all_running_ip(split_stream)

    filter_face = []
    for runface in all_running:
        ipaddress = all_running[runface]
        print("runface---ip----",ipaddress)
        if '192.168' not in ipaddress:
            filter_face.append(runface)
        else:
            if ipaddress.split('.')[2] not in ip_support:
                if is_pxk_running(ipaddress) == -1:
                    filter_face.append(runface)

    print("filter_face---",filter_face)
    if len(filter_face) > 0:
        for face in filter_face:
            print("del_face---",face)
            del all_running[face]
            del all_running_mac[face]

    all_running_bak = all_running.copy()
    work_interface_pre = all_running.copy()

    filterindex = 0
    for key in all_running:
        value = all_running[key]
        if is_pxk_running(value) == -1:
            is_setup_done = 0

    print("is_setup_done", is_setup_done)

    work_interface = {}
    for interface in all_running:
        print ("interface-",interface)
        tm_ip = all_running[interface]
        print tm_ip
        if '192.168' in tm_ip:
            tmpsplist = all_running[interface].split('.')
            work_interface[interface] = tmpsplist[0] + '.' + tmpsplist[1] + '.' + tmpsplist[2]
    #print work_interface

    rev_all_running = {}
    for key, value in work_interface.items():
        rev_all_running.setdefault(value, set()).add(key)

    group_repeat = []
    for key, value in rev_all_running.items():
        if len(value) > 1:
            group_repeat.append(list(value))

    print ("group_repeat",group_repeat)
    if is_setup_done == 1 and len(group_repeat) == 0:
        print("pxk mybe is setup done, pls check by manual !")
        sys.exit()

    if len(group_repeat) == 1:
        for item in group_repeat:
            for index in range(len(item)):
                ipaddr = work_interface[item[index]].split('.')[2]
                if ipaddr == '100':
                    print ("del -------", item[index])
                    del work_interface_pre[item[index]]
                    is_first_setup = 1

    if is_first_setup == 1:
        for face in work_interface_pre:
            if is_pxk_running(work_interface_pre[face]) != -1:
                is_first_setup = 0
                break

    print ("is_first_setup",is_first_setup)
    if is_first_setup == 1:
        setup_first()
    elif is_first_setup == 0:
        group = {}
        repeat_interface = []
        for item in group_repeat:
            for index in range(len(item)):
                repeat_interface.append(item[index])
        print ("repeat_interface ",  repeat_interface)

        for interface in repeat_interface:
            del all_running[interface]
        print ("----current all_running------", all_running)

        no_runface = []
        for interface in all_running:
            if is_pxk_running(all_running[interface]) == -1:
                no_runface.append(interface)
        for interface in no_runface:
            del all_running[interface]
        print ("******current all_running*****", all_running)
        print ("len all_running" , len(all_running))

        if len(all_running) == 0:
            myip = 100
            ethmap = {}
            i = 0;
            down_interface(repeat_interface)
            for interface in repeat_interface:
                ipaddr = all_running_bak[interface]
                print ("ipaddr" , ipaddr)

                os.environ['eth'] = interface
                os.environ['ip'] = ipaddr
                os.system('ifconfig $eth up')
                os.system('ifconfig $eth $ip')
                sleep(25)
                try :
                    setup_dhcp(ipaddr, myip, all_running_mac[interface][1])
                    #setup_dhcp(ipaddr, myip, '09.08.01.02.03.04')
                    ethmap[interface] = myip
                    myip = myip + 1
                    i = i + 1;
                    print "-----setup dhcp " + interface  + " OKKK !!  "
                except:
                    print "-----setup dhcp " + interface  + " error !!  "
                down_interface(repeat_interface)
            for ethname in ethmap:
                print("ifconfig up " + ethname + str(ethmap[ethname]))
                os.environ['eth'] = ethname
                os.environ['ip'] = str(ethmap[ethname])
                os.system('ifconfig $eth up')
                os.system('ifconfig $eth 192.168.$ip.200')
                sleep(10)
        else :
            myip = 150
            ethmap = {}
            i = 0;
            down_interface(repeat_interface)
            for interface in repeat_interface:
                ipaddr = all_running_bak[interface]
                os.environ['eth'] = interface
                os.environ['ip'] = ipaddr
                os.system('ifconfig $eth up')
                os.system('ifconfig $eth $ip')
                sleep(25)
                try :
                    setup_dhcp(ipaddr, myip, all_running_mac[interface][1])
                    ethmap[interface] = myip
                    myip = myip + 1
                    i = i + 1;
                    print "-----setup dhcp " + interface  + " OKKK !!  "
                except:
                    print "-----setup dhcp " + interface  + " error !!  "
                down_interface(repeat_interface)

            for ethname in ethmap:
                print("ifconfig up " + ethname + str(ethmap[ethname]))
                os.environ['eth'] = ethname
                os.environ['ip'] = str(ethmap[ethname])
                os.system('ifconfig $eth up')
                os.system('ifconfig $eth 192.168.$ip.200')
                sleep(30)
            ## sort all map:
            pre_sort_stream = get_ifconfig_stream()
            pre_sort_split_stream = split_ip_stream(pre_sort_stream)
            pre_sort_interface = get_all_running_interface(pre_sort_split_stream)

            invalid_face = []
            for face in pre_sort_interface:
                value = pre_sort_interface[face][0]
                if '192.168' not in value or is_pxk_running(value) == -1:
                    invalid_face.append(face)

            for item in invalid_face:
                del pre_sort_interface[face]

            need_insert_ip = []
            ip_map = []
            need_sort_interface = []
            for interface in pre_sort_interface:
                ip_addr = pre_sort_interface[interface][0].split('.')[2]
                ip_map.append(ip_addr)
                print ("ip_addr = " + ip_addr)
                if ip_addr not in ip_support:
                    need_sort_interface.append(interface)

            for item in ip_support:
                if item not in ip_map:
                    need_insert_ip.append(item)

            print ("need_sort_interface :" , need_sort_interface)
            print ("need_insert_ip :" , need_insert_ip)

            index = 0
            for insert_face in need_sort_interface:
                ipaddr = pre_sort_interface[insert_face][0]
                try :
                    os.environ['eth'] = insert_face
                    os.environ['ip'] = need_insert_ip[index]
                    setup_dhcp(ipaddr, need_insert_ip[index], pre_sort_interface[interface][1])
                    index = index + 1
                    os.system('ifconfig $eth down')
                    os.system('ifconfig $eth up')
                    os.system('ifconfig $eth 192.168.$ip.200')
                    sleep(20)
                    print "********setup dhcp " + interface  + " OKKK !!  "
                except:
                    print "***********setup dhcp " + interface  + " error !!  "
            sleep(20)
            pxk_save_running()
