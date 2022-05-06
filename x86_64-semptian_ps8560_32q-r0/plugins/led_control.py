# led_control.py
#
# Platform-specific LED control functionality for SONiC
#

try:
    from sonic_led.led_control_base import LedControlBase
    import os
    import syslog
    from socket import *
    from select import *
except ImportError as e:
    raise ImportError(str(e) + " - required module not found")


def DBG_PRINT(str):
    syslog.openlog("semptian-led")
    syslog.syslog(syslog.LOG_INFO, str)
    syslog.closelog()


class LedControl(LedControlBase):
    """Platform specific LED control class"""
    
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/39-0011/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/39-0011/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD1_PATH = temp
    DBG_PRINT(" BASE_CPLD1_PATH %s" % BASE_CPLD1_PATH)
    #os.system('cp -rf /usr/share/sonic/platform/plugins/sonic_platform /usr/local/lib/python3.7/dist-packages/')
    
    #os.system('cp -rf /usr/share/sonic/platform/plugins/sonic_platform /usr/local/lib/python2.7/dist-packages/')
    FILE_PATH='/usr/local/lib/python3.7/dist-packages/sonic_platform'
    if os.path.isdir(FILE_PATH):
        print("####sonic_platform is exsit")
    else:
        print("####sonic_platform is not exsit")
        os.system('cp -rf /usr/share/sonic/platform/plugins/sonic_platform /usr/local/lib/python3.7/dist-packages/')
        
    # Helper method to map SONiC port name to index
    def _port_name_to_index(self, port_name):
        # Strip "Ethernet" off port name
        if not port_name.startswith(self.SONIC_PORT_NAME_PREFIX):
            return -1

        port_idx = int(port_name[len(self.SONIC_PORT_NAME_PREFIX):])
        return port_idx

    def _port_state_to_mode(self, port_idx, state):
        if state == "up":
            return self.LED_MODE_UP[0]
        else:
            return self.LED_MODE_DOWN[0]

    def _get_port_led_path(self, port_num):
        port_id = int(port_num/8)
 
        port_cpld_path = self.BASE_CPLD1_PATH + "port" + str(port_id) + "_led" 
        
        #DBG_PRINT("_get_port_led_path port_num{} port_index {} port_cpld_path {}".format(port_num, port_index, port_cpld_path))        
        return port_cpld_path

    def _get_port_present_path(self, port_num):
        port_id = int(port_num / 8)
  
        port_cpld_path = self.BASE_CPLD1_PATH + "port" + str(port_id) + "_present" 

            
        #DBG_PRINT("_get_port_present_path port_num{} port_index {} port_cpld_path {}".format(port_num, port_index, port_cpld_path))    
        return port_cpld_path 
 
    def _port_led_mode_update(self, port_idx, ledMode):
        port_led=self._get_port_led_path(port_idx)

        with open(port_led, 'w') as led_file:
            led_file.write(str(ledMode))

    def _initSystemLed(self):
        return True

    # Concrete implementation of port_link_state_change() method

    def port_link_state_change(self, portname, state):
       

        port_idx = self._port_name_to_index(portname)
        
        #DBG_PRINT("-------portname %s--------port_idx %s-----state :%s----- " % (portname, port_idx, state))
       
        ledMode = self._port_state_to_mode(port_idx, state)

        port_led=self._get_port_led_path(port_idx)
       
        """if state == "up":
            port_to_is_present = self._get_port_present_path(port_idx)
            content = "1"
            try:
                val_file = open(port_to_is_present)
                #fcntl.flock(val_file, fcntl.LOCK_EX)
                content = val_file.readline().rstrip()
                #fcntl.flock(val_file, fcntl.LOCK_UN)  
                val_file.close()
            except IOError as e:
                print("Error: unable to access file: %s" % str(e))
                return False

            #DBG_PRINT("    port_idx:%d------port_sfp_present:%s---------- " % (port_idx, content))  
            if content == "1":
                return""" 


        with open(port_led, 'r') as led_file:
            saveMode = int(led_file.read())

        if ledMode == saveMode:
            return

        self._port_led_mode_update(port_idx, ledMode)
        DBG_PRINT("-------------update {} led mode from {} to {} path {}".format(portname, saveMode, ledMode, port_led))

    # Constructor

    def __init__(self):
        self.SONIC_PORT_NAME_PREFIX = "Ethernet"
        self.LED_MODE_UP = [2]
        self.LED_MODE_DOWN = [1]
        
        
        
        


        