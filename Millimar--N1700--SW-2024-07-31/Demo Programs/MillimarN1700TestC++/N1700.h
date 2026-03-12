//------------------------------------------------------------------------------
// N1700.H 14.04.2021
// Calls and Messages for N1700.dll
//------------------------------------------------------------------------------
// 2021.04.14: Extended DataCallback
// 2021.03.31: Enhancements for N 1702 VSS
// 2020.11.11: Added functionality for N 1702 VSS
// 2020.04.02: Changed Datatypes of OffsetMM, digitsToMM, and gain from double to float (Onyl in Header)
// 2018.12.10: For DLL 1.01-23, Position of mtN1702M_HR at End of tModuleType
// 2018.11.27: For DLL 1.01-20, Added N1700SetLED, Changed N1700SetLED (Param state)
// 2018.10.08: For DLL 1.01-17, Added tModuleType mtN1702M_HR
// 2018.06.14: For DLL 1.01-15, Added N1700PollData
// 2017.12.07: For DLL 1.01-xx, changes for PE-Module, see 20171207
//------------------------------------------------------------------------------
#if !defined(N1700_H)
#define N1700_H

//#include "types.h"
typedef char I16;
typedef int I32;
typedef unsigned short UI16;
typedef unsigned int UI32;
typedef BYTE byte;

#define NO_VAL  -999999999

// Return codes
#define N1700_SUCCESS  0
#define N1700_FAILURE  -1
#define N1700_TIMEOUT  -2
#define N1700_INVALID_DEVNO -3
#define N1700_NO_MODULES -4
#define N1700_FILENOTEXISTS -5
#define N1700_WRONGFILEFORMAT -6
#define N1700_NOTYETSUPPORTED -7
#define N1700_INVALID_CHANNELIDX -8
#define N1700_CONTINUOUS_ACTIVE -9
#define N1700_CALL_STILL_IN_ACTION -10
#define N1700_WRONG_MODULETYPE -11
#define N1700_FILEVARIANTNOTEXISTS -12


//#define WM_USER  0x00000400

// Messages
#define WM_N1700_Tick  WM_USER + 2000 + 1
#define WM_N1700_ModuleCountChanged  WM_USER + 2000 + 2
#define WM_N1700_ChannelCountChanged  WM_USER + 2000 + 3
#define WM_N1700_NewMeasVal  WM_USER + 2000 + 4
#define WM_N1700_SendDataCallbacks  WM_USER + 2000 + 5
#define WM_N1700_MwProSek  WM_USER + 2000 + 6
#define WM_N1700_Switch  WM_USER + 2000 + 7
#define WM_N1700_Communication  WM_USER + 2000 + 8
#define WM_N1700_FirmwareUpdateProgress  WM_USER + 2000 + 9 // Param = Progress in 1/10 %
#define WM_N1700_FirmwareUpdateError  WM_USER + 2000 + 10 // Param = Progress in
#define WM_N1700_Debug  WM_USER + 2000 + 11
#define WM_N1700_ChannelMwProSek  WM_USER + 2000 + 12
#define WM_N1700_ChannelParChanged  WM_USER + 2000 + 13
#define WM_N1700_Error  WM_USER + 2000 + 14
#define WM_N1700_ErrorFlashInfo WM_USER + 2000 + 15
#define WM_N1700_AutoReset WM_USER + 2000 + 16
#define WM_N1700_PhaseCorrTimeoutSecs WM_USER + 2000 + 17
#define WM_N1700_PhaseCorrValue WM_USER + 2000 + 18
#define WM_N1700_RefStat WM_USER + 2000 + 19 // 1: RefStat Ok, 0: RefStat Not Ok

enum tModuleType : byte
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

enum tPortType : byte
{
	ptNone,
	ptAnalog,
	ptDigital,
	ptIncr
};

enum tLedState : byte
{
   lsOff,
   lsOn,
   lsBlocked,
   lsUnblocked
};

enum tDataValueType : byte
{
   dvtDigital,
   dvtPosition,
   dvtVelocity,
   dvtTurn
};

#define MaxChannelCnt  4


typedef struct sN1700_Module { // Call of function N1700GetModule fills this struct
	UI32  ModuleIdx; // The Id of the Modul, sequence number

	byte sFtDescription[40]; // For internal use

	byte sFtSerial[12]; // For internal use

	tModuleType ModuleType; // Type of Module

	byte sModuleType[24]; // Type of Module as string // 20171207 New Size

	byte sDescription[24]; // Name of Module as string, same as sModuleType // 20171207 New Size

	byte sIdentNo[8]; // Ident Number of Module

	byte sSerialNo[9]; // Serial Number of Module

	byte sFirmwareVersion[10];  // Firmware Version number of Module

	byte ChannelCount; // Count of Channels the module has

	byte PowerModuleNeeded; // If TRUE (1), there is a Power Module needed at position before this Module

	short int  PowerConsumption_mA; // Power Consumption of Module, negative if Consumption, positiv if Supply (USB-Modul, Power Module)

	UI32 ChannelIdxArray[4]; // The Ids of the Channels included
};

struct sN1700_Channel { // Call of function N1700GetChannel fills this struct
	UI32 ChannelIdx; // The Id of the Channel
	UI32 ParentModuleIdx; // The Id of the Parent Module for accessing the Module-Parameters

	tPortType tPortType; // Type of Channel-Port (ptAnalog, ptDigital)

	byte PortInCount; // Count of Input Ports

	byte PortOutCount; // Count of Output Ports

	int Decimals; // Count of decimals for PortType ptAnalog. Can be Changed with Call of N1700SetDecimal

	UI32 DigFilter; // 20171207 New
	byte CustomerCalibActive; // 20171207 New

	byte CustomerCalibrated; // 20171207 New
	byte FactoryCalibrated; // 20171207 New
}; // N1700_Channel, *PN1700_Channel;

struct sN1700_ChannelExtData { // for ExtDataCallback
	UI32    ChannelIdx;
	tDataValueType  ValueType;
	byte Reserve1[3];
	double  dValue;
	//        if Channel is an N 1704 I/O or N 17001 USB, the float value has to be converted to uint32,
	//        the low  2 bytes are the digital outputs(Bit 0x0000 0001 ist Port 1, Bit 0x0000 0002 ist Port 2...
	//        the high 2 bytes are the digital inputs (Bit 0x0001 0000 ist Port 1, Bit 0x0002 0000 ist Port 2...

	byte 	ReferenceActive;
	byte  	Referenced;

	byte Reserve2[14];
};

struct sN1700_CnfVSS {
	  bool PhasenCorrOn;
	  bool PhasenCorrOk;
	  byte PhaseCorrDeg10Value; // 10tel Grad, ein Byte, ReadOnly
	  bool RotaryNotLinear;

	  byte IPolFaktIdx;
	  bool PosAndVel; // Position and Velocity
	  bool RefActive;
	  bool RefStatOk;

	  bool MultiTurn;
	  bool FilterOn;
	  byte FilterFreqIdx;  // Grenzfrequenz, cutoff
	  byte Reserve1; // 1

	  UI32 PerLenOrIncPR; // Periodenlänge oder Inkremente pro Umdrehung
	  UI32 DistanceRefMarkers;
	  byte Reserve2[16]; // Sum 32 Bytes
};

typedef int(__stdcall *F_N1700DataCallback)(
	int numChannels,
	int *pChannelIdxArray,  // Channels in Low byte, and Additional Information, if Context = 1
	double* pData,
	void* pContext);
// numChannels: Count of Channels, from which Data is sended
// pChannelIdxArray: Array with Channel-Ids in Low word (32 bit), from which Data is sendet, and Additional Information in high word (32 bit), if Context > 0
//					 if bit 0x10 in Context is set, Data is Velocity, if Bit 0x100000 in pChannelIdxArray is set
//					 if bit 0x20 in Context is set, Data is Multiturn-Value, if Bit 0x200000 in pChannelIdxArray is set
//					 if bit 0x01 in Context is set, Reference detection is active, if Bit 0x10000 in pChannelIdxArray is set
//					 if bit 0x02 in Context is set, Position Value of Channel is referenced, if Bit 0x20000 in pChannelIdxArray is set
// pdata: pointer to float array with meausring data
//        if Channel is an N 1704 I/O, the float value has to be converted to uint32,
//        the low  2 bytes are the digital outputs(Bit 0x0000 0001 ist Port 1, Bit 0x0000 0002 ist Port 2...
//        the high 2 bytes are the digital inputs (Bit 0x0001 0000 ist Port 1, Bit 0x0002 0000 ist Port 2...

typedef int(__stdcall *F_N1700ExtDataCallback)(
	int numData, 
	sN1700_ChannelExtData* pData,
	void* pContext);
// numData: Count of data-Blocks 
// pdata: pointer to array of sN1700_ChannelExtData

typedef int(__stdcall *F_N1700MsgCallback)(
	int msg,
	UI32 Channel,
	int param);


struct N1700version
{
	struct {
		int major;
		int minor;
		int micro;
		int nano;
	}N1700lib;
	struct {
		int major;
		int minor;
		int micro;
		int nano;
	}FTDIlib;
}; // N1700VERSION, *N1700VERSION;


// Initialize Library and determines connected configuration
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700InitializeLibrary)(BOOL Console, UI32 *NumModules, UI32 *NumChannels, I32 Par);
//------------------------------------------------------------------------------
// Out Parameters:
// NumModules: Count of connected Modules
// NumChannels: Count of all channels in connected Modules

// Initialize Library for use in applications, that connect to other FTDI-Devices
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700InitializeLibraryNoAutoSrch)(BOOL Console, I32 Par);
//------------------------------------------------------------------------------

// Get DeviceCount if FTDI-Count changed when initialized with if N1700InitializeLibraryNoAutoSrch
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetDevices)(UI32 *NumModules, UI32 *NumChannels);
//------------------------------------------------------------------------------
// Out Parameters:
// NumModules: Count of connected Modules
// NumChannels: Count of all channels in connected Modules

// Activate or Deactivate AutoSrch N1700 Devices 
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetAutoSrch)(BOOL AutoSrch);
//------------------------------------------------------------------------------
// In Parameters:
// AutoSrch: true or false

// Close Library
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700FreeLibrary)(void);
//------------------------------------------------------------------------------

// Determine connected configuration again
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700Refresh)(UI32 *NumModules, UI32 *NumChannels);
//------------------------------------------------------------------------------
// Out Parameters:
// NumModules: Count of connected Modules
// NumChannels: Count of all channels in connected Modules

// Get Version
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetVersion)(N1700version *Version); // sN1700version
//------------------------------------------------------------------------------
// Out Parameter:
// Version: Pointer to Version of DLLs in struct N1700version

// Determine count of connected Modules
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetNumModules)(void);
//------------------------------------------------------------------------------
// return value:
// Count of connected Modules

// Determine count of connected Channels
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetNumChannels)(void);
//------------------------------------------------------------------------------
// return value:
// Count of all channels in connected Modules

// Read Informations about Module
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetModule)(UI32 ModuleIdx, sN1700_Module* Module); // sN1700_Module
//------------------------------------------------------------------------------
// In Parameter:
// ModuleIdx: Id of Module, from which Information will be returned (0..ModuleCount-1)
// Out Parameter:
// Module: Pointer to struct sN1700_Module

// Read Informations about Channel
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetChannel)(UI32 ChannelIdx, sN1700_Channel* Channel); // sN1700_Channel;
//------------------------------------------------------------------------------
// In Parameter:
// ChannelIdx: Id of Channel, from which Information will be returned (0..ChannelCount-1)
// Out Parameter:
// Channel: Pointer to struct sN1700_Channel


// Read data-Value from Channel
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700PollData)(UI32 ChannelIdx, double* Data);// Pointer to array of ChannelId
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel, from which Information will be returned (0..ChannelCount-1)
// Out Parameter:
// Data: Pointer to readed Measuring Value

// Request Data of selected Channels
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700RequestData)(int numChannels, UI32* pchannelIdxArray, int par);// Pointer to array of ChannelId
//------------------------------------------------------------------------------
// In Parameters:
// numChannels: Count of Channels, from which will Data be requested
// pChNoArray: Array with Channel-Ids, , from which will Data be requested
// par: for internal use

// Request Data of all Channels
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700RequestAllData)(int par);
//------------------------------------------------------------------------------
// In Parameters:
// par: for internal use

// Start Continuous Request of Data for all Channels
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700StartContinuousRequestAllData)(UI32 interval, int par);
//------------------------------------------------------------------------------
// In Parameter:
// interval: not supported yet, Data will be received as fast as possible
// par: for internal use

// Stop Continuous Request of Data for all Channels
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700StopContinuousRequestAllData)(void);
//------------------------------------------------------------------------------

// Start Continuous Request of Foot Switch
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700StartContinuousRequestFootSwitch)(void);
//------------------------------------------------------------------------------

// Stops Continuous Request of Foot Switch
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700StopContinuousRequestFootSwitch)(void);
//------------------------------------------------------------------------------

// Set Outport Data of Channel of Module "N 1704 I/O"
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetData)(UI32 channelIdx, UI32 data);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel. Must be the Channel of a "N 1704 I/O"-Module
// data: state of Ports bitwise: - Port Out 01: Bit 0 (0x01) (0001 0000)
//                               - Port Out 02: Bit 1 (0002) (0010 0000)
//                               - Port Out 03: Bit 2 (0x04) (0100 0000)
//                               - Port Out 04: Bit 3 (0x08) (1000 0000)
//                               ... and so on

// Set LED of Channel
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetLED)(UI32 channelIdx, tLedState state);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// state: LED State: 0 = OFF, 1 = ON, 2 = BLOCKED, 3 = UNBLOCKED

// Get LED of Channel
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetLED)(UI32 channelIdx, tLedState* state);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// state: LED State: 0 = OFF, 1 = ON, 2 = BLOCKED, 3 = UNBLOCKED

// Set Count of Decimals of Measuring Value. Only for optional use. Count will be saved in struct sN1700_Channel
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetDecimals)(UI32 channelIdx, int decimals);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// decimals: Count of Decimals of Measuring Value

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetCalibration)(UI32 channelIdx, float* OffsetMM, float* digitsToMM, float* gain);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetOffsetMM)(UI32 channelIdx, float offsetMM);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// OffsetMM
// Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetDigitsToMM)(UI32 channelIdx, float digitsToMM);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// digitsToMM
// Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetGain)(UI32 channelIdx, float gain);
//------------------------------------------------------------------------------
// Out Parameters:
// gain
// Measuring Value = ((Indcator Digits / DigitsToMM) - OffsetMM) * Gain

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetFilter)(UI32 channelIdx, int* Filter);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// Filter

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetFilter)(UI32 channelIdx, int Filter);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Filter

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetPeType)(UI32 channelIdx, int* PeType);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// Type of Pe-Module

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetPeType)(UI32 channelIdx, int PeType);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Type of Pe-Module

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetCnfVSS)(UI32 channelIdx, bool ReadNew, sN1700_CnfVSS* CnfVSS);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// ReadNew: Read the saved Configuration from Module. It will be readed automatically while first connection to module
// Out Parameters:
// CnfVSS: Konfiguration of VSS-Module

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700SetCnfVSS)(UI32 channelIdx, sN1700_CnfVSS CnfVSS);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// CnfVSS: Konfiguration of VSS-Module

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700DoResetVSS)(UI32 channelIdx);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel

//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700ActivatePhaseCorrVSS)(UI32 channelIdx);
//------------------------------------------------------------------------------
// In Parameters:
// ChannelIdx: Id of Channel
// Out Parameters:
// PhaseCorr: Phase Correction of VSS-Module

// Register a callback which is called every time new values arrives
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700RegisterDataCallback)(F_N1700DataCallback pCallback, int numChannels, int *pChannelIdxArray, void *pContext);
//------------------------------------------------------------------------------
// In Parameters:
// pCallback: Callback function
// numChannels: Count of Channels, from which will Data be requested
// pChNoArray: Array with Channel-Ids, , from which will Data be requested

// Unregister a callback function
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700UnregisterDataCallback)(F_N1700DataCallback pCallback);
//------------------------------------------------------------------------------
// In Parameters
// pCallback: Callback function

// Register a callback which is called every time new values arrives
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700RegisterExtDataCallback)(F_N1700ExtDataCallback pCallback, int numChannels, int *pChannelIdxArray, void *pContext);
//------------------------------------------------------------------------------
// In Parameters:
// pCallback: Callback function
// numChannels: Count of Channels, from which will Data be requested
// pChNoArray: Array with Channel-Ids, , from which will Data be requested

// Unregister a callback function
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700UnregisterExtDataCallback)(F_N1700ExtDataCallback pCallback);
//------------------------------------------------------------------------------
// In Parameters
// pCallback: Callback function

// Register a callback for receiving Messages from DLL
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700RegisterMsgCallback)(F_N1700MsgCallback pCallback);
//------------------------------------------------------------------------------
// In Parameters
// pCallback: Callback function

// Unregister the Message callback function
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700UnregisterMsgCallback)(void);
//------------------------------------------------------------------------------

// functions for cutomer calibration
//------------------------------------------------------------------------------
typedef int(__stdcall *F_N1700GetCustomerCalibration)(UI32 channelIdx, float* offsetMM, float* digitsToMM, float* gain, bool* isActive);
typedef int(__stdcall *F_N1700CustomerCalibrateChannelStart)(UI32 channelIdx);
typedef int(__stdcall *F_N1700CustomerCalibrateChannelPos)(int calPos, double calValMM, int* calValDigits);
typedef int(__stdcall *F_N1700CustomerCalibrateChannelSave)(void);
typedef int(__stdcall *F_N1700SetCustomerGain)(UI32 channelIdx, float gain);
typedef int(__stdcall *F_N1700ActivateCustomerCalibration)(UI32 channelIdx, bool activate);
typedef int(__stdcall *F_N1700ClearCustomerCalibration)(UI32 channelIdx);
//------------------------------------------------------------------------------


// For test Only
//------------------------------------------------------------------------------
typedef int(__stdcall *N1700StopEngine)(void);
typedef int(__stdcall *N1700ReStartEngine)(void);
typedef int(__stdcall *F_N1700ReadValue)(UI32 channelIdx, double *value);
//------------------------------------------------------------------------------

#endif // !defined(N1700_H)

