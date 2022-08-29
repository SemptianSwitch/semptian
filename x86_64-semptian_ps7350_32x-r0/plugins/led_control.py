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

    #FILE_PATH='/usr/local/lib/python3.7/dist-packages/sonic_platform'
    #if os.path.isdir(FILE_PATH):
        #print("####python3.7 sonic_platform is exsit")
    #else:
        #print("####python3.7 sonic_platform is not exsit")
        #os.system('cp -rf /usr/share/sonic/platform/plugins/sonic_platform /usr/local/lib/python3.7/dist-packages/')

    #FILE_PATH='/usr/local/lib/python2.7/dist-packages/sonic_platform'
    #if os.path.isdir(FILE_PATH):
        #print("####python2.7 sonic_platform is exsit")
    #else:
        #print("####python2.7 sonic_platform is not exsit")
        #os.system('cp -rf /usr/share/sonic/platform/plugins/sonic_platform /usr/local/lib/python2.7/dist-packages/')
        
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

    def _port_led_mode_update(self, port_idx, ledMode):
        port_led=self.f_led  + "port" + str(port_idx) + "_led"

        with open(port_led, 'w') as led_file:
            led_file.write(str(ledMode))

    def _initSystemLed(self):
        try:
            with open(self.f_led.format("system"), 'w') as led_file:
                led_file.write("1")
            DBG_PRINT("init system led to normal")
            with open(self.f_led.format("idn"), 'w') as led_file:
                led_file.write("1")
            DBG_PRINT("init idn led to off")
        except IOError as e:
            DBG_PRINT(str(e))

    # Concrete implementation of port_link_state_change() method

    def port_link_state_change(self, portname, state):
       

        port_idx = self._port_name_to_index(portname)
        
        port_idx=port_idx/4
        ledMode = self._port_state_to_mode(port_idx, state)


        port_led=self.f_led  + "port" + str(port_idx) + "_led"
        #print("DDDDDDD------- port_idx:%s portname:%s state:%s------------------ " % (port_idx, portname, state))
        
        if state == "up":
            port_to_is_present =self.f_led  + "port" + str(port_idx) + "_present"
            content = "1"
            try:
                val_file = open(port_to_is_present)
                content = val_file.readline().rstrip()
                val_file.close()
            except IOError as e:
                print("Error: unable to access file: %s" % str(e))
                return False

            if content == "1":
                return 


        with open(port_led, 'r') as led_file:
            #saveMode = self._port_state_to_mode(port_idx, led_file.read())
            saveMode = led_file.read()

        #print("DDDDDDD------- port_idx:%s portname:%s state:%s saveMode:%s ledMode:%s------------------ " % (port_idx, portname, state, saveMode, ledMode))
        if ledMode == saveMode:
            return

        self._port_led_mode_update(port_idx, ledMode)
        DBG_PRINT("update {} led mode from {} to {}".format(portname, saveMode, ledMode))
        #print("update {} led mode from {} to {}".format(portname, saveMode, ledMode))

    # Constructor

    def __init__(self):
        self.SONIC_PORT_NAME_PREFIX = "Ethernet"
        self.LED_MODE_UP = [2]
        self.LED_MODE_DOWN = [0]
        
        import os

        sysfs = "cat "
        sysfs = sysfs + '/sys/class/hwmon/hwmon{0}/name'
        offset = 3
        cpld_name = 'xc3400an_port_cpld'
        for index in range(0, 10):
            cmd=sysfs.format(index)
            ret = os.popen(cmd)
            adaptername=ret.read()
            
            print("cmd:%s  adaptername:%s" % (cmd, adaptername))
            
            if adaptername.find(cpld_name) >= 0:
                ret.close()
                offset = index
                print("get:%s  adaptername:%s" % (cmd, adaptername))
                break
            else:
                ret.close() 
            
        path = '/sys/class/hwmon/hwmon{0}/'
        BASE_CPLD1_PATH = path.format(index)
        self.f_led = BASE_CPLD1_PATH
