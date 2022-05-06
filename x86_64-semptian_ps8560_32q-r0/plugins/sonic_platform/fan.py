#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

from __future__ import division
import math
import os.path

try:
    from sonic_platform_base.fan_base import FanBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

EMC2305_PATH = "/sys/bus/i2c/drivers/emc2305/"
GPIO_DIR = "/sys/class/gpio"
GPIO_LABEL = "pca9505"
EMC2305_MAX_PWM = 255
EMC2305_FAN_PWM = "pwm{}"
EMC2305_FAN_TARGET = "fan{}_target"
EMC2305_FAN_INPUT = "pwm{}"
FAN_NAME_LIST = ["FAN-1F", "FAN-1R", "FAN-2F", "FAN-2R",
                 "FAN-3F", "FAN-3R", "FAN-4F", "FAN-4R", "FAN-5F", "FAN-5R"]
FAN_SPEED_TOLERANCE = 10
PSU_FAN_MAX_RPM = 11000
PSU_HWMON_PATH = "/sys/bus/i2c/devices/i2c-{0}/{0}-00{1}/hwmon"
PSU_I2C_MAPPING = {
    0: {
        "num": 10,
        "addr": "5a"
    },
    1: {
        "num": 11,
        "addr": "5b"
    },
}
NULL_VAL = "N/A"


class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0, is_psu_fan=False, psu_index=0):
        FanBase.__init__(self)
        self.fan_index = fan_index
        self._api_helper = APIHelper()
        self.fan_tray_index = fan_tray_index
        self.is_psu_fan = is_psu_fan
        if self.is_psu_fan:
            self.psu_index = psu_index
            self.psu_i2c_num = PSU_I2C_MAPPING[self.psu_index]["num"]
            self.psu_i2c_addr = PSU_I2C_MAPPING[self.psu_index]["addr"]
            self.psu_hwmon_path = PSU_HWMON_PATH.format(
                self.psu_i2c_num, self.psu_i2c_addr)


    def __write_txt_file(self, file_path, value):
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(value))
        except Exception:
            return False
        return True

    def __search_file_by_name(self, directory, file_name):
        for dirpath, dirnames, files in os.walk(directory):
            for name in files:
                file_path = os.path.join(dirpath, name)
                if name in file_name:
                    return file_path
        return None
        
    def __get_bmc(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sdr')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Psu get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### sensor:%s" % sensor[1])
                if sensor[1].find("disable") >= 0:
                    bmc_pipe.close()
                    return 0
                else:
                    data = sensor[1].split( )
                    #print("### data:%s" % data[0]) 
                    bmc_pipe.close()
                    return int(data[0])                
        
        bmc_pipe.close()
        
        return 0 
        
    def __get_bmc_presence(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sdr')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Psu get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### __get_bmc_presence sensor[1]:%s" % sensor[1])
                if sensor[1].find("disable") >= 0:
                    #print("### find disable") 
                    bmc_pipe.close()
                    return False  
                else:
                    #print("### not find disable") 
                    bmc_pipe.close()
                    return True                
        
        bmc_pipe.close()
        
        return True 

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        #print("fan get_direction fan_tray_index:%s fan_index:%s" % (self.fan_tray_index, self.fan_index))
        if self.is_psu_fan:
            direction = self.FAN_DIRECTION_EXHAUST
            return direction
            
            
        if self.fan_index == 0: 
            direction = self.FAN_DIRECTION_INTAKE
        else:
            direction = self.FAN_DIRECTION_EXHAUST

        return direction

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            speed = pwm_in/255*100
        """
        tmp = 0
        if self.is_psu_fan:
            if self.psu_index == 0:
                tmp = self.__get_bmc("pwr0.fan.rpm")
            else:
                tmp = self.__get_bmc("pwr1.fan.rpm")
            
            #print("fan get_speed psu_index:%s rpm:%s" % (self.psu_index, tmp))            
            speed=40
            return int(speed)        
            
            
        if self.fan_tray_index == 0:    
            if self.fan_index == 0:
                #in.fan0.rpm
                tmp = self.__get_bmc("fan0.level")
            else:
                #out.fan0.rpm
                tmp = self.__get_bmc("fan0.level")      
        elif self.fan_tray_index == 1:
            if self.fan_index == 0:
                #in.fan1.rpm
                tmp = self.__get_bmc("fan1.level")
            else:
                #out.fan1.rpm
                tmp = self.__get_bmc("fan1.level")  
        elif self.fan_tray_index == 2:
            if self.fan_index == 0:
                #in.fan2.rpm
                tmp = self.__get_bmc("fan2.level")
            else:
                #out.fan2.rpm
                tmp = self.__get_bmc("fan2.level") 
        elif self.fan_tray_index == 3:
            if self.fan_index == 0:
                #in.fan3.rpm
                tmp = self.__get_bmc("fan3.level")
            else:
                #out.fan3.rpm
                tmp = self.__get_bmc("fan3.level")                 
        else: 
            print("unkown fan_tray_index[%s] for get_speed" % self.fan_tray_index)    
      
        #print("fan get_speed fan_tray_index:%s fan_index:%s" % (self.fan_tray_index, self.fan_index))
        speed=tmp
        return int(speed)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            speed_pc = pwm_target/255*100

            0   : when PWM mode is use
            pwm : when pwm mode is not use
        """
        tmp = 0
        if self.is_psu_fan:
            if self.psu_index == 0:
                tmp = self.__get_bmc("pwr0.fan.rpm")
            else:
                tmp = self.__get_bmc("pwr1.fan.rpm")
            
            #print("fan get_speed psu_index:%s rpm:%s" % (self.psu_index, tmp))            
            speed=40
            return int(speed)        
            
            
        if self.fan_tray_index == 0:    
            if self.fan_index == 0:
                #in.fan0.rpm
                tmp = self.__get_bmc("fan0.level")
            else:
                #out.fan0.rpm
                tmp = self.__get_bmc("fan0.level")      
        elif self.fan_tray_index == 1:
            if self.fan_index == 0:
                #in.fan1.rpm
                tmp = self.__get_bmc("fan1.level")
            else:
                #out.fan1.rpm
                tmp = self.__get_bmc("fan1.level")  
        elif self.fan_tray_index == 2:
            if self.fan_index == 0:
                #in.fan2.rpm
                tmp = self.__get_bmc("fan2.level")
            else:
                #out.fan2.rpm
                tmp = self.__get_bmc("fan2.level") 
        elif self.fan_tray_index == 3:
            if self.fan_index == 0:
                #in.fan3.rpm
                tmp = self.__get_bmc("fan3.level")
            else:
                #out.fan3.rpm
                tmp = self.__get_bmc("fan3.level")                 
        else: 
            print("unkown fan_tray_index[%s] for get_speed" % self.fan_tray_index)    
      
        #print("fan get_speed fan_tray_index:%s fan_index:%s" % (self.fan_tray_index, self.fan_index))
        speed=tmp
        return int(speed)

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        return False #Not supported

    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not
        """

        return False

    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if status LED state is set successfully, False if not
        """

        return False #Not supported


    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """

        return False

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        #print("fan get_name fan_tray_index:%s fan_index:%s" % (self.fan_tray_index, self.fan_index))
        fan_name = FAN_NAME_LIST[self.fan_tray_index*2 + self.fan_index] \
            if not self.is_psu_fan \
            else "PSU-{} FAN-{}".format(self.psu_index+1, self.fan_index+1)

        return fan_name

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        #print("fan get_presence is_psu_fan:%s fan_tray_index:%s" % (self.is_psu_fan, self.fan_tray_index))
        
        presence = 0  
        tmp = 0
        if self.is_psu_fan:
            if self.psu_index == 0:
                presence = self.__get_bmc_presence("pwr0.fan.rpm")
            else:
                presence = self.__get_bmc_presence("pwr1.fan.rpm")
            
            #print("#########fan get_presence psu_index:%s presence:%s" % (self.psu_index, presence))
            return presence    
        
        if self.fan_tray_index == 0:
            presence = self.__get_bmc_presence("in.fan0.rpm")
        elif self.fan_tray_index == 1:
            presence = self.__get_bmc_presence("in.fan1.rpm") 
        elif self.fan_tray_index == 2:
            presence = self.__get_bmc_presence("in.fan2.rpm")  
        elif self.fan_tray_index == 3:
            presence = self.__get_bmc_presence("in.fan2.rpm")            
        else: 
            print("unkown fan_tray_index[%s] for get_presence" % self.fan_tray_index)          
        
        #print("fan_tray_index[%s] presence[%s]" % (self.fan_tray_index, presence))  
        return presence        

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        if self.is_psu_fan:
            return NULL_VAL

        model = NULL_VAL
        return model

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        if self.is_psu_fan:
            return NULL_VAL

        serial = NULL_VAL
        return serial

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True


    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of
        entPhysicalContainedIn is'0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device
            or -1 if cannot determine the position
        """
        return (self.fan_tray_index*2 + self.fan_index + 1) \
            if not self.is_psu_fan else (self.fan_index+1)

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True if not self.is_psu_fan else False
