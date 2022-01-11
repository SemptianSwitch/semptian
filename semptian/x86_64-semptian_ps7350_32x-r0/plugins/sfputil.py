# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    import os
    import sys
    from ctypes import create_string_buffer
    from sonic_sfp.sfputilbase import SfpUtilBase
    from sonic_sfp.sff8472 import sff8472InterfaceId
    from sonic_sfp.sff8472 import sff8472Dom
    from sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_sfp.sff8436 import sff8436Dom
    from sonic_sfp.inf8628 import inf8628InterfaceId
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

SFP_I2C_START = 25
I2C_EEPROM_PATH = '/sys/bus/i2c/devices/{0}-0050/eeprom'

class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 33
    OSFP_PORT_START = 0
    OSFP_PORT_END = 31
    PORTS_IN_BLOCK = 34

    BASE_OOM_PATH = "/sys/bus/i2c/devices/{0}-0050/"
    cmd = "ls "
    cmd = cmd + '/sys/bus/i2c/devices/5-0011/hwmon/'
    ret = os.popen(cmd)
    temp ='/sys/bus/i2c/devices/5-0011/hwmon/' +   ret.read()
    temp = temp[:-1]
    temp = temp + '/'
    BASE_CPLD1_PATH = temp
    

    _port_to_is_present = {}
    _port_to_lp_mode = {}

    _port_to_eeprom_mapping = {}
    _port_to_i2c_mapping = {
        0: [1, 18],
        1: [2, 19],
        2: [3, 20],
        3: [4, 21],
        4: [5, 22],
        5: [6, 23],
        6: [7, 24],
        7: [8, 25],
        8: [9, 26],
        9: [10, 27],
        10: [11, 28],
        11: [12, 29],
        12: [13, 30],
        13: [14, 31],
        14: [15, 32],
        15: [16, 33],
        16: [17, 34],
        17: [18, 35],
        18: [19, 36],
        19: [20, 37],
        20: [21, 38],
        21: [22, 39],
        22: [23, 40],
        23: [24, 41],
        24: [25, 42],
        25: [26, 43],
        26: [27, 44],
        27: [28, 45],
        28: [29, 46],
        29: [30, 47],
        30: [31, 48],
        31: [32, 49],
        32: [33, 50],
        33: [34, 51],
    }

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
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                self._port_to_i2c_mapping[x][1]
            )

        SfpUtilBase.__init__(self)

    def _get_eeprom_path(self, port_num):
        port_to_i2c_mapping = SFP_I2C_START + port_num
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
            return None

        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        try:
            eeprom.seek(offset)
            raw = eeprom.read(num_bytes)
        except IOError:
            eeprom.close()
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

    def get_low_power_mode(self, port_num):
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

    def set_low_power_mode(self, port_num, lpmode):
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

    def reset(self, port_num):
        if port_num < self.port_start or port_num > self.port_end:
            return False

        mod_rst_path = self.BASE_CPLD1_PATH + "module_reset_" + str(port_num+1)


        self.__port_to_mod_rst = mod_rst_path
        try:
            reg_file = open(self.__port_to_mod_rst, 'r+')
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = '1'

        reg_file.write(reg_value)
        reg_file.close()

        return True

    def get_cpld_interrupt(self):
        return True

    def get_transceiver_change_event(self, timeout=0):
        start_time = time.time()
        port_dict = {}
        ori_present = {}
        forever = False

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
        time.sleep(3)
        for i in range(self.port_start, self.port_end-1):
            value = self.get_presence(i)
            if value:
                port_dict[i] = '1'
            else:
                port_dict[i] = '0'
            #print("yyyy {} {}".format(i,port_dict[i]))
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
