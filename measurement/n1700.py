"""
Kairosloop N1700 Driver
Python wrapper for Mahr Millimar N1700.dll

Updated: Added continuous mode and filter control
"""

import ctypes
from ctypes import (
    c_int, c_uint, c_double, c_float, c_bool, c_byte, c_void_p,
    POINTER, Structure, byref, CFUNCTYPE
)
from enum import IntEnum
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any


# =============================================================================
# CONSTANTS AND ENUMS
# =============================================================================

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


class LedState(IntEnum):
    OFF = 0
    ON = 1
    BLOCKED = 2
    UNBLOCKED = 3


class FilterLevel(IntEnum):
    """Digital averaging filter levels."""
    OFF = 0        # No averaging (raw)
    AVG_2 = 1      # 2 samples
    AVG_4 = 2      # 4 samples
    AVG_8 = 3      # 8 samples
    AVG_16 = 4     # 16 samples
    AVG_32 = 5     # 32 samples (default)
    AVG_64 = 6     # 64 samples


# =============================================================================
# STRUCTURES
# =============================================================================

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


class N1700Version(Structure):
    _fields_ = [
        ("N1700lib_major", c_int),
        ("N1700lib_minor", c_int),
        ("N1700lib_micro", c_int),
        ("N1700lib_nano", c_int),
        ("FTDIlib_major", c_int),
        ("FTDIlib_minor", c_int),
        ("FTDIlib_micro", c_int),
        ("FTDIlib_nano", c_int),
    ]


# =============================================================================
# CALLBACK TYPES
# =============================================================================

# Callback signature: int callback(int numChannels, int* pChannelIdxArray, double* pData, void* pContext)
DATA_CALLBACK_TYPE = CFUNCTYPE(c_int, c_int, POINTER(c_int), POINTER(c_double), c_void_p)

# Message callback signature: int callback(int msg, uint32 channel, int param)
MSG_CALLBACK_TYPE = CFUNCTYPE(c_int, c_int, c_uint, c_int)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class N1700Exception(Exception):
    """Exception raised for N1700 errors."""
    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.message = message or f"N1700 error code: {code}"
        super().__init__(self.message)


# =============================================================================
# MAIN CLASS
# =============================================================================

class N1700:
    """
    Python wrapper for Mahr Millimar N1700.dll
    
    Usage (polling mode):
        gauge = N1700()
        gauge.initialize()
        value = gauge.poll_data(channel=0)
        gauge.close()
    
    Usage (continuous mode):
        gauge = N1700()
        gauge.initialize()
        
        def on_data(channel_data: dict):
            for ch, value in channel_data.items():
                print(f"Channel {ch}: {value}")
        
        gauge.start_continuous(callback=on_data)
        # ... data streams to callback ...
        gauge.stop_continuous()
        gauge.close()
    """
    
    # Default DLL search paths (relative to project or absolute)
    DEFAULT_DLL_PATHS = [
        # Project vendor directory
        "Millimar--N1700--SW-2024-07-31/Millimar N1700 DLL 1.02.14/Win64/N1700_64.dll",
        "Millimar--N1700--SW-2024-07-31/Millimar N1700 DLL 1.02.14/Win32/N1700.dll",
        # Mahr default install locations
        "C:/Program Files/Mahr/Millimar N1700/N1700_64.dll",
        "C:/Program Files (x86)/Mahr/Millimar N1700/N1700.dll",
        # Current directory
        "N1700_64.dll",
        "N1700.dll",
    ]
    
    def __init__(self, dll_path: str = None):
        """
        Initialize the N1700 wrapper.
        
        Args:
            dll_path: Path to N1700.dll (optional, will search default locations)
        """
        import sys
        
        self._dll = None
        self._initialized = False
        self._continuous_active = False
        self._num_modules = 0
        self._num_channels = 0
        
        # Callback storage (prevent garbage collection)
        self._data_callback = None
        self._data_callback_raw = None
        self._msg_callback = None
        self._user_callback = None
        
        # Auto-detect 64-bit
        self._use_64bit = sys.maxsize > 2**32
        
        if dll_path:
            self._dll_path = Path(dll_path)
        else:
            self._dll_path = self._find_dll()
        
        self._load_dll()
    
    def _find_dll(self) -> Path:
        """Search for the DLL in default locations."""
        import os
        
        # Filter paths based on architecture
        suffix = "_64.dll" if self._use_64bit else ".dll"
        
        for path_str in self.DEFAULT_DLL_PATHS:
            # Skip wrong architecture
            if self._use_64bit and "Win32" in path_str:
                continue
            if not self._use_64bit and "Win64" in path_str:
                continue
            if not path_str.endswith(suffix) and "_64" not in path_str:
                continue
                
            path = Path(path_str)
            if path.exists():
                return path
        
        # Fallback to just the DLL name (let Windows find it)
        return Path("N1700_64.dll" if self._use_64bit else "N1700.dll")
    
    def _load_dll(self):
        """Load the N1700 DLL."""
        try:
            self._dll = ctypes.WinDLL(str(self._dll_path))
        except OSError as e:
            raise N1700Exception(-1, f"Failed to load DLL: {e}")
        
        self._setup_functions()
    
    def _setup_functions(self):
        """Setup function signatures for the DLL."""
        
        # --- Initialization ---
        self._dll.N1700InitializeLibrary.argtypes = [c_bool, POINTER(c_uint), POINTER(c_uint), c_int]
        self._dll.N1700InitializeLibrary.restype = c_int
        
        self._dll.N1700FreeLibrary.argtypes = []
        self._dll.N1700FreeLibrary.restype = c_int
        
        self._dll.N1700Refresh.argtypes = [POINTER(c_uint), POINTER(c_uint)]
        self._dll.N1700Refresh.restype = c_int
        
        # --- Module/Channel Info ---
        self._dll.N1700GetNumModules.argtypes = []
        self._dll.N1700GetNumModules.restype = c_int
        
        self._dll.N1700GetNumChannels.argtypes = []
        self._dll.N1700GetNumChannels.restype = c_int
        
        self._dll.N1700GetModule.argtypes = [c_uint, POINTER(sN1700_Module)]
        self._dll.N1700GetModule.restype = c_int
        
        self._dll.N1700GetChannel.argtypes = [c_uint, POINTER(sN1700_Channel)]
        self._dll.N1700GetChannel.restype = c_int
        
        self._dll.N1700GetVersion.argtypes = [POINTER(N1700Version)]
        self._dll.N1700GetVersion.restype = c_int
        
        # --- Polling ---
        self._dll.N1700PollData.argtypes = [c_uint, POINTER(c_double)]
        self._dll.N1700PollData.restype = c_int
        
        # --- Continuous Mode ---
        self._dll.N1700StartContinuousRequestAllData.argtypes = [c_uint, c_int]
        self._dll.N1700StartContinuousRequestAllData.restype = c_int
        
        self._dll.N1700StopContinuousRequestAllData.argtypes = []
        self._dll.N1700StopContinuousRequestAllData.restype = c_int
        
        self._dll.N1700RegisterDataCallback.argtypes = [DATA_CALLBACK_TYPE, c_int, POINTER(c_int), c_void_p]
        self._dll.N1700RegisterDataCallback.restype = c_int
        
        self._dll.N1700UnregisterDataCallback.argtypes = [DATA_CALLBACK_TYPE]
        self._dll.N1700UnregisterDataCallback.restype = c_int
        
        # --- Filter ---
        self._dll.N1700GetFilter.argtypes = [c_uint, POINTER(c_int)]
        self._dll.N1700GetFilter.restype = c_int
        
        self._dll.N1700SetFilter.argtypes = [c_uint, c_int]
        self._dll.N1700SetFilter.restype = c_int
        
        # --- LED Control ---
        self._dll.N1700SetLED.argtypes = [c_uint, c_byte]
        self._dll.N1700SetLED.restype = c_int
        
        self._dll.N1700GetLED.argtypes = [c_uint, POINTER(c_byte)]
        self._dll.N1700GetLED.restype = c_int
        
        # --- Decimals ---
        self._dll.N1700SetDecimals.argtypes = [c_uint, c_int]
        self._dll.N1700SetDecimals.restype = c_int
        
        # --- Calibration ---
        self._dll.N1700GetCalibration.argtypes = [c_uint, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        self._dll.N1700GetCalibration.restype = c_int
        
        self._dll.N1700SetOffsetMM.argtypes = [c_uint, c_float]
        self._dll.N1700SetOffsetMM.restype = c_int
        
        # --- Customer Calibration ---
        self._dll.N1700GetCustomerCalibration.argtypes = [
            c_uint, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_bool)
        ]
        self._dll.N1700GetCustomerCalibration.restype = c_int
        
        self._dll.N1700ActivateCustomerCalibration.argtypes = [c_uint, c_bool]
        self._dll.N1700ActivateCustomerCalibration.restype = c_int
    
    def _check_result(self, result: int, operation: str = ""):
        """Check the result code and raise exception if error."""
        if result != N1700Error.SUCCESS:
            raise N1700Exception(result, f"{operation} failed with code {result}")
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
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
        if self._continuous_active:
            self.stop_continuous()
        
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
    
    def get_version(self) -> dict:
        """Get DLL version information."""
        version = N1700Version()
        result = self._dll.N1700GetVersion(byref(version))
        self._check_result(result, "GetVersion")
        
        return {
            "n1700": f"{version.N1700lib_major}.{version.N1700lib_minor}.{version.N1700lib_micro}.{version.N1700lib_nano}",
            "ftdi": f"{version.FTDIlib_major}.{version.FTDIlib_minor}.{version.FTDIlib_micro}.{version.FTDIlib_nano}",
        }
    
    # =========================================================================
    # MODULE/CHANNEL INFO
    # =========================================================================
    
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
            "filter": channel.DigFilter,
            "customer_calib_active": bool(channel.CustomerCalibActive),
            "customer_calibrated": bool(channel.CustomerCalibrated),
            "factory_calibrated": bool(channel.FactoryCalibrated),
        }
    
    # =========================================================================
    # POLLING MODE
    # =========================================================================
    
    def poll_data(self, channel_idx: int) -> float:
        """
        Read measurement value from a channel (polling mode).
        
        For fast measurement, use start_continuous() instead.
        
        Args:
            channel_idx: Channel index (0 to num_channels-1)
            
        Returns:
            Measurement value in mm
        """
        if self._continuous_active:
            raise N1700Exception(
                N1700Error.CONTINUOUS_ACTIVE,
                "Cannot poll while continuous mode is active. Call stop_continuous() first."
            )
        
        data = c_double()
        result = self._dll.N1700PollData(channel_idx, byref(data))
        self._check_result(result, f"PollData({channel_idx})")
        
        return data.value
    
    def poll_all(self) -> Dict[int, float]:
        """
        Poll all channels and return dict of {channel_idx: value}.
        
        For fast measurement, use start_continuous() instead.
        """
        if self._continuous_active:
            raise N1700Exception(
                N1700Error.CONTINUOUS_ACTIVE,
                "Cannot poll while continuous mode is active."
            )
        
        results = {}
        for i in range(self._num_channels):
            try:
                results[i] = self.poll_data(i)
            except N1700Exception:
                results[i] = None
        return results
    
    # =========================================================================
    # CONTINUOUS MODE
    # =========================================================================
    
    def start_continuous(
        self,
        callback: Callable[[Dict[int, float]], None],
        channels: Optional[List[int]] = None
    ):
        """
        Start continuous data acquisition (recommended for fast measurement).
        
        Data is pushed to your callback as fast as the hardware allows.
        All channels are read simultaneously.
        
        Args:
            callback: Function called with dict of {channel_idx: value}
            channels: Optional list of channel indices to monitor (default: all)
        
        Example:
            def on_data(channel_data):
                for ch, value in channel_data.items():
                    print(f"CH {ch}: {value:.4f} mm")
            
            gauge.start_continuous(callback=on_data)
        """
        if self._continuous_active:
            raise N1700Exception(
                N1700Error.CONTINUOUS_ACTIVE,
                "Continuous mode already active. Call stop_continuous() first."
            )
        
        # Determine which channels to monitor
        if channels is None:
            channels = list(range(self._num_channels))
        
        num_channels = len(channels)
        channel_array = (c_int * num_channels)(*channels)
        
        # Store user callback
        self._user_callback = callback
        
        # Create C callback wrapper
        def c_callback(num_ch: int, p_channel_idx, p_data, p_context) -> int:
            try:
                # Build dict of channel -> value
                channel_data = {}
                for i in range(num_ch):
                    ch_idx = p_channel_idx[i]
                    value = p_data[i]
                    channel_data[ch_idx] = value
                
                # Call user's Python callback
                if self._user_callback:
                    self._user_callback(channel_data)
                
                return 0
            except Exception as e:
                print(f"Callback error: {e}")
                return -1
        
        # Store callback to prevent garbage collection
        self._data_callback = DATA_CALLBACK_TYPE(c_callback)
        
        # Register callback
        result = self._dll.N1700RegisterDataCallback(
            self._data_callback,
            num_channels,
            channel_array,
            None  # pContext
        )
        self._check_result(result, "RegisterDataCallback")
        
        # Start continuous mode
        result = self._dll.N1700StartContinuousRequestAllData(0, 0)
        self._check_result(result, "StartContinuousRequestAllData")
        
        self._continuous_active = True
    
    def stop_continuous(self):
        """Stop continuous data acquisition."""
        if not self._continuous_active:
            return
        
        # Stop continuous mode
        result = self._dll.N1700StopContinuousRequestAllData()
        self._check_result(result, "StopContinuousRequestAllData")
        
        # Unregister callback
        if self._data_callback:
            self._dll.N1700UnregisterDataCallback(self._data_callback)
            self._data_callback = None
        
        self._user_callback = None
        self._continuous_active = False
    
    @property
    def is_continuous(self) -> bool:
        """Check if continuous mode is active."""
        return self._continuous_active
    
    # =========================================================================
    # FILTER CONTROL
    # =========================================================================
    
    def get_filter(self, channel_idx: int) -> int:
        """
        Get the digital averaging filter level for a channel.
        
        Args:
            channel_idx: Channel index (0 to num_channels-1)
            
        Returns:
            Filter level (0-6). See FilterLevel enum.
        """
        filter_val = c_int()
        result = self._dll.N1700GetFilter(channel_idx, byref(filter_val))
        self._check_result(result, f"GetFilter({channel_idx})")
        return filter_val.value
    
    def set_filter(self, channel_idx: int, level: int):
        """
        Set the digital averaging filter level for a channel.
        
        Higher values = more averaging = smoother but slower response.
        Lower values = less averaging = noisier but faster response.
        
        Args:
            channel_idx: Channel index (0 to num_channels-1)
            level: Filter level (0-6)
                0 = Off (no averaging)
                1 = 2 samples
                2 = 4 samples
                3 = 8 samples
                4 = 16 samples
                5 = 32 samples (default)
                6 = 64 samples
        """
        if level < 0 or level > 6:
            raise ValueError("Filter level must be 0-6")
        
        result = self._dll.N1700SetFilter(channel_idx, level)
        self._check_result(result, f"SetFilter({channel_idx}, {level})")
    
    def set_filter_all(self, level: int):
        """Set filter level for all channels."""
        for i in range(self._num_channels):
            self.set_filter(i, level)
    
    # =========================================================================
    # LED CONTROL
    # =========================================================================
    
    def get_led(self, channel_idx: int) -> LedState:
        """Get LED state for a channel."""
        state = c_byte()
        result = self._dll.N1700GetLED(channel_idx, byref(state))
        self._check_result(result, f"GetLED({channel_idx})")
        return LedState(state.value)
    
    def set_led(self, channel_idx: int, state: LedState):
        """
        Set LED state for a channel.
        
        Args:
            channel_idx: Channel index
            state: LedState.OFF, ON, BLOCKED, or UNBLOCKED
        """
        result = self._dll.N1700SetLED(channel_idx, state.value)
        self._check_result(result, f"SetLED({channel_idx}, {state})")
    
    # =========================================================================
    # DECIMALS
    # =========================================================================
    
    def set_decimals(self, channel_idx: int, decimals: int):
        """
        Set the number of decimal places for a channel.
        
        This is for display purposes only; does not affect actual measurement.
        """
        result = self._dll.N1700SetDecimals(channel_idx, decimals)
        self._check_result(result, f"SetDecimals({channel_idx}, {decimals})")
    
    # =========================================================================
    # CALIBRATION
    # =========================================================================
    
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
    
    def get_customer_calibration(self, channel_idx: int) -> dict:
        """
        Get customer calibration parameters for a channel.
        
        Returns:
            Dictionary with offset_mm, digits_to_mm, gain, is_active
        """
        offset = c_float()
        digits_to_mm = c_float()
        gain = c_float()
        is_active = c_bool()
        
        result = self._dll.N1700GetCustomerCalibration(
            channel_idx,
            byref(offset),
            byref(digits_to_mm),
            byref(gain),
            byref(is_active)
        )
        self._check_result(result, f"GetCustomerCalibration({channel_idx})")
        
        return {
            "offset_mm": offset.value,
            "digits_to_mm": digits_to_mm.value,
            "gain": gain.value,
            "is_active": is_active.value,
        }
    
    def activate_customer_calibration(self, channel_idx: int, activate: bool = True):
        """
        Toggle between customer and factory calibration.
        
        Args:
            channel_idx: Channel index
            activate: True for customer calibration, False for factory
        """
        result = self._dll.N1700ActivateCustomerCalibration(channel_idx, activate)
        self._check_result(result, f"ActivateCustomerCalibration({channel_idx}, {activate})")
    
    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import time
    
    print("=== N1700 Test ===\n")
    
    with N1700() as gauge:
        # Show version
        version = gauge.get_version()
        print(f"DLL Version: {version['n1700']}")
        print(f"FTDI Version: {version['ftdi']}")
        print(f"Modules: {gauge.get_num_modules()}")
        print(f"Channels: {gauge.get_num_channels()}\n")
        
        # Show channel info
        for i in range(gauge.get_num_channels()):
            ch = gauge.get_channel(i)
            print(f"Channel {i}: filter={ch['filter']}, type={ch['port_type'].name}")
        
        print("\n--- Polling Mode ---")
        for i in range(gauge.get_num_channels()):
            value = gauge.poll_data(i)
            print(f"Channel {i}: {value:.6f} mm")
        
        print("\n--- Setting Filter to Fast (level 2) ---")
        gauge.set_filter_all(FilterLevel.AVG_4)
        
        print("\n--- Continuous Mode (5 seconds) ---")
        readings = []
        
        def on_data(channel_data):
            readings.append(channel_data)
            # Print first channel
            if 0 in channel_data:
                print(f"CH 0: {channel_data[0]:.6f} mm", end='\r')
        
        gauge.start_continuous(callback=on_data)
        time.sleep(5)
        gauge.stop_continuous()
        
        print(f"\nReceived {len(readings)} readings in 5 seconds")
        print(f"Rate: {len(readings) / 5:.1f} Hz")