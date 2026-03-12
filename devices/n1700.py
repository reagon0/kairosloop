"""
Kairosloop N1700 Driver
Python wrapper for Mahr Millimar N1700.dll
"""

import ctypes
from ctypes import c_int, c_uint, c_double, c_float, c_bool, c_byte, POINTER, Structure, byref
from enum import IntEnum
from pathlib import Path


# Return codes
class N1700Error(IntEnum):
    SUCCESS = 0
    FAILURE = -1
    TIMEOUT = -2
    INVALID_DEVNO = -3
    NO_MODULES = -4
    FILENOTEXISTS = -5
    WRONGFILEFORMAT = -6
    NOTYETSUPPORTED = -7
    INVALID_CHANNELIDX = -8
    CONTINUOUS_ACTIVE = -9
    CALL_STILL_IN_ACTION = -10
    WRONG_MODULETYPE = -11
    FILEVARIANTNOTEXISTS = -12


class ModuleType(IntEnum):
    UNDEF = 0
    POWER = 1
    TERMINATION = 2
    N1701USB = 3
    N1702M = 4
    N1702T = 5
    N1702U = 6
    N1704M = 7
    N1704T = 8
    N1704U = 9
    N1704IO = 10
    N1701PMXXXX = 11
    N1701PM2500 = 12
    N1701PM5000 = 13
    N1701PM10000 = 14
    N1701PF25005000 = 15
    N1701PF25005000_4 = 16
    N1701PF10000 = 17
    N1702M_HR = 18
    N1702VPP = 19


class PortType(IntEnum):
    NONE = 0
    ANALOG = 1
    DIGITAL = 2
    INCR = 3


class sN1700_Module(Structure):
    _fields_ = [
        ("ModuleIdx", c_uint),
        ("sFtDescription", c_byte * 40),
        ("sFtSerial", c_byte * 12),
        ("ModuleType", c_byte),
        ("sModuleType", c_byte * 24),
        ("sDescription", c_byte * 24),
        ("sIdentNo", c_byte * 8),
        ("sSerialNo", c_byte * 9),
        ("sFirmwareVersion", c_byte * 10),
        ("ChannelCount", c_byte),
        ("PowerModuleNeeded", c_byte),
        ("PowerConsumption_mA", ctypes.c_short),
        ("ChannelIdxArray", c_uint * 4),
    ]


class sN1700_Channel(Structure):
    _fields_ = [
        ("ChannelIdx", c_uint),
        ("ParentModuleIdx", c_uint),
        ("tPortType", c_byte),
        ("PortInCount", c_byte),
        ("PortOutCount", c_byte),
        ("Decimals", c_byte),
        ("DigFilter", c_uint),
        ("CustomerCalibActive", c_byte),
        ("CustomerCalibrated", c_byte),
        ("FactoryCalibrated", c_byte),
        ("Reserve", c_byte),
    ]


class N1700Exception(Exception):
    """Exception raised for N1700 errors."""
    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.message = message or f"N1700 error code: {code}"
        super().__init__(self.message)


class N1700:
    """
    Python wrapper for Mahr Millimar N1700.dll
    
    Usage:
        gauge = N1700()
        gauge.initialize()
        value = gauge.poll_data(channel=0)
        gauge.close()
    """
    
    def __init__(self, dll_path: str = None, use_64bit: bool = False):
        """
        Initialize the N1700 wrapper.
        
        Args:
            dll_path: Path to N1700.dll (optional, will search default locations)
            use_64bit: Use N1700_64.dll instead of N1700.dll
        """
        self._dll = None
        self._initialized = False
        self._num_modules = 0
        self._num_channels = 0
        
        dll_name = "N1700_64.dll" if use_64bit else "N1700.dll"
        
        if dll_path:
            self._dll_path = Path(dll_path)
        else:
            self._dll_path = Path(dll_name)
        
        self._load_dll()
    
    def _load_dll(self):
        """Load the N1700 DLL."""
        try:
            self._dll = ctypes.WinDLL(str(self._dll_path))
        except OSError as e:
            raise N1700Exception(-1, f"Failed to load DLL: {e}")
        
        self._setup_functions()
    
    def _setup_functions(self):
        """Setup function signatures for the DLL."""
        # N1700InitializeLibrary
        self._dll.N1700InitializeLibrary.argtypes = [c_bool, POINTER(c_uint), POINTER(c_uint), c_int]
        self._dll.N1700InitializeLibrary.restype = c_int
        
        # N1700FreeLibrary
        self._dll.N1700FreeLibrary.argtypes = []
        self._dll.N1700FreeLibrary.restype = c_int
        
        # N1700GetNumModules
        self._dll.N1700GetNumModules.argtypes = []
        self._dll.N1700GetNumModules.restype = c_int
        
        # N1700GetNumChannels
        self._dll.N1700GetNumChannels.argtypes = []
        self._dll.N1700GetNumChannels.restype = c_int
        
        # N1700GetModule
        self._dll.N1700GetModule.argtypes = [c_uint, POINTER(sN1700_Module)]
        self._dll.N1700GetModule.restype = c_int
        
        # N1700GetChannel
        self._dll.N1700GetChannel.argtypes = [c_uint, POINTER(sN1700_Channel)]
        self._dll.N1700GetChannel.restype = c_int
        
        # N1700PollData
        self._dll.N1700PollData.argtypes = [c_uint, POINTER(c_double)]
        self._dll.N1700PollData.restype = c_int
        
        # N1700Refresh
        self._dll.N1700Refresh.argtypes = [POINTER(c_uint), POINTER(c_uint)]
        self._dll.N1700Refresh.restype = c_int
        
        # N1700GetCalibration
        self._dll.N1700GetCalibration.argtypes = [c_uint, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        self._dll.N1700GetCalibration.restype = c_int
        
        # N1700SetOffsetMM
        self._dll.N1700SetOffsetMM.argtypes = [c_uint, c_float]
        self._dll.N1700SetOffsetMM.restype = c_int
    
    def _check_result(self, result: int, operation: str = ""):
        """Check the result code and raise exception if error."""
        if result != N1700Error.SUCCESS:
            raise N1700Exception(result, f"{operation} failed with code {result}")
    
    def initialize(self, console: bool = False) -> tuple:
        """
        Initialize the library and detect connected modules.
        
        Returns:
            Tuple of (num_modules, num_channels)
        """
        num_modules = c_uint()
        num_channels = c_uint()
        
        result = self._dll.N1700InitializeLibrary(
            console, 
            byref(num_modules), 
            byref(num_channels), 
            0
        )
        self._check_result(result, "Initialize")
        
        self._initialized = True
        self._num_modules = num_modules.value
        self._num_channels = num_channels.value
        
        return (self._num_modules, self._num_channels)
    
    def close(self):
        """Close the library and release resources."""
        if self._initialized:
            self._dll.N1700FreeLibrary()
            self._initialized = False
    
    def refresh(self) -> tuple:
        """
        Refresh the module/channel detection.
        
        Returns:
            Tuple of (num_modules, num_channels)
        """
        num_modules = c_uint()
        num_channels = c_uint()
        
        result = self._dll.N1700Refresh(byref(num_modules), byref(num_channels))
        self._check_result(result, "Refresh")
        
        self._num_modules = num_modules.value
        self._num_channels = num_channels.value
        
        return (self._num_modules, self._num_channels)
    
    def get_num_modules(self) -> int:
        """Get the number of connected modules."""
        return self._dll.N1700GetNumModules()
    
    def get_num_channels(self) -> int:
        """Get the total number of channels."""
        return self._dll.N1700GetNumChannels()
    
    def get_module(self, module_idx: int) -> dict:
        """
        Get information about a module.
        
        Args:
            module_idx: Module index (0 to num_modules-1)
            
        Returns:
            Dictionary with module information
        """
        module = sN1700_Module()
        result = self._dll.N1700GetModule(module_idx, byref(module))
        self._check_result(result, f"GetModule({module_idx})")
        
        return {
            "index": module.ModuleIdx,
            "type": ModuleType(module.ModuleType),
            "type_name": bytes(module.sModuleType).decode('utf-8').rstrip('\x00'),
            "description": bytes(module.sDescription).decode('utf-8').rstrip('\x00'),
            "ident_no": bytes(module.sIdentNo).decode('utf-8').rstrip('\x00'),
            "serial_no": bytes(module.sSerialNo).decode('utf-8').rstrip('\x00'),
            "firmware": bytes(module.sFirmwareVersion).decode('utf-8').rstrip('\x00'),
            "channel_count": module.ChannelCount,
            "channels": list(module.ChannelIdxArray[:module.ChannelCount]),
        }
    
    def get_channel(self, channel_idx: int) -> dict:
        """
        Get information about a channel.
        
        Args:
            channel_idx: Channel index (0 to num_channels-1)
            
        Returns:
            Dictionary with channel information
        """
        channel = sN1700_Channel()
        result = self._dll.N1700GetChannel(channel_idx, byref(channel))
        self._check_result(result, f"GetChannel({channel_idx})")
        
        return {
            "index": channel.ChannelIdx,
            "parent_module": channel.ParentModuleIdx,
            "port_type": PortType(channel.tPortType),
            "port_in_count": channel.PortInCount,
            "port_out_count": channel.PortOutCount,
            "decimals": channel.Decimals,
            "customer_calib_active": bool(channel.CustomerCalibActive),
            "customer_calibrated": bool(channel.CustomerCalibrated),
            "factory_calibrated": bool(channel.FactoryCalibrated),
        }
    
    def poll_data(self, channel_idx: int) -> float:
        """
        Read measurement value from a channel.
        
        Args:
            channel_idx: Channel index (0 to num_channels-1)
            
        Returns:
            Measurement value in mm
        """
        data = c_double()
        result = self._dll.N1700PollData(channel_idx, byref(data))
        self._check_result(result, f"PollData({channel_idx})")
        
        return data.value
    
    def get_calibration(self, channel_idx: int) -> dict:
        """
        Get calibration parameters for a channel.
        
        Args:
            channel_idx: Channel index
            
        Returns:
            Dictionary with offset_mm, digits_to_mm, gain
        """
        offset = c_float()
        digits_to_mm = c_float()
        gain = c_float()
        
        result = self._dll.N1700GetCalibration(
            channel_idx, 
            byref(offset), 
            byref(digits_to_mm), 
            byref(gain)
        )
        self._check_result(result, f"GetCalibration({channel_idx})")
        
        return {
            "offset_mm": offset.value,
            "digits_to_mm": digits_to_mm.value,
            "gain": gain.value,
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Example usage
if __name__ == "__main__":
    with N1700() as gauge:
        print(f"Modules: {gauge.get_num_modules()}")
        print(f"Channels: {gauge.get_num_channels()}")
        
        for i in range(gauge.get_num_channels()):
            value = gauge.poll_data(i)
            print(f"Channel {i}: {value:.6f} mm")