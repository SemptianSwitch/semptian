#############################################################################
# Accton
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import os.path
import glob

try:
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    THERMAL_NAME_LIST = []
    SYSFS_PATH = "/sys/bus/i2c/devices"

    def __init__(self, thermal_index=0):
        self.THERMAL_NAME_LIST = []
        self.SYSFS_PATH = "/sys/bus/i2c/devices"
        self.index = thermal_index
        # Add thermal name
        self.THERMAL_NAME_LIST.append("mb_air.in.tmp")
        self.THERMAL_NAME_LIST.append("mb_air.out.tmp")
        self.THERMAL_NAME_LIST.append("mb_tmp411.bf.tmp")        
        self.THERMAL_NAME_LIST.append("Temp sensor 4")       
        self.THERMAL_NAME_LIST.append("Temp sensor 5")        
        self.THERMAL_NAME_LIST.append("Temp sensor 6")        

        # Set hwmon path
        i2c_path = {
            0: "15-0048/hwmon/hwmon*/", 
            1: "15-0049/hwmon/hwmon*/", 
            2: "15-004a/hwmon/hwmon*/", 
            3: "15-004b/hwmon/hwmon*/", 
            4: "15-004c/hwmon/hwmon*/", 
            5: "15-004f/hwmon/hwmon*/"
        }.get(self.index, None)

        self.hwmon_path = "{}/{}".format(self.SYSFS_PATH, i2c_path)
        self.ss_key = self.THERMAL_NAME_LIST[self.index]
        self.ss_index = 1
        #print("###########class Thermal init")

    def __read_txt_file(self, file_path):
        for filename in glob.glob(file_path):
            try:
                with open(filename, 'r') as fd:                    
                    data =fd.readline().rstrip()
                    return data
            except IOError as e:
                pass

        return None

    def __get_temp(self, temp_file):
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_temp = self.__read_txt_file(temp_file_path)
        if raw_temp is not None:
            return float(raw_temp)/1000
        else:
            return 0        

    def __get_bmc(self, data_str):
        bmc_pipe = os.popen('/usr/share/sonic/platform/plugins/ipmitool sdr')
        str_bmc = bmc_pipe.read()
        #print("##########get str_bmc:%s" % str_bmc)
        
        #print("!!!!!!!!!!!!!!Thermal get str_bmc data_str:%s!!!!!!!!!!!!!!!!" % data_str)
        
        #print (str_bmc.split('\n'))
        strs_tmp = str_bmc.split('\n')
        for str_tmp in strs_tmp:
            sensor = str_tmp.split('|')
            if sensor[0].find(data_str) >= 0:
                #print("### sensor:%s" % sensor[1])
                data = sensor[1].split( )
                #print("### data:%s" % data[0]) 
                bmc_pipe.close()
                return int(data[0])                
        
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

    def __set_threshold(self, file_name, temperature):
        temp_file_path = os.path.join(self.hwmon_path, file_name)
        for filename in glob.glob(temp_file_path):
            try:
                with open(filename, 'w') as fd:
                    fd.write(str(temperature))
                return True
            except IOError as e:
                print("IOError")


    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        
        temp = 0
        if self.index == 1:
            temp = self.__get_bmc("mb_air.in.tmp")
        elif self.index == 2:
            temp = self.__get_bmc("mb_air.out.tmp")  
        else: 
            temp = self.__get_bmc("mb_tmp411.bf.tmp")   
        
        #print("#########thermal get_temperature temp:%s index:%s" % (temp, self.index))
        return temp
        
        temp_file = "temp{}_input".format(self.ss_index)
        return self.__get_temp(temp_file)

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        
        temp = 0
        if self.index == 1:
            temp = self.__get_bmc_high_threshold("mb_air.in.tmp")
        elif self.index == 2:
            temp = self.__get_bmc_high_threshold("mb_air.out.tmp")  
        else: 
            temp = self.__get_bmc_high_threshold("mb_tmp411.bf.tmp")   
        
        #print("#########thermal get_high_threshold temp:%s index:%s" % (temp, self.index))
        return temp
        
        temp_file = "temp{}_max".format(self.ss_index)
        return self.__get_temp(temp_file)

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal
        Args :
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125
        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        temp_file = "temp{}_max".format(self.ss_index)
        temperature = temperature *1000
        self.__set_threshold(temp_file, temperature)

        return True

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        return self.THERMAL_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the Thermal
        Returns:
            bool: True if Thermal is present, False if not
        """
        
        return True
        
        temp_file = "temp{}_input".format(self.ss_index)
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_txt = self.__read_txt_file(temp_file_path)
        if raw_txt is not None:
            return True
        else:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True
        
        file_str = "temp{}_input".format(self.ss_index)
        file_path = os.path.join(self.hwmon_path, file_str)
        raw_txt = self.__read_txt_file(file_path)
        if raw_txt is None:
            return False
        else:     
            return int(raw_txt) != 0
