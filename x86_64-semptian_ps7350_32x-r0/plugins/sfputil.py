# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    import os
    import sys
    import re
    from ctypes import create_string_buffer
    from sonic_sfp.sfputilbase import SfpUtilBase
    from sonic_sfp.sff8472 import sff8472InterfaceId
    from sonic_sfp.sff8472 import sff8472Dom
    from sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_sfp.sff8436 import sff8436Dom
    from sonic_sfp.inf8628 import inf8628InterfaceId
    from sonic_py_common.interface import backplane_prefix
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

# definitions of the offset and width for values in XCVR info eeprom
XCVR_TYPE_OFFSET = 0
XCVR_TYPE_WIDTH = 1

SFP_TYPE_CODE_LIST = [
    '03'  # SFP/SFP+/SFP28
]
QSFP_TYPE_CODE_LIST = [
    '0d',  # QSFP+ or later
    '11'  # QSFP28 or later
]
QSFP_DD_TYPE_CODE_LIST = [
    '18'  # QSFP-DD Double Density 8X Pluggable Transceiver
]

SFP_TYPE = "SFP"
QSFP_TYPE = "QSFP"
OSFP_TYPE = "OSFP"
QSFP_DD_TYPE = "QSFP_DD"


I2C_EEPROM_PATH = '/sys/bus/i2c/devices/{0}-0050/eeprom'

def DBG_PRINT(str):
    syslog.openlog("semptian-sfputil")
    syslog.syslog(syslog.LOG_INFO, str)
    syslog.closelog()

def get_port_cpld_hwmon_offset():
    sysfs = "cat "
    sysfs = sysfs + '/sys/class/hwmon/hwmon{0}/name'
    
    offset = 3
    cpld_name = 'xc3400an_port_cpld'
    for index in range(0, 10):
        cmd=sysfs.format(index)
        ret = os.popen(cmd)
        adaptername=ret.read()
        
        #print("cmd:%s  adaptername:%s find result:%s" % (cmd, adaptername, adaptername.find(cpld_name)))
        
        if adaptername.find(cpld_name) >= 0:
            #print("get:%s  adaptername:%s" % (cmd, adaptername))
            offset = index 
            ret.close()       
            break
        else:
            ret.close()
            
    return  offset 

def get_mg_cpld_adapter_offset():
    sysfs = "cat "
    sysfs = sysfs + '/sys/bus/i2c/devices/i2c-{0}/name'

    offset = 0
    for index in range(0, 10):
        cmd=sysfs.format(index)
        ret = os.popen(cmd)
        adaptername=ret.read()
        #print("cmd:%s  adaptername:%s" % (cmd, adaptername))
        if adaptername.find('cpld mg I2C adapter') >= 0:
            offset = index
            #print("get cmd:%s  adaptername:%s" % (cmd, adaptername))
            ret.close()  
            break 
        else:
            ret.close() 
            
    return  offset 
    
class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 33
    OSFP_PORT_START = 0
    OSFP_PORT_END = 31
    PORTS_IN_BLOCK = 34
    
    SFP_ADAPTER_OFFSET = 17
    
    BASE_OOM_PATH = "/sys/bus/i2c/devices/{0}-0050/"
    #cmd = "ls "
    #cmd = cmd + '/sys/bus/i2c/devices/5-0011/hwmon/'
    #ret = os.popen(cmd)
    #temp ='/sys/bus/i2c/devices/5-0011/hwmon/' +   ret.read()
    #temp = temp[:-1]
    #temp = temp + '/'
    #BASE_CPLD1_PATH = temp
    
    index = get_port_cpld_hwmon_offset()        
    path = '/sys/class/hwmon/hwmon{0}/'
    BASE_CPLD1_PATH = path.format(index)
    #print("SfpUtil BASE_CPLD1_PATH %s" % BASE_CPLD1_PATH)
    mg_adapterid = get_mg_cpld_adapter_offset()
    SFP_I2C_START = SFP_ADAPTER_OFFSET + mg_adapterid
    
    _port_to_is_present = {}
    _port_to_lp_mode = {}

    sfp_port_cur_present_state = {}
        
    for i in range(PORT_START, PORT_END+1):
        sfp_port_cur_present_state[i] = '0'

    _port_to_eeprom_mapping = {}
            
    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return []

    @property
    def osfp_ports(self):
        return list(range(self.OSFP_PORT_START, self.OSFP_PORT_END + 1))

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        eeprom_path = self.BASE_OOM_PATH + "eeprom"

        for x in range(0, self.port_end+1):
            sfp_id = self.SFP_ADAPTER_OFFSET + self.mg_adapterid + x
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                sfp_id
            )

        SfpUtilBase.__init__(self)

    def __write_txt_file(self, file_path, value):
        try:
            reg_file = open(file_path, "w")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_file.write(str(value))
        reg_file.close()

        return True
        
    def __read_txt_file(self, file_path):
        try:
            reg_file = open(file_path, "r")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        data = reg_file.readline().rstrip()
        reg_file.close()

        return data
        
    def _get_eeprom_path(self, port_num):
        port_to_i2c_mapping = self.SFP_I2C_START + port_num
        port_eeprom_path = I2C_EEPROM_PATH.format(port_to_i2c_mapping)
        return port_eeprom_path

    def _read_eeprom_specific_bytes_(self, offset, num_bytes, port_num):
        sysfs_sfp_i2c_client_eeprom_path = self._get_eeprom_path(port_num)
        eeprom_raw = []
        try:
            eeprom = open(
                sysfs_sfp_i2c_client_eeprom_path,
                mode="rb", buffering=0)
        except IOError:
            print("open sfp eeprom error port_num:%s sysfs:%s" % (port_num, sysfs_sfp_i2c_client_eeprom_path))
            return None

        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        try:
            eeprom.seek(offset)
            raw = eeprom.read(num_bytes)
        except IOError:
            eeprom.close()
            print("open sfp eeprom error port_num:%s sysfs:%s" % (port_num, sysfs_sfp_i2c_client_eeprom_path))
            return None

        try:
            if isinstance(raw, str):
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)
            else:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(raw[n])[2:].zfill(2)

        except BaseException:
            eeprom.close()
            return None

        eeprom.close()
        return eeprom_raw

    def _detect_sfp_type(self, port_num):
        sfp_type = QSFP_TYPE
        eeprom_raw = []
        eeprom_raw = self._read_eeprom_specific_bytes_(
            XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH, port_num)
        if eeprom_raw:
            if eeprom_raw[0] in SFP_TYPE_CODE_LIST:
                self.sfp_type = SFP_TYPE
            elif eeprom_raw[0] in QSFP_TYPE_CODE_LIST:
                self.sfp_type = QSFP_TYPE
            elif eeprom_raw[0] in QSFP_DD_TYPE_CODE_LIST:
                self.sfp_type = QSFP_DD_TYPE
            else:
                self.sfp_type = sfp_type
        else:
            self.sfp_type = sfp_type

    def get_eeprom_dict(self, port_num):
        """Returns dictionary of interface and dom data.
        format: {<port_num> : {'interface': {'version' : '1.0', 'data' : {...}},
                               'dom' : {'version' : '1.0', 'data' : {...}}}}
        """
        self._detect_sfp_type(port_num)
        sfp_data = {}

        eeprom_ifraw = self.get_eeprom_raw(port_num)
        eeprom_domraw = self.get_eeprom_dom_raw(port_num)

        if eeprom_ifraw is None:
            return None

        if self.sfp_type == QSFP_DD_TYPE:
            sfpi_obj = inf8628InterfaceId(eeprom_ifraw)

            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()

            return sfp_data
        elif self.sfp_type == QSFP_TYPE:
            sfpi_obj = sff8436InterfaceId(eeprom_ifraw)

            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()

            # For Qsfp's the dom data is part of eeprom_if_raw
            # The first 128 bytes
            sfpd_obj = sff8436Dom(eeprom_ifraw)
            if sfpd_obj is not None:
                sfp_data['dom'] = sfpd_obj.get_data_pretty()

            return sfp_data
        else:
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)

            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
                cal_type = sfpi_obj.get_calibration_type()

            if eeprom_domraw is not None:
                sfpd_obj = sff8472Dom(eeprom_domraw, cal_type)
                if sfpd_obj is not None:
                    sfp_data['dom'] = sfpd_obj.get_data_pretty()

            return sfp_data

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        present_path = self.BASE_CPLD1_PATH + "port" + str(port_num) + "_present"
        self.__port_to_is_present = present_path
        content = "1"
        try:
            val_file = open(self.__port_to_is_present)
            content = val_file.readline().rstrip()
            val_file.close()
        except IOError as e:
            print("Error: unable to access file: %s" % str(e))
            return False
            
        if content == "0":
            return True

        return False

    def get_low_power_mode_sfp(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            eeprom = None

            if not self.get_presence(port_num):
                return False

            eeprom = open(self.port_to_eeprom_mapping[port_num], "rb")
            eeprom.seek(93)
            lpmode = ord(eeprom.read(1))

            if ((lpmode & 0x3) == 0x3):
                return True  # Low Power Mode if "Power override" bit is 1 and "Power set" bit is 1
            else:
                # High Power Mode if one of the following conditions is matched:
                # 1. "Power override" bit is 0
                # 2. "Power override" bit is 1 and "Power set" bit is 0
                return False
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False
        finally:
            if eeprom is not None:
                eeprom.close()
                time.sleep(0.01)

    def set_low_power_mode_sfp(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            eeprom = None

            if not self.get_presence(port_num):
                return False  # Port is not present, unable to set the eeprom

            # Fill in write buffer
            # 0x3:Low Power Mode. "Power override" bit is 1 and "Power set" bit is 1
            # 0x9:High Power Mode. "Power override" bit is 1 ,"Power set" bit is 0 and "High Power Class Enable" bit is 1
            regval = 0x3 if lpmode else 0x9

            buffer = create_string_buffer(1)
            buffer[0] = chr(regval)

            # Write to eeprom
            eeprom = open(self.port_to_eeprom_mapping[port_num], "r+b")
            eeprom.seek(93)
            eeprom.write(buffer[0])
            return True
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False
        finally:
            if eeprom is not None:
                eeprom.close()
                time.sleep(0.01)
                
    def set_low_power_mode(self, port_num, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        if port_num < self.port_start or port_num > self.port_end:
            return False
                
        lpmode_path = self.BASE_CPLD1_PATH + "port" + str(port_num) + "_lpmode" 
        
        data = "0"
        if lpmode is not True:
            data = "0"
        else:  
            data = "1" 
            
        ret = self.__write_txt_file(lpmode_path, data) #sysfs 1: enable lpmode
        
        return ret  
            
    def get_low_power_mode(self, port_num):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        if port_num < self.port_start or port_num > self.port_end:
            return False
            
        lpmode_path = self.BASE_CPLD1_PATH + "port" + str(port_num) + "_lpmode" 

        val=self.__read_txt_file(lpmode_path)
        if val is not None:
            return int(val, 10)==1
        else:           
            return False
            
    def reset(self, port_num):
        if port_num < self.port_start or port_num > self.port_end:
            return False

        mod_rst_path = self.BASE_CPLD1_PATH + "module_reset_" + str(port_num)

        ret = self.__write_txt_file(mod_rst_path, "0")
        time.sleep(0.2)
        ret = self.__write_txt_file(mod_rst_path, "1")

        return True

    def get_cpld_interrupt(self):
        return True

    def get_transceiver_change_event(self, timeout=0):
        start_time = time.time()
        port_dict = {}
        ori_present = {}
        forever = False
        change_status = 0

        #DBG_PRINT("#################get_transceiver_change_event sfp_port_cur_present_state {}".format(self.sfp_port_cur_present_state))
        
        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000)  # Convert to secs
        else:
            print("get_transceiver_change_event:Invalid timeout value", timeout)
            return False, {}

        end_time = start_time + timeout
        if start_time > end_time:
            print('get_transceiver_change_event:'
                  'time wrap / invalid timeout value', timeout)

            return False, {}  # Time wrap or possibly incorrect timeout

        # for i in range(self.port_start, self.port_end+1):
        #        ori_present[i]=self.get_presence(i)
        #time.sleep(3)
        for i in range(self.port_start, self.port_end+1):
            value = self.get_presence(i)
            if value:
                port_dict[i] = '1'
            else:
                port_dict[i] = '0'    
            
            if self.sfp_port_cur_present_state[i] !=  port_dict[i]:
                self.sfp_port_cur_present_state[i] =  port_dict[i]
                change_status = 1
            else:
                del port_dict[i]            
            #print("yyyy {} {}".format(i,port_dict[i]))
            
        if 1 == change_status:
          DBG_PRINT("get_transceiver_change_event port_dict {} port_start {} port_end {}".format(port_dict, self.port_start, self.port_end))  
          
        return True, port_dict
        
        while timeout >= 0:
            change_status = 0

            port_dict = self.get_cpld_interrupt()
            present = 0
            for key, value in port_dict.items():
                if value == 1:
                    present = self.get_presence(key)
                    change_status = 1
                    if present:
                        port_dict[key] = '1'
                    else:
                        port_dict[key] = '0'

            if change_status:
                return True, port_dict
            if forever:
                time.sleep(1)
            else:
                timeout = end_time - time.time()
                if timeout >= 1:
                    time.sleep(1)  # We poll at 1 second granularity
                else:
                    if timeout > 0:
                        time.sleep(timeout)
                    return True, {}
        print("get_evt_change_event: Should not reach here.")
        return False, {}
        
    def read_porttab_mappings(self, porttabfile, asic_inst=0):
        logical = []
        logical_to_bcm = {}
        logical_to_physical = {}
        physical_to_logical = {}
        last_fp_port_index = 0
        last_portname = ""
        first = 1
        port_pos_in_file = 0
        parse_fmt_port_config_ini = False

        try:
            f = open(porttabfile)
        except:
            raise

        parse_fmt_port_config_ini = (os.path.basename(porttabfile) == "port_config.ini")

        # Read the porttab file and generate dicts
        # with mapping for future reference.
        #
        # TODO: Refactor this to use the portconfig.py module that now
        # exists as part of the sonic-config-engine package.
        title = []
        for line in f:
            line.strip()
            if re.search("^#", line) is not None:
                # The current format is: # name lanes alias index speed
                # Where the ordering of the columns can vary
                title = line.split()[1:]
                continue

            # Parsing logic for 'port_config.ini' file
            if (parse_fmt_port_config_ini):
                # bcm_port is not explicitly listed in port_config.ini format
                # Currently we assume ports are listed in numerical order according to bcm_port
                # so we use the port's position in the file (zero-based) as bcm_port
                portname = line.split()[0]

                # Ignore if this is an internal backplane interface
                if portname.startswith(backplane_prefix()):
                    continue

                bcm_port = str(port_pos_in_file)

                if "index" in title:
                    fp_port_index = int(line.split()[title.index("index")])
                # Leave the old code for backward compatibility
                elif "asic_port_name" not in title and len(line.split()) >= 4:
                    fp_port_index = int(line.split()[3])
                else:
                    fp_port_index = portname.split("Ethernet").pop()
                    fp_port_index = int(fp_port_index.split("s").pop(0))/4
            else:  # Parsing logic for older 'portmap.ini' file
                (portname, bcm_port) = line.split("=")[1].split(",")[:2]

                fp_port_index = portname.split("Ethernet").pop()
                fp_port_index = int(fp_port_index.split("s").pop(0))/4

            if ((len(self.sfp_ports) > 0) and (fp_port_index not in self.sfp_ports)):
                continue

            if first == 1:
                # Initialize last_[physical|logical]_port
                # to the first valid port
                last_fp_port_index = fp_port_index
                last_portname = portname
                first = 0

            logical.append(portname)

            # Mapping of logical port names available on a system to ASIC instance
            self.logical_to_asic[portname] = asic_inst

            logical_to_bcm[portname] = "xe" + bcm_port
            logical_to_physical[portname] = [fp_port_index]
            if physical_to_logical.get(fp_port_index) is None:
                physical_to_logical[fp_port_index] = [portname]
            else:
                physical_to_logical[fp_port_index].append(
                    portname)

            last_fp_port_index = fp_port_index
            last_portname = portname

            port_pos_in_file += 1

        self.logical.extend(logical)
        self.logical_to_bcm.update(logical_to_bcm)
        self.logical_to_physical.update(logical_to_physical)
        self.physical_to_logical.update(physical_to_logical)

        """
        print("logical: " + self.logical)
        print("logical to bcm: " + self.logical_to_bcm)
        print("logical to physical: " + self.logical_to_physical)
        print("physical to logical: " + self.physical_to_logical)
     """
     
    def get_asic_id_for_logical_port(self, logical_port):
        """Returns the asic_id list of physical ports for the given logical port"""
        return self.logical_to_asic.get(logical_port)
  