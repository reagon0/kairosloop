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
        public const int N1700_SUCCESS                      =  0;
        public const int N1700_FAILURE                      = -1;
        public const int N1700_TIMEOUT                      = -2;
        public const int N1700_INVALID_DEVNO                = -3;
        public const int N1700_NO_MODULES                   = -4;
        public const int N1700_FILENOTEXISTS                = -5;
        public const int N1700_WRONGFILEFORMAT              = -6;

        public const int WM_USER = 0x00000400;

        // Messages
        public const int WM_N1700_Tick                      = WM_USER + 2000 + 1;
        public const int WM_N1700_ModuleCountChanged        = WM_USER + 2000 + 2;
        public const int WM_N1700_ChannelCountChanged       = WM_USER + 2000 + 3;
        public const int WM_N1700_NewMeasVal                = WM_USER + 2000 + 4;
        public const int WM_N1700_SendDataCallbacks         = WM_USER + 2000 + 5;
        public const int WM_N1700_MwProSek                  = WM_USER + 2000 + 6;
        public const int WM_N1700_Switch                    = WM_USER + 2000 + 7;
        public const int WM_N1700_Communication             = WM_USER + 2000 + 8;
        public const int WM_N1700_FirmwareUpdateProgress    = WM_USER + 2000 + 9; // Param = Progress in 1/10 %
        public const int WM_N1700_FirmwareUpdateError       = WM_USER + 2000 + 10; // Param = Progress in 
        public const int WM_N1700_Debug                     = WM_USER + 2000 + 11;

        public enum tModuleType
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
            mtN1704IO
        }
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

        public enum MwlDeviceEnum
        {
            MarWL_dtMarCator1087Ri = 1,
            MarWl_dtMarCator1087BRi = 2,
            MarWl_dtMarCator1086Ri = 3,
            MarWl_dtMarCal16EWRi = 4
        }

        public const int MaxChannelCnt = 4;


        public const string sPowerIdentNo = "5331133";

                    
  
        public struct sN1700_Module {
            public int  ModuleIdx;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 40)]
            public byte[] sFtDescription;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 12)]
            public byte[] sFtSerial;

            public tModuleType ModuleType;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 24)]
            public byte[] sModuleType;

            public bool PowerModuleFollows;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 24)]
            public byte[] sDescription;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
            public byte[] sIdentNo;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
            public byte[] sSerialNo;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
            public byte[] sFirmwareVersion;

            public byte ChannelCount;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
            public byte[] Channel;

        }; 

        public struct sN1700_Channel {
	UI32 ChannelIdx;
	UI32 ParentModuleIdx;

	tPortType tPortType;
	byte PortInCount;
	byte PortOutCount;
	int Decimals;


    ALT -->
            public int ChannelIdx;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 40)]
            public byte[] sFtDescription;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 12)]
            public byte[] sFtSerial;

            public tModuleType ModuleType;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
            public byte[] sModuleType;

            public bool PowerModuleFollows;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 20)]
            public byte[] sDescription;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
            public byte[] sIdentNo;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
            public byte[] sSerialNo;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
            public byte[] sFirmwareVersion;

            public int Decimals;
        }; // N1700_Channel, *PN1700_Channel;



        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate void N1700DataCallback(int numChannels, int[] deviceIds, double[] data, IntPtr context);

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate void N1700MsgCallback(int msg, int channel, int param);

        // Library and driver version
        public struct sN1700version
        {
            public struct sN1700lib
            {
                public int major;
                public int minor;
                public int micro;
                public int nano;
            }
            public struct sftdilib
            {
                public int major;
                public int minor;
                public int micro;
                public int nano;
            }
        }

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700InitializeLibrary(out uint NumModules, out uint NumChannels);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700FreeLibrary();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700Refresh(out uint NumModules, out uint NumChannels);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetVersion(IntPtr Version); // sN1700version

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetNumModules();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetNumChannels();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetModule(uint ModuleIdx, IntPtr Module); // sN1700_Module

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700GetChannel(uint ModuleIdx, IntPtr Channel); // sN1700_Channel;

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RequestData(int numChannels, IntPtr pChNoArray, int par);// Pointer to array of ChannelId

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RequestAllData(int par);

//        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
//        public static extern int N1700StartContinuousRequestData(int numChannels, IntPtr pChNoArray, int interval);

//        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
//        public static extern int N1700StopContinuousRequestData(int numChannels, IntPtr pChNoArray);
        
        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StartContinuousRequestAllData(uint interval, int par);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StopContinuousRequestAllData();
         

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StartContinuousRequestFootSwitch();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StopContinuousRequestFootSwitch();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetIOData(uint channelIdx, byte data);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetLED(uint channelIdx, bool state);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetSerialNo(uint channelIdx, byte[] serNoArr);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CalibrateChannelStart(uint channelIdx);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CalibrateChannelPos(int calPos, double calValMM);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700CalibrateChannelSave();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetDecimals(uint channelIdx, int decimals);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700SetGain(uint channelIdx, double gain); 

        // Register a callback which is called every time new values arrive
        // The caller have to make sure that all Channels use the same root hub !
        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RegisterDataCallback(N1700DataCallback pCallback, int numChannels, int[] pChNoArray, IntPtr pContext);

        // Deregister a callback function/data pair
        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700UnregisterDataCallback(N1700DataCallback pCallback);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700RegisterMsgCallback(N1700MsgCallback pCallback);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700UnregisterMsgCallback();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700FirmwareUpdate(int channelIdx, string Filename);

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700StopEngine();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ReStartEngine();

        [DllImport("N1700.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern int N1700ReadValue(int channelIdx, out double value);

  }
}
