//------------------------------------------------------------------------------
// N1700.H 16.11.2020
// Calls and Messages for N1700.dll
//------------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace MillimarN1700LibCSharp
{
    public class N1700Lib
    {
        public const int NO_VAL = -999999999;

        // Return codes 
        public const int N1700_SUCCESS = 0;
        public const int N1700_FAILURE = -1;
        public const int N1700_TIMEOUT = -2;
        public const int N1700_INVALID_DEVNO = -3;
        public const int N1700_NO_MODULES = -4;
        public const int N1700_FILENOTEXISTS = -5;
        public const int N1700_WRONGFILEFORMAT = -6;
        public const int N1700_NOTYETSUPPORTED = -7;
        public const int N1700_INVALID_CHANNELIDX = -8;
        public const int N1700_CONTINUOUS_ACTIVE = -9;
        public const int N1700_CALL_STILL_IN_ACTION = -10;
        public const int N1700_WRONG_MODULETYPE = -11;
        public const int N1700_FILEVARIANTNOTEXISTS = -12;


        public const int WM_USER = 0x00000400;

        // Messages
        public const int WM_N1700_Tick = WM_USER + 2000 + 1;
        public const int WM_N1700_ModuleCountChanged = WM_USER + 2000 + 2;
        public const int WM_N1700_ChannelCountChanged = WM_USER + 2000 + 3;
        public const int WM_N1700_NewMeasVal = WM_USER + 2000 + 4;
        public const int WM_N1700_SendDataCallbacks = WM_USER + 2000 + 5;
        public const int WM_N1700_MwProSek = WM_USER + 2000 + 6;
        public const int WM_N1700_Switch = WM_USER + 2000 + 7;
        public const int WM_N1700_Communication = WM_USER + 2000 + 8;
        public const int WM_N1700_FirmwareUpdateProgress = WM_USER + 2000 + 9; // Param = Progress in 1/10 %
        public const int WM_N1700_FirmwareUpdateError = WM_USER + 2000 + 10; // Param = Progress in 
        public const int WM_N1700_Debug = WM_USER + 2000 + 11;
        public const int WM_N1700_ChannelMwProSek = WM_USER + 2000 + 12;
        public const int WM_N1700_ChannelParChanged = WM_USER + 2000 + 13;
        public const int WM_N1700_Error = WM_USER + 2000 + 14;
        public const int WM_N1700_ErrorFlashInfo = WM_USER + 2000 + 15;
        public const int WM_N1700_AutoReset = WM_USER + 2000 + 16;
        public const int WM_N1700_PhaseCorrTimeoutSecs = WM_USER + 2000 + 17;
        public const int WM_N1700_PhaseCorrValue = WM_USER + 2000 + 18;


        public enum tModuleType : byte
        {
            mtUNDEF,
            mtPOWER,
            mtTERMINATION,
            mtN1701USB,
            mtN1702M,
            mtN1702T,
            mtN1702U,
            mtN1704M,
            mtN1704T,
            mtN1704U,
            mtN1704IO,
            mt1701PMXXXX, // 20171207
            mt1701PM2500, // 20171207
            mt1701PM5000, // 20171207
            mt1701PM10000, // 20171207
            mt1701PF25005000, // 20171207
            mt1701PF25005000_4, // 20171207
            mt1701PF10000, // 20171207
            mtN1702M_HR, // 20181210
            mtN1702VSS // 20201111
        };

        public enum tPortType : byte
        {
            ptNone,
            ptAnalog,
            ptDigital,
            ptIncr
        };

        public enum tDataValueType : byte
        {
            dvtDigital,
            dvtPosition,
            dvtVelocity,
            dvtTurn
        };

        private static readonly HashSet<tModuleType> ModuleTypeIndicator
            = new HashSet<tModuleType>
        {
            tModuleType.mtN1702M,
            tModuleType.mtN1702T,
            tModuleType.mtN1702U,
            tModuleType.mtN1704M,
            tModuleType.mtN1704T,
            tModuleType.mtN1704U
        };

        public const int MaxChannelCnt = 4;

        public const string sPowerIdentNo = "5331133";

        public struct sN1700_Module // Call of function N1700GetModule fills this struct
        {
            public uint ModuleIdx; // The Id of the Modul, sequence number

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 40)]
            public byte[] sFtDescription; // For internal use

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 12)]
            public byte[] sFtSerial; // For internal use

            public tModuleType ModuleType; // Type of Module

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 24)]
            public byte[] sModuleType; // Type of Module as string

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 24)]
            public byte[] sDescription; // Name of Module as string (same as sModuleType)

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
            public byte[] sIdentNo; // Ident Number of Module

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
            public byte[] sSerialNo; // Serial Number of Module

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
            public byte[] sFirmwareVersion; // Firmware Version number of Module

            public byte ChannelCount; // Count of Channels the module has

            public byte PowerModuleNeeded; // If TRUE (1), there is a Power Module needed at position before this Module

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
            public uint[] ChannelIdxArray; // The Ids of the Channels included

        };

        public struct sN1700_Channel // Call of function N1700GetChannel fills this struct
        {
            public uint ChannelIdx; // The Id of the Channel

            public uint ParentModuleIdx; // The Id of the Parent Module for accessing the Module-Parameters

            public tPortType tPortType; // Type of Channel-Port (ptAnalog, ptDigital)

            public byte PortInCount; // Count of Input Ports

            public byte PortOutCount; // Count of Output Ports

            public byte Decimals; // Count of decimals for PortType ptAnalog. Can be Changed with Call of N1700SetDecimal

            public uint DigFilter;

            public byte CustomerCalibActive;
            public byte CustomerCalibrated;
            public byte FactoryCalibrated;
            public byte Reserve;

        }; // N1700_Channel, *PN1700_Channel;

        public struct sN1700_ChannelExtData { // for ExtDataCallback
	        public uint    ChannelIdx;
            public tDataValueType ValueType;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
	        public byte[] Reserve1;
            public double dValue;
	        //        if Channel is an N 1704 I/O or N 17001 USB, the float value has to be converted to uint32,
	        //        the low  2 bytes are the digital outputs(Bit 0x0000 0001 ist Port 1, Bit 0x0000 0002 ist Port 2...
	        //        the high 2 bytes are the digital inputs (Bit 0x0001 0000 ist Port 1, Bit 0x0002 0000 ist Port 2...

            public byte ReferenceActive;
            public byte Referenced;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 14)]
	        public byte[] Reserve2;
        };

        public struct sN1700_CnfVSS 
        {
            public byte PhasenCorrOn; // bool is 4-Byte in C#, so we'll use byte
            public byte PhasenCorrOk;
            public byte PhaseCorrDeg10Value; // 10tel Grad, ein Byte, ReadOnly
            public byte RotaryNotLinear;

            public byte IPolFaktIdx;
            public byte PosAndVel; // Position and Velocity
            public byte RefActive;
            public byte RefStatOk;
            
            public byte MultiTurn;
            public byte FilterOn;
            public byte FilterFreqIdx;  // Grenzfrequenz, cutoff
            public byte Reserve1; // 12
            public uint PerLenOrIncPR; // Periodenlänge oder Inkremente pro Umdrehung
            public uint DistanceRefMarkers;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
            public byte[] Reserve2; // Sum 32 Bytes
        };

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate void N1700DataCallback(int numChannels, IntPtr pChannelIdxArray, IntPtr pData, IntPtr context);
        // numChannels: Count of Channels, from which will Data is sended
        // pChannelIdxArray: Array with Channel-Ids, from which will Data is received
        // pData: pointer to float array with meausring data
        //        if Channel is an N 1704 I/O, the float value has to be converted to uint32, 
        //        the low  2 bytes are the digital outputs (Bit 0x0000 0001 ist Port 1, Bit 0x0000 0002 ist Port 2...
        //        the high 2 bytes are the digital inputs  (Bit 0x0001 0000 ist Port 1, Bit 0x0002 0000 ist Port 2...


        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate void N1700ExtDataCallback(int numData, IntPtr pData, IntPtr context);
        // numData: Count of Datablocks
        // pData: pointer to array of sN1700_ChannelExtData
        //        if Channel is an N 1704 I/O, the float value has to be converted to uint32, 
        //        the low  2 bytes are the digital outputs (Bit 0x0000 0001 ist Port 1, Bit 0x0000 0002 ist Port 2...
        //        the high 2 bytes are the digital inputs  (Bit 0x0001 0000 ist Port 1, Bit 0x0002 0000 ist Port 2...


        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate void N1700MsgCallback(int msg, uint channel, int param);


        public struct libVersion
        {
            public int major;
            public int minor;
            public int micro;
            public int nano;
        };

        // Library and driver version
        public struct N1700version
        {
            public libVersion N1700lib;
            public libVersion FTDIlib;
        }

#if WIN64    
        const string DLLName = "N1700_64.dll";
#else
        const string DLLName = "N1700.dll";
#endif

        // Initialize Library and determines connected configuration
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700InitializeLibrary(bool Console, out uint NumModules, out uint NumChannels, int Par);
        // Out Parameters:
        // NumModule: Count of connected Modules
        // NumModule: Count of all channels in connected Modules

        // Close Library
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700FreeLibrary();

        // Initialize Library for use in applications, that connect to other FTDI-Devices
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700InitializeLibraryNoAutoSrch(bool Console, Int32 Par);

        // Get DeviceCount if FTDI-Count changed when initialized with if N1700InitializeLibraryNoAutoSrch
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetDevices(out uint NumModules, out uint NumChannels);
        // Out Parameters:
        // NumModules: Count of connected Modules
        // NumChannels: Count of all channels in connected Modules

        // Activate or Deactivate AutoSrch N1700 Devices 
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetAutoSrch(bool AutoSrch);
        // In Parameters:
        // AutoSrch: true or false

        // Determine connected configuration again
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700Refresh(out uint NumModules, out uint NumChannels);
        // Out Parameters:
        // NumModule: Count of connected Modules
        // NumModule: Count of all channels in connected Modules

        // Get Version
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetVersion(IntPtr Version); // sN1700version
        // Out Parameter:
        // Version: Pointer to Version of DLLs in struct N1700version

        // Determine count of connected Modules
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetNumModules();
        // return value:
        // Count of connected Modules

        // Determine count of connected Channels
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetNumChannels();
        // return value:
        // Count of all channels in connected Modules

        // Read Informations about Module
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetModule(uint ModuleIdx, IntPtr Module); // sN1700_Module
        // In Parameter:
        // ModuleIdx: Id of Module, from which Information will be returned (0..ModuleCount-1)
        // Out Parameter:
        // Module: Pointer to struct sN1700_Module

        // Read Informations about Channel
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetChannel(uint ChannelIdx, IntPtr Channel); // sN1700_Channel;
        // In Parameter:
        // ChannelIdx: Id of Channel, from which Information will be returned (0..ChannelCount-1)
        // Out Parameter:
        // Channel: Pointer to struct sN1700_Channel

        // Read data-Value from Channel
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700PollData(uint ChannelIdx, out double data); // sN1700_Channel;
        // In Parameters:
        // ChannelIdx: Id of Channel, from which Information will be returned (0..ChannelCount-1)
        // Out Parameter:
        // Data: Pointer to readed Measuring Value

        // Request Data of selected Channels
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RequestData(int numChannels, IntPtr pchannelIdxArray, int par);// Pointer to array of ChannelId
        // In Parameters:
        // numChannels: Count of Channels, from which will Data be requested
        // pChannelIdxArray: Array with Channel-Ids, , from which will Data be requested
        // par: for internal use


        // Request Data of all Channels
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RequestAllData(int par);
        // In Parameters:
        // par: for internal use

        // Start Continuous Request of Data for all Channels
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StartContinuousRequestAllData(uint interval, int par);
        // In Parameter:
        // interval: not supported yet, Data will be received as fast as possible
        // par: for internal use

        // Stop Continuous Request of Data for all Channels
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StopContinuousRequestAllData();

        // Start Continuous Request of Foot Switch
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StartContinuousRequestFootSwitch();

        // Stops Continuous Request of Foot Switch
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StopContinuousRequestFootSwitch();

        // Set Outport Data of Channel of Module "N 1704 I/O"
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetData(uint channelIdx, uint data);
        // Out Parameters:
        // ChannelIdx: Id of Channel. Must be the Channel of a "N 1704 I/O"-Module  
        // data: state of Ports bitwise: - Port Out 01: Bit 0 (0x01) (0001 0000)
        //                               - Port Out 02: Bit 1 (0002) (0010 0000)
        //                               - Port Out 03: Bit 2 (0x04) (0100 0000)
        //                               - Port Out 04: Bit 3 (0x08) (1000 0000)
        //                               ... and so on   

        // Set LED of Channel 
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetLED(uint channelIdx, bool state);
        // Out Parameters:
        // ChannelIdx: Id of Channel
        // state: LED State: 1 = ON, 0 = OFF

        // Set Count of Decimals of Measuring Value. Only for optional use. Count will be saved in struct sN1700_Channel
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetDecimals(uint channelIdx, char decimals);
        // Out Parameters:
        // ChannelIdx: Id of Channel
        // decimals: Count of Decimals of Measuring Value

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetCalibration(uint channelIdx, out float OffsetMM, out float digitsToMM, out float gain);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetOffsetMM(uint channelIdx, float offsetMM);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Out Parameters:
        // OffsetMM
        // Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetDigitsToMM(uint channelIdx, float digitsToMM);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Out Parameters:
        // digitsToMM
        // Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetGain(uint channelIdx, float gain);
        // Out Parameters:
        // gain
        // Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetFilter(uint channelIdx, out int Filter);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Out Parameters:
        // Filter

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetFilter(uint channelIdx, int Filter);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Filter

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetPeType(uint channelIdx, out int PeType);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Out Parameters:
        // Type of Pe-Module

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetPeType(uint channelIdx, int PeType);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Type of Pe-Module

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetCnfVSS(uint channelIdx, bool ReadNew, IntPtr CnfVSS); // sN1700_CnfVSS
        // In Parameters:
        // ChannelIdx: Id of Channel
        // ReadNew: Read the saved Configuration from Module. It will be readed automatically while first connection to module
        // Out Parameters:
        // CnfVSS: Pointer to struct sN1700_CnfVSS with Konfiguration of VSS-Module

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetCnfVSS(uint channelIdx, sN1700_CnfVSS CnfVSS);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // CnfVSS: Konfiguration of VSS-Module

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700DoResetVSS(uint channelIdx);
        // In Parameters:
        // ChannelIdx: Id of Channel

        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ActivatePhaseCorrVSS(uint channelIdx);
        // In Parameters:
        // ChannelIdx: Id of Channel
        // Out Parameters:
        // PhaseCorr: Phase Correction of VSS-Module


        // Register a callback which is called every time new values arrives
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RegisterDataCallback(N1700DataCallback pCallback, int numChannels, uint[] pChannelIdxArray, IntPtr pContext);
        // In Parameters:   
        // pCallback: Callback function
        // numChannels: Count of Channels, from which will Data be requested
        // pChNoArray: Array with Channel-Ids, , from which will Data be requested
        // pContext

        // Unregister a callback function
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700UnregisterDataCallback(N1700DataCallback pCallback);
        // In Parameters
        // pCallback: Callback function

        // Register a callback which is called every time new values arrives
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RegisterExtDataCallback(N1700ExtDataCallback pCallback, int numChannels, uint[] pChannelIdxArray, IntPtr pContext);
        // In Parameters:   
        // pCallback: Callback function
        // numChannels: Count of Channels, from which will Data be requested
        // pChNoArray: Array with Channel-Ids, , from which will Data be requested
        // pContext

        // Unregister a callback function
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700UnregisterExtDataCallback(N1700ExtDataCallback pCallback);
        // In Parameters
        // pCallback: Callback function

        // Register a callback for receiving Messages from DLL
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RegisterMsgCallback(N1700MsgCallback pCallback);
        // In Parameters
        // pCallback: Callback function

        // Unregister the Message callback function
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700UnregisterMsgCallback();


// functions for cutomer calibration
//------------------------------------------------------------------------------
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetCustomerCalibration(uint channelIdx, ref float fOffsetMM, ref float fDigitsToMM, ref float fGain, ref bool bIsActive);
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetCustomerGain(uint channelIdx, float gain);
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CustomerCalibrateChannelStart(uint channelIdx);
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CustomerCalibrateChannelPos(int calPos, double calValMM, IntPtr calValDigits);
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CustomerCalibrateChannelSave();
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ActivateCustomerCalibration(uint channelIdx, bool activate);
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ClearCustomerCalibration(uint channelIdx);
//------------------------------------------------------------------------------

        // For TEST only...
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern void N1700StopEngine();
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern void N1700ReStartEngine();
        [DllImport(DLLName, CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ReadValue(uint channelIdx, out double value);
    }
}
