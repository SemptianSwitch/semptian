#############################################################################
# Accton
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################
import os
import os.path

try:
    from sonic_platform_base.psu_base import PsuBase
    #from sonic_platform.fan import Fan
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


I2C_PATH ="/sys/bus/i2c/devices/{0}-00{1}/"

PSU_NAME_LIST = ["PSU-1", "PSU-2"]
PSU_NUM_FAN = [1, 1]
PSU_HWMON_I2C_MAPPING = {
    0: {
        "num": 9,
        "addr": "58"
    },
    1: {
        "num": 9,
        "addr": "59"
    },
}

PSU_CPLD_I2C_MAPPING = {
    0: {
        "num": 9,
        "addr": "50"
    },
    1: {
        "num": 9,
        "addr": "51"
    },
}

class Psu(PsuBase):
    """Platform-specific Psu class"""

    def __init__(self, psu_index=0):
        PsuBase.__init__(self)
        self.index = psu_index
        self._api_helper = APIHelper()

        self.i2c_num = PSU_HWMON_I2C_MAPPING[self.index]["num"]
        self.i2c_addr = PSU_HWMON_I2C_MAPPING[self.index]["addr"]
        self.hwmon_path = I2C_PATH.format(self.i2c_num, self.i2c_addr)

        self.i2c_num = PSU_CPLD_I2C_MAPPING[self.index]["num"]
        self.i2c_addr = PSU_CPLD_I2C_MAPPING[self.index]["addr"]
        self.cpld_path = I2C_PATH.format(self.i2c_num, self.i2c_addr)
        self.__initialize_fan()
        '''
        for fan_index in range(0, PSU_NUM_FAN[self.index]):
            #def __init__(self, fan_tray_index, fan_index=0, is_psu_fan=False, psu_index=0):
            #fan = Fan(fan_index, 0, is_psu_fan=True, psu_index=self.index)
            fan = Fan(fan_index, 0, True, self.index)
            self._fan_list.append(fan)
        '''

    def __initialize_fan(self):
        from sonic_platform.fan import Fan
        for fan_index in range(0, PSU_NUM_FAN[self.index]):
            fan = Fan(fan_index, 0, is_psu_fan=True, psu_index=self.index)
            self._fan_list.append(fan)

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
                    return float(data[0])                
        
        bmc_pipe.close()
        
        return 0 

    def __get_bmc_low_threshold(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sensor')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Thermal get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### sensor[6]:%s" % sensor[6])
                #data = sensor[1].split( )
                #print("### data:%s" % data[0]) 
                bmc_pipe.close()
                return float(sensor[6])                
        
        bmc_pipe.close()
        
        return 0  

    def __get_bmc_middle_threshold(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sensor')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Thermal get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### sensor[6]:%s" % sensor[6])
                #data = sensor[1].split( )
                #print("### data:%s" % data[0]) 
                bmc_pipe.close()
                return float(sensor[6])                
        
        bmc_pipe.close()
        
        return 0 

    def __get_bmc_high_threshold(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sensor')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Thermal get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### sensor[7]:%s" % sensor[7])
                #data = sensor[1].split( )
                #print("### data:%s" % data[0]) 
                bmc_pipe.close()
                return float(sensor[7])                
        
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

    def __get_bmc_status(self, data_str):
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
                #print("### data:%s" % data[0]) 
                    bmc_pipe.close()
                    return False  
                else:
                    bmc_pipe.close()
                    return True                
        
        bmc_pipe.close()
        
        return True 
        
    def get_voltage(self):
        """
        Retrieves current PSU voltage output
        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        
        temp = 0
        if self.index == 0:
            temp = self.__get_bmc("pwr0.vout")
        elif self.index == 1:
            temp = self.__get_bmc("pwr1.vout")  
        else: 
            print("unkown psu index[%s]" % self.index)    

        #print("##psu index[%s] vol[%s] for get_voltage" % (self.index, temp)) 
        
        return  temp         
        
        vout_path = "{}{}".format(self.hwmon_path, 'psu_v_out')        
        vout_val=self._api_helper.read_txt_file(vout_path)
        if vout_val is not None:
            return float(vout_val)/ 1000
        else:
            return 0

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU
        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        
        temp = 0
        if self.index == 0:
            temp = self.__get_bmc("pwr1.iout")
        elif self.index == 1:
            temp = self.__get_bmc("pwr1.iout")  
        else: 
            print("unkown psu index[%s] for get current" % self.index)    

        #print("##psu index[%s] current[%s]" % (self.index, temp)) 
        
        return  temp           
        
        iout_path = "{}{}".format(self.hwmon_path, 'psu_i_out')        
        val=self._api_helper.read_txt_file(iout_path)
        if val is not None:
            return float(val)/1000
        else:
            return 0

    def get_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        
        temp = 0
        if self.index == 0:
            temp = self.__get_bmc("psu.power.in")
        elif self.index == 1:
            temp = self.__get_bmc("psu.power.out")  
        else: 
            print("unkown psu index[%s] for get_power" % self.index)    

        #print("##psu index[%s] get_power[%s]" % (self.index, temp)) 
        
        return  temp          
        
        pout_path = "{}{}".format(self.hwmon_path, 'psu_p_out')        
        val=self._api_helper.read_txt_file(pout_path)
        if val is not None:
            return float(val)/1000
        else:
            return 0

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        return self.get_status()

    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the PSU status LED
                   Note: Only support green and off
        Returns:
            bool: True if status LED state is set successfully, False if not
        """

        return False  #Controlled by HW

    def get_status_led(self):
        """
        Gets the state of the PSU status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """

        return False  #Controlled by HW

    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """

        temp = 0
        if self.index == 0:
            temp = self.__get_bmc("pwr0.tmp")
        elif self.index == 1:
            temp = self.__get_bmc("pwr1.tmp")  
        else: 
            print("unkown psu index[%s] for get_temperature" % self.index)    

        #print("##psu index[%s] get_temperature[%s]" % (self.index, temp)) 
        
        return  temp          
       
        temp_path = "{}{}".format(self.hwmon_path, 'psu_temp1_input')        
        val=self._api_helper.read_txt_file(temp_path)
        if val is not None:
            return float(val)/1000
        else:
            return 0

    def get_temperature_high_threshold(self):
        """
        Retrieves the high threshold temperature of PSU
        Returns:
            A float number, the high threshold temperature of PSU in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return False #Not supported

    def get_voltage_high_threshold(self):
        """
        Retrieves the high threshold PSU voltage output
        Returns:
            A float number, the high threshold output voltage in volts, 
            e.g. 12.1 
        """

        temp = 0
        if self.index == 0:
            temp = self.__get_bmc_high_threshold("pwr0.vout")
        elif self.index == 1:
            temp = self.__get_bmc_high_threshold("pwr1.vout")  
        else: 
            print("unkown psu index[%s]" % self.index)    

        #print("##psu index[%s] vol[%s] for get_voltage" % (self.index, temp)) 
        
        return  temp          
        
        vout_path = "{}{}".format(self.hwmon_path, 'psu_mfr_vout_max')        
        vout_val=self._api_helper.read_txt_file(vout_path)
        if vout_val is not None:
            return float(vout_val)/ 1000
        else:
            return 0

    def get_voltage_low_threshold(self):
        """
        Retrieves the low threshold PSU voltage output
        Returns:
            A float number, the low threshold output voltage in volts, 
            e.g. 12.1 
        """
        
        temp = 0
        if self.index == 0:
            temp = self.__get_bmc_low_threshold("pwr0.vout")
        elif self.index == 1:
            temp = self.__get_bmc_low_threshold("pwr1.vout")  
        else: 
            print("unkown psu index[%s]" % self.index)    

        #print("##psu index[%s] vol[%s] for get_voltage" % (self.index, temp)) 
        
        return  temp              
        
        vout_path = "{}{}".format(self.hwmon_path, 'psu_mfr_vout_min')        
        vout_val=self._api_helper.read_txt_file(vout_path)
        if vout_val is not None:
            return float(vout_val)/ 1000
        else:
            return 0

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return PSU_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """ 
        presence = 0        
        if self.index == 0:
            presence = self.__get_bmc_presence("pwr0.vout")
        elif self.index == 1:
            presence = self.__get_bmc_presence("pwr1.vout") 
        else: 
            print("unkown psu index[%s] for get_presence" % self.index)          
        
        #print("psu index[%s] presence[%s]" % (self.index, presence))  
        return presence
        
        presence_path="{}{}".format(self.cpld_path, 'psu_present')
        val=self._api_helper.read_txt_file(presence_path)
        if val is not None:
            return int(val, 10) == 1
        else:
            return 0

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        
        return True
        
        power_path="{}{}".format(self.cpld_path, 'psu_power_good')
        val=self._api_helper.read_txt_file(power_path)
        if val is not None:
            return int(val, 10) == 1
        else:
            return 0
