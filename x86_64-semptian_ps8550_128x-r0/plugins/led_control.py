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
    cmd = cmd + '/sys/bus/i2c/devices/7-0010/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/7-0010/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD1_PATH = temp
    DBG_PRINT(" BASE_CPLD1_PATH %s" % BASE_CPLD1_PATH)
    
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/8-0011/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/8-0011/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD2_PATH = temp
    DBG_PRINT(" BASE_CPLD2_PATH %s" % BASE_CPLD2_PATH)
 
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/9-0012/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/9-0012/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD3_PATH = temp
    DBG_PRINT(" BASE_CPLD3_PATH %s" % BASE_CPLD3_PATH)
 
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/10-0013/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/10-0013/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD4_PATH = temp
    DBG_PRINT(" BASE_CPLD4_PATH %s" % BASE_CPLD4_PATH)
  
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/11-0014/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/11-0014/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD5_PATH = temp
    DBG_PRINT(" BASE_CPLD5_PATH %s" % BASE_CPLD5_PATH)
 
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/12-0015/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/12-0015/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD6_PATH = temp
    DBG_PRINT(" BASE_CPLD6_PATH %s" % BASE_CPLD6_PATH)

    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/13-0016/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/13-0016/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD7_PATH = temp
    DBG_PRINT(" BASE_CPLD7_PATH %s" % BASE_CPLD7_PATH)
  
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/14-0017/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/14-0017/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD8_PATH = temp
    DBG_PRINT(" BASE_CPLD8_PATH %s" % BASE_CPLD8_PATH)

    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/15-0019/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/15-0019/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_MB1CPLD_PATH = temp
    DBG_PRINT(" BASE_MB1CPLD_PATH %s" % BASE_MB1CPLD_PATH)
    
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
        port_index = port_num / 2
        port_id = port_index%16
        if port_num >= 0 and port_num < 32:
            port_cpld_path = self.BASE_CPLD1_PATH + "port" + str(port_id) + "_led" 
        elif port_num >= 32 and port_num < 64:
            port_cpld_path = self.BASE_CPLD2_PATH + "port" + str(port_id) + "_led" 
        elif port_num >= 64 and port_num < 96:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_led" 
        elif port_num >= 96 and port_num < 128:
            port_cpld_path = self.BASE_CPLD4_PATH + "port" + str(port_id) + "_led" 
        elif port_num >= 128 and port_num < 160:
            port_cpld_path = self.BASE_CPLD5_PATH + "port" + str(port_id) + "_led"
        elif port_num >= 160 and port_num < 192:
            port_cpld_path = self.BASE_CPLD6_PATH + "port" + str(port_id) + "_led" 
        elif port_num >= 192 and port_num < 224:
            port_cpld_path = self.BASE_CPLD7_PATH + "port" + str(port_id) + "_led"  
        elif port_num >= 224 and port_num < 256:
            port_cpld_path = self.BASE_CPLD8_PATH + "port" + str(port_id) + "_led" 
        
        #DBG_PRINT("_get_port_led_path port_num{} port_index {} port_cpld_path {}".format(port_num, port_index, port_cpld_path))        
        return port_cpld_path

    def _get_pim_present_path(self, port_num):
        if port_num >= 0 and port_num < 32:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim0_present" 
        elif port_num >= 32 and port_num < 64:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim1_present" 
        elif port_num >= 64 and port_num < 96:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim2_present" 
        elif port_num >= 96 and port_num < 128:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim3_present" 
        elif port_num >= 128 and port_num < 160:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim4_present"
        elif port_num >= 160 and port_num < 192:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim5_present" 
        elif port_num >= 192 and port_num < 224:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim6_present"  
        elif port_num >= 224 and port_num < 256:
            port_cpld_path = self.BASE_MB1CPLD_PATH + "pim7_present" 
            
        #DBG_PRINT("_get_pim_present_path port_num{} port_cpld_path {}".format(port_num, port_cpld_path))    
        return port_cpld_path

    def _get_port_present_path(self, port_num):
        port_index = port_num / 2
        port_id = port_index%16
        if port_num >= 0 and port_num < 32:
            port_cpld_path = self.BASE_CPLD1_PATH + "port" + str(port_id) + "_present" 
        elif port_num >= 32 and port_num < 64:
            port_cpld_path = self.BASE_CPLD2_PATH + "port" + str(port_id) + "_present" 
        elif port_num >= 64 and port_num < 96:
            port_cpld_path = self.BASE_CPLD2_PATH + "port" + str(port_id) + "_present" 
        elif port_num >= 96 and port_num < 128:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_present" 
        elif port_num >= 128 and port_num < 160:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_present"
        elif port_num >= 160 and port_num < 192:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_present" 
        elif port_num >= 192 and port_num < 224:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_present"  
        elif port_num >= 224 and port_num < 256:
            port_cpld_path = self.BASE_CPLD3_PATH + "port" + str(port_id) + "_present" 
            
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
        
        pim_to_is_present = self._get_pim_present_path(port_idx)
        try:
            pim_file = open(pim_to_is_present)
            #fcntl.flock(pim_file, fcntl.LOCK_EX)
            pim_present = pim_file.readline().rstrip()
            #fcntl.flock(pim_file, fcntl.LOCK_UN)   
            pim_file.close()
        except IOError as e:
            print("Error: unable to access file: %s" % str(e))
            return False
        
        #DBG_PRINT("    port_idx:%d       pim_present:%s" % (port_idx, pim_present))   
        
        if pim_present == "1":
            return 
       
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
        
        
        
        


        