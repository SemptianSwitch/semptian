#!/usr/bin/env python
# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation

# Script that runs cmdline_test app and feeds keystrokes into it.
from __future__ import print_function
import time
import os
import threading

LED_OFF = 1
LED_ON = 2
LED_FLICKER = 3

port_status = []#0:down  1:up
port_rx = []
port_tx = []
led_status = []#LED_OFF, LED_ON, LED_FLICKER

def port_led_set(pst,val):
    ret = False
    if os.system("echo "+str(val)+" > /sys/bus/i2c/devices/5-0011/hwmon/hwmon1/port"+str(pst)+"_led") == 0:
        if os.popen("cat /sys/bus/i2c/devices/5-0011/hwmon/hwmon1/port"+str(pst)+"_led").read().split("\n")[0] == str(val):
            ret = True
    return ret

def flows_change_ckeck(pst,rx,tx):
    if port_status[pst] == 0:
        if led_status[pst] != LED_OFF:
            led_status[pst] = LED_OFF
            port_led_set(pst,LED_OFF)
    elif port_rx[pst] != rx and port_tx[pst] != tx:
        if led_status[pst] != LED_FLICKER:
            led_status[pst] = LED_FLICKER
            port_led_set(pst,LED_FLICKER)
    else:
        if led_status[pst] != LED_ON:
            led_status[pst] = LED_ON
            port_led_set(pst,LED_ON)
            
    port_rx[pst] = rx
    port_tx[pst] = tx
        

def port_check():
    pst = 0
    port_st_array = os.popen("show interfaces status").read().split("\n")
    for i in range(0,len(port_st_array)):
        if "Ethernet" in port_st_array[i]:
            for j in range(pst,len(port_st_array)):
                if "Ethernet"+str(j*4)+" " in port_st_array[i]:
                    if "up" in port_st_array[i].split()[7]:
                        port_status[j] = 1
                    elif "down" in port_st_array[i].split()[7]:
                        port_status[j] = 0
                    pst = j + 1
                    break
    
    pst = 0
    port_flows_array = os.popen("show interfaces counters").read().split("\n")
    for i in range(0,len(port_flows_array)):
        if "Ethernet" in port_flows_array[i]:
            for j in range(pst,len(port_st_array)):
                if "Ethernet"+str(j*4)+" " in port_flows_array[i]:
                    rx_temp = int(port_flows_array[i].split("/")[0].split()[-2])
                    tx_temp = int(port_flows_array[i].split("/")[2].split()[-2])
                    flows_change_ckeck(j,rx_temp,tx_temp)
                    pst = j + 1
                    break
            
def led_polling(address):
    if os.system("sudo chmod 777 /sys/bus/i2c/devices/5-0011/hwmon/hwmon1/port*_led") != 0:
        print("port_led ctrl failed")
        return 1
    
    for i in range(0,256):
        port_status.append(0)
        port_rx.append(0)
        port_tx.append(0)
        led_status.append(0)
        
    while True:
        #threading.Lock().acquire() 
        port_check()
        #threading.Lock().release()
        time.sleep(1)
        
################start################
led_thread = threading.Thread(target=led_polling,name='port_led_polling',args=('add_ress',))
 
led_thread.start()
