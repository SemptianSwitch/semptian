#############################################################################
# Ingrasys S9180-32X
#
# Platform and model specific eeprom subclass, inherits from the base class,
# and provides the followings:
# - the eeprom format definition
# - specific encoder/decoder if there is special need
#############################################################################

try:
    import os
    from sonic_eeprom import eeprom_tlvinfo
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

EEPROM_I2C_OFFSET = 7
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
            offset = EEPROM_I2C_OFFSET + index
            #print("get cmd:%s  adaptername:%s" % (cmd, adaptername))
            ret.close()  
            break 
        else:
            ret.close() 
            
    return  offset 
    
class board(eeprom_tlvinfo.TlvInfoDecoder):

    def __init__(self, name, path, cpld_root, ro):

        offset =  get_mg_cpld_adapter_offset()    
        eeprom_path_tmp = "/sys/bus/i2c/devices/{0}-0053/eeprom"
        self._eeprom_path = eeprom_path_tmp.format(offset)
        #print("get eeprom_path:%s" % self._eeprom_path)
        super(board, self).__init__(self._eeprom_path, 0, '', True)
