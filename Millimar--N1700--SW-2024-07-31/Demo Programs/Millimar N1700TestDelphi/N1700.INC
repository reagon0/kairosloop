//------------------------------------------------------------------------------
// N1700.inc
// Calls and Messages for N1700.dll
// Needs N1700.dll,  FTD2XX.dll
//------------------------------------------------------------------------------
// Versions and Changes:
// 2018.11.27: For DLL 1.01-20, Added N1700SetLED, Changed N1700SetLED (Param state)
// 2018.06.14: For DLL 1.01-15, Added N1700PollData
// 1.00-0: // - First Version
//------------------------------------------------------------------------------
type
  tModuleType       = (mtUNDEF,
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
                       mt1701PMXXXX,
                       mt1701PM2500,
                       mt1701PM5000,
                       mt1701PM10000,
                       mt1701PF25005000,
                       mt1701PF25005000_4,
                       mt1701PF10000,
                       mtN1702M_HR,
                       mtN1702VSS,
                       mtN1702TTL
                       );

  tModuleGroup      = (mgUndef,
                       mgN1701USB,
                       mgN1702M_T_U_MHR,
                       mgN1704M_T_U,
                       mgN1704IO,
                       mgN1701PM_PF,
                       mgN1702VSS,
                       mgN1702TTL
                       );

   tPortType        = (ptNone,
                       ptAnalog,
                       ptDigital,
                       ptIncr
                       );

   tLedState        = (lsOff,
                       lsOn,
                       lsBlocked,
                       lsUnblocked);

var
  ChannelPortType: array[tModuleType] of tPortType
                   = (ptNone,        //  'UNDEF',
                      ptNone,        //  'N 1700 PSmodule1',
                      ptNone,        //  'TERMINATION',
                      ptDigital,     //  'N 1701 USB',
                      ptAnalog,      //  'N 1702 M',
                      ptAnalog,      //  'N 1702 T',
                      ptAnalog,      //  'N 1702 U',
                      ptAnalog,      //  'N 1704 M',
                      ptAnalog,      //  'N 1704 T',
                      ptAnalog,      //  'N 1704 U',
                      ptDigital,     //  'N 1704 I/O',
                      ptAnalog,      //  'N 1701 PM-XXXX',
                      ptAnalog,      //  'N 1701 PM-2500',
                      ptAnalog,      //  'N 1701 PM-5000',
                      ptAnalog,      //  'N 1701 PM-10000',
                      ptAnalog,      //  'N 1701 PF-2500/5000',
                      ptAnalog,      //  'N 1701 PF-2500/5000-4',
                      ptAnalog,      //  'N 1701 PF-10000',
                      ptAnalog,      //  'N 1702 M-HR',
                      ptIncr,        //  'N 1702 Vss',
                      ptIncr         //  'N 1702 TTL',
                      );

  ChannelModulGroup: array[tModuleType] of tModuleGroup
                   = (mgUndef,           //  'UNDEF',
                      mgUndef,           //  'N 1700 PS',
                      mgUndef,           //  'TERMINATION',
                      mgN1701USB,        //  'N 1701 USB',
                      mgN1702M_T_U_MHR,  //  'N 1702 M',
                      mgN1702M_T_U_MHR,  //  'N 1702 T',
                      mgN1702M_T_U_MHR,  //  'N 1702 U',
                      mgN1704M_T_U,      //  'N 1704 M',
                      mgN1704M_T_U,      //  'N 1704 T',
                      mgN1704M_T_U,      //  'N 1704 U',
                      mgN1704IO,         //  'N 1704 I/O',
                      mgN1701PM_PF,      //  'N 1701 PM-XXXX',
                      mgN1701PM_PF,      //  'N 1701 PM-2500',
                      mgN1701PM_PF,      //  'N 1701 PM-5000',
                      mgN1701PM_PF,      //  'N 1701 PM-10000',
                      mgN1701PM_PF,      //  'N 1701 PF-2500/5000',
                      mgN1701PM_PF,      //  'N 1701 PF-2500/5000-4',
                      mgN1701PM_PF,      //  'N 1701 PF-10000',
                      mgN1702M_T_U_MHR,  //  'N 1702 M-HR',
                      mgN1702VSS,        //  'N 1702 Vss',
                      mgN1702TTL         //  'N 1702 TTL',
                      );

  ModuleTypePe : set of tModuleType = [
                       mt1701PMXXXX,
                       mt1701PM2500,
                       mt1701PM5000,
                       mt1701PM10000,
                       mt1701PF25005000,
                       mt1701PF25005000_4,
                       mt1701PF10000
                       ];

  ModuleTypePeDef : set of tModuleType = [
                       mt1701PM2500,
                       mt1701PM5000,
                       mt1701PM10000,
                       mt1701PF25005000,
                       mt1701PF25005000_4,
                       mt1701PF10000
                       ];

   sModuleType: array[tModuleType] of ansistring
                    = ('UNDEF',
                       'N 1700 PS',
                       'TERMINATION',
                       'N 1701 USB',
                       'N 1702 M',
                       'N 1702 T',
                       'N 1702 U',
                       'N 1704 M',
                       'N 1704 T',
                       'N 1704 U',
                       'N 1704 I/O',
                       'N 1701 PM-XXXX',
                       'N 1701 PM-2500',
                       'N 1701 PM-5000',
                       'N 1701 PM-10000',
                       'N 1701 PF-2500/5000',
                       'N 1701 PF-2500/5000-4',
                       'N 1701 PF-10000',
                       'N 1702 M-HR',
                       'N 1702 VSS',
                       'N 1702 TTL'
                       );

   sModuleGroup: array[tModuleGroup] of ansistring
                    = ('',
                       'N 1701 USB',
                       'N 1702 M/T/U/M-HR',
                       'N 1704 M/T/U',
                       'N 1704 I/O',
                       'N 1701 PM/PF',
                       'N 1702 VSS',
                       'N 1702 TTL');

   iFirmwareVariante: array [tModuleGroup] of integer
                    = (-1, // Undef
                       0, // 'N 1701 USB',
                       0, // ''N 1702 M/T/U/M-HR',
                       0, // ''N 1704 M/T/U',
                       0, // ''N 1704 I/O',
                       0, // ''N 1701 PM/PF',
                       1, // ''N 1702 VSS',
                       1); // 'N 1702 TTL');


   sCalIniTxt: array[tModuleType] of ansistring
                    = ('',
                       '',
                       '',
                       '',
                       'M_Cal_mym_',
                       'T_Cal_mym_',
                       'U_Cal_mym_',
                       'M4_Cal_mym_',
                       'T4_Cal_mym_',
                       'U4_Cal_mym_',
                       '',
                       'PM-XXXX_Cal_mym_',
                       'PM-2500_Cal_mym_',
                       'PM-5000_Cal_mym_',
                       'PM-10000_Cal_mym_',
                       'PF-2500/5000_Cal_mym_',
                       'PF-2500/5000-4_Cal_mym_',
                       'PF-10000_Cal_mym_',
                       'M_HR_Cal_mym_',
                       'Vss_Cal_mym_',
                       'TTL_Cal_mym_');

const
   MaxModuleCount = 100;
   MaxChannelCount = 400;
   NO_VAL = -999999999;

// Return codes
   N1700_SUCCESS                      =  0;
   N1700_FAILURE                      = -1;
   N1700_TIMEOUT                      = -2;
   N1700_INVALID_MODULEIDX            = -3;
   N1700_NO_MODULES                   = -4;
   N1700_FILENOTEXISTS                = -5;
   N1700_WRONGFILEFORMAT              = -6;
   N1700_NOTYETSUPPORTED              = -7;
   N1700_INVALID_CHANNELIDX           = -8;
   N1700_CONTINUOUS_ACTIVE            = -9;
   N1700_CALL_STILL_IN_ACTION         = -10;
   N1700_WRONG_MODULETYPE             = -11;
   N1700_FILEVARIANTNOTEXISTS         = -12;

   WM_N1700_Tick                   = WM_USER + 2000 +  1;
   WM_N1700_ModuleCountChanged     = WM_USER + 2000 +  2;
   WM_N1700_ChannelCountChanged    = WM_USER + 2000 +  3;
   WM_N1700_NewMeasVal             = WM_USER + 2000 +  4;
   WM_N1700_SendDataCallbacks      = WM_USER + 2000 +  5;
   WM_N1700_MwProSek               = WM_USER + 2000 +  6;
   WM_N1700_Switch                 = WM_USER + 2000 +  7;
   WM_N1700_Communication          = WM_USER + 2000 +  8;
   WM_N1700_FirmwareUpdateProgress = WM_USER + 2000 +  9; // Param = Progress in 1/10 %
   WM_N1700_FirmwareUpdateError    = WM_USER + 2000 + 10; // Param = Progress in
   WM_N1700_Debug                  = WM_USER + 2000 + 11;
   WM_N1700_ChannelMwProSek        = WM_USER + 2000 + 12;
   WM_N1700_ChannelParChanged      = WM_USER + 2000 + 13;
   WM_N1700_Error                  = WM_USER + 2000 + 14;
   WM_N1700_ErrorFlashInfo         = WM_USER + 2000 + 15;
   WM_N1700_AutoReset              = WM_USER + 2000 + 16;
   WM_N1700_PhaseCorrTimeoutSecs   = WM_USER + 2000 + 17;
   WM_N1700_PhaseCorrValue         = WM_USER + 2000 + 18;

   MaxModuleChannelCnt = 4;

   sPowerIdentNo = '5331133';

   LenSerialNo     = 8;
   LenIdentNo      = 7;
   LenDescription  = 23;
type

   aDescription    = array[0.. LenDescription] of ansichar;
   aSerialNo       = array[0.. LenSerialNo]    of ansichar;
   aIdentNo        = array[0.. LenIdentNo]     of ansichar;
//  aBezeichnung

   rN1700_Module = record
      ModuleIdx                      : dWord;
      sFtDescription                 : array[0..39] of ansichar;
      sFtSerial                      : array[0..11] of ansichar;

//      PowerModuleFollows             : boolean;

      ModuleType                     : tModuleType;
      sModuleType                    : array[0..23] of ansichar;

      sDescription                   : aDescription;
      sIdentNo                       : aIdentNo;
      sSerialNo                      : aSerialNo;
      sFirmwareVersion               : array[0.. 9] of ansichar;

      ChannelCount                   : byte;

      PowerModuleNeeded              : boolean;
      PowerConsumption_mA            : smallint; // Notwendig wegen Ausrichtung der structs in C++ und C#
      
      ChannelIdxArray                : array[0..3] of dWord; // Index of Channel in Group

   end; // N1700_Channel, *PN1700_Channel;

   rN1700_Channel = record
      ChannelIdx                     : dWord;
      ParentModuleIdx                : dWord;

      PortType                       : tPortType;
      PortInCount                    : byte;
      PortOutCount                   : byte;

      Decimals                       : byte;
      DigFilter                      : dWord; // 12
      CustomerCalibActive            : boolean;

      CustomerCalibrated             : boolean;
      FactoryCalibrated              : boolean;
      Reserve                        : boolean;
   end; // N1700_Channel, *PN1700_Channel;

   rN1700_CnfVSS = record
      PhasenCorrOn      : boolean;
      PhasenCorrOk      : boolean;
      PhaseCorrDeg10Value  : shortint; // 10tel Grad, ein Byte, ReadOnly
      RotaryNotLinear   : boolean;

      IPolFaktIdx       : byte;
      PosAndVel         : boolean; // Position and Velocity
      RefActive         : boolean;
      RefStatOk         : boolean;

      MultiTurn         : boolean;
      FilterOn          : boolean;
      FilterFreqIdx     : byte;  // Grenzfrequenz, cutoff
      Reserve1          : byte; // 1

      PerLenOrIncPR     : dWord; // Periodenlänge oder Inkremente pro Umdrehung
      DistanceRefMarkers: dWord;
      Reserve2          : array [0..15] of byte; // In Summe 32 Bytes
   end;


   // if Context (integer) = 1 then pDataDefArr (integer) includes Channel-number in Low byte, and additional Information in higher bytes
   tPFN_N1700_DATA_HANDLER = procedure(numChannels : integer; // Number of Channels
                                     pDataDefArr   : pointer; // Pointer to array of Channels in Low byte, and Additional Information, if Context = 1
                                     pDataArr      : pointer; // Pointer to array of Data
                                     pContext      : pointer); stdcall;
   tPFNO_N1700_DATA_HANDLER = procedure(numChannels: integer; // Number of Channels
                                     pDataDefArr   : pointer; // Pointer to array of Channels in Low byte, and Additional Information, if Context = 1
                                     pDataArr      : pointer; // Pointer to array of DevNo
                                     pContext      : pointer) of object;

   tPFN_N1700_MSG_HANDLER = procedure(Msg: integer; Channel: integer; Param: integer); stdcall;
   tPFNO_N1700_MSG_HANDLER = procedure(Msg: integer; Channel: integer; Param: integer) of object;

   // Library and driver version


   rN1700_VERSION = record
        N1700lib : record
           major       : integer;
           minor       : integer;
           micro       : integer;
           nano        : integer;
        end; // midlib
        ftdilib : record
           major       : integer;
           minor       : integer;
           micro       : integer;
           nano        : integer;
        end; // midlib
   end; // N1700_VERSION, *PN1700_VERSION;

{$ifdef DLLMAIN}
function N1700InitializeLibrary(Console: boolean; var NumModules: dword; var NumChannels: dword; Par: integer):  integer; stdcall;
function N1700InitializeLibraryDemo(Console: boolean; var NumModules: dword; var NumChannels: dword): integer; stdcall;
function N1700InitializeLibraryNoAutoSrch(Console: boolean; Par: integer): integer; stdcall;
function N1700GetDevices(var NumModules: dWord; var NumChannels: dWord): integer; stdcall;
function N1700SetAutoSrch(AutoSrch: boolean): integer; stdcall;
function N1700FreeLibrary: integer; stdcall;
function N1700Refresh(var NumModules: dword; var NumChannels: dword):  integer; stdcall;
function N1700GetVersion(var Version: rN1700_VERSION): integer; stdcall;
function N1700GetNumModules: integer; stdcall;
function N1700GetNumChannels: integer; stdcall;
function N1700GetModule(ModuleIdx: dword; var Module: rN1700_Module): integer; stdcall;
function N1700GetChannel(ChannelIdx: dword; var Channel: rN1700_Channel): integer; stdcall;
function N1700PollData(ChannelIdx: integer; // // Id of Channel
                       var Data: double): integer; stdcall;

// Messdaten für die in pDevNoArray gelisteten Geräte anfordern
function N1700RequestData(numChannels       : integer;      // Number of Channels
                          pChannelIdxArray  : pointer;                    // Pointer to array of ChannelIdx
                          Par               : integer): integer; stdcall; // Par: 0
function N1700RequestAllData(Par: integer): integer; stdcall; // Par: 0
function N1700StartContinuousRequestData(numChannels       : integer;      // Number of Channels
                                         pChannelIdxArray  : pointer;                    // Pointer to array of ChannelIdx
                                         Interval          : dword): integer; stdcall;  // Pointer to array of DevNo
function N1700StopContinuousRequestData(numChannels        : integer;      // Number of Channels
                                        pChannelIdxArray   : pointer): integer; stdcall; // Pointer to array of ChannelIdx
function N1700StartContinuousRequestAllData(Interval: dword; // Interval: 0
                                            Par     : integer): integer; stdcall; // Par: 0
function N1700StopContinuousRequestAllData: integer; stdcall;

function N1700StartContinuousRequestFootSwitch: integer; stdcall;
function N1700StopContinuousRequestFootSwitch: integer; stdcall;

function N1700SetData(ChannelIdx: dword; Data: dWord): integer; stdcall;

function N1700SetLED(ChannelIdx: dword; State: tLedState): integer; stdcall;
function N1700GetLed(ChannelIdx: dWord; var LedState: tLedState): integer; stdcall;
function N1700SetSerialNo(ChannelIdx: dword; SerNoArr: aSerialNo): integer; stdcall;
function N1700GetIdentNo(ChannelIdx: dword; var IdentNoArr: aIdentNo): integer; stdcall;
function N1700CalibrateChannelStart(ChannelIdx: dword): integer; stdcall;
function N1700CalibrateChannelPos(CalPos: integer; CalValMM: double; var CalValDigits: integer): integer; stdcall;
function N1700CalibrateChannelSave: integer; stdcall;
function N1700GetCustomerCalibration(ChannelIdx: dword; var OffsetMM: single; var DigitsToMM: single; var Gain: single; var IsActive: boolean): integer; stdcall;
function N1700GetCustomerCalibrationDate(ChannelIdx: dWord; var Day: word; var  Month: word; var Year: word): integer; stdcall;
function N1700SetCustomerGain(ChannelIdx: dword; Gain: single): integer; stdcall;
function N1700CustomerCalibrateChannelStart(ChannelIdx: dword): integer; stdcall;
function N1700CustomerCalibrateChannelPos(CalPos: integer; CalValMM: double; var CalValDigits: integer): integer; stdcall;
function N1700CustomerCalibrateChannelSave: integer; stdcall;
function N1700ActivateCustomerCalibration(ChannelIdx: dword; Activate: boolean): integer; stdcall;
function N1700ClearCustomerCalibration(ChannelIdx: dword): integer; stdcall;
function N1700SetDecimals(ChannelIdx: dword; Decimals: byte): integer; stdcall;
// Measuring Value := ((Indcator / DigitsToMM) - OffsetMM) * Gain
function N1700GetCalibration(ChannelIdx: dword; var OffsetMM: single; var DigitsToMM: single; var Gain: single): integer; stdcall;
function N1700GetCalibrationDate(ChannelIdx: dWord; var Day: word; var  Month: word; var Year: word): integer; stdcall;
function N1700SetOffsetMM(ChannelIdx: dword; OffsetMM: single): integer; stdcall;
function N1700SetDigitsToMM(ChannelIdx: dword; DigitsToMM: single): integer; stdcall;
function N1700SetGain(ChannelIdx: dword; Gain: single): integer; stdcall;
function N1700GetFilter(ChannelIdx: dword; var Filter: integer): integer; stdcall;
function N1700SetFilter(ChannelIdx: dword; Filter: integer): integer; stdcall;
function N1700GetPeType(ChannelIdx: dword; var PeType: integer): integer; stdcall;
function N1700SetPeType(ChannelIdx: dword; PeType: integer): integer; stdcall;
function N1700GetCnfVSS(ChannelIdx: dWord; ReadNew: boolean; var CnfVSS: rN1700_CnfVSS): integer; stdcall;
function N1700SetCnfVSS(ChannelIdx: dWord; CnfVSS: rN1700_CnfVSS): integer; stdcall;
function N1700DoResetVSS(ChannelIdx: dWord): integer; stdcall;
function N1700ActivatePhaseCorrVSS(ChannelIdx: dWord): integer; stdcall;


    // Register a callback which is called every time new values arrive
    // The caller have to make sure that all Channels use the same root hub !
function N1700RegisterDataCallback(callback_func     : tPFN_N1700_DATA_HANDLER;  // Callback handler
                                   numChannels       : integer;                    // # of Channels
                                   pChannelIdxArray  : pointer;                    // Pointer to array of ChannelId
                                   pContext          : pointer): integer; stdcall; // Pointer to integer, defines usage of
function N1700RegisterDataCallbackO(callback_func    : tPFNO_N1700_DATA_HANDLER;  // Callback handler
                                    numChannels      : integer;                       // # of Channel
                                    pChannelIdxArray : pointer;                    // Pointer to array of ChannelId
                                    pContext         : pointer): integer; stdcall;

    // Deregister a callback function/data pair
function N1700UnregisterDataCallback(callback_func : tPFN_N1700_DATA_HANDLER): integer; stdcall;   // Callback handler
function N1700UnregisterDataCallbackO(callback_func : tPFNO_N1700_DATA_HANDLER): integer; stdcall;   // Callback handler

function N1700RegisterMsgCallback(callback_func : tPFN_N1700_MSG_HANDLER): integer; stdcall;     // Callback handler
function N1700RegisterMsgCallbackO(callback_func : tPFNO_N1700_MSG_HANDLER): integer; stdcall;     // Callback handler
function N1700UnregisterMsgCallback: integer; stdcall;
function N1700UnregisterMsgCallbackO: integer; stdcall;

function N1700FirmwareUpdate(ChannelIdx: dWord; FilePath: string; OverwriteInfoA: boolean): integer; stdcall;
function N1700FirmwareUpdateUnknownModule(ChannelIdx: integer; ModuleGroup: tModuleGroup; FilePath: string; OverwriteInfoA: boolean): integer; stdcall;

procedure N1700StopEngine; stdcall;
procedure N1700ReStartEngine; stdcall;
function N1700ReadValue(ChannelIdx: dWord; var Value: double): integer; stdcall;
function N1700Reset(par: integer): integer; stdcall;
//function N1700TimeMeasure(Par: integer): integer; stdcall;
// Funktionen zusätzlich zur Definition

{$else} //---------------------------------------------------------------------------------------------------------------------------
{$ifdef x64}
const DllName= 'N1700_64';
{$else}
const DllName= 'N1700';
{$endif}
function N1700InitializeLibrary(Console: boolean; var NumModules: dword; var NumChannels: dword; Par: integer): integer; stdcall; external DLLName;
function N1700InitializeLibraryDemo(Console: boolean; var NumModules: dword; var NumChannels: dword): integer; stdcall; external DLLName
function N1700InitializeLibraryNoAutoSrch(Console: boolean; Par: integer): integer; stdcall; external DLLName
function N1700GetDevices(var NumModules: dWord; var NumChannels: dWord): integer; stdcall; external DLLName
function N1700FreeLibrary: integer; stdcall; external DllName;
function N1700SetAutoSrch(AutoSrch: boolean): integer; stdcall; external DllName;
function N1700Refresh(var NumModules: dword; var NumChannels: dword):  integer; stdcall; external DllName
function N1700GetVersion(var Version: rN1700_VERSION): integer; stdcall; external DllName;
function N1700GetNumModules: integer; stdcall; external DllName;
function N1700GetNumChannels: integer; stdcall; external DllName;
function N1700GetModule(ModuleIdx: dword; var Module: rN1700_Module): integer; stdcall; external DllName;
function N1700GetChannel(ChannelIdx: dword; var Channel: rN1700_Channel): integer; stdcall; external DllName;
function N1700PollData(ChannelIdx: integer; // Id of Channel
                       var Data: double): integer; stdcall; external DllName; // Pointer to data array for each Channel

function N1700RequestData(numChannels      : integer;      // Number of Channels
                          pChannelIdxArray : pointer;      // Pointer to array of ChannelIdx
                          Par               : integer): integer; stdcall; external DllName;
function N1700RequestAllData(Par: integer): integer; stdcall; external DllName;  // Request data from all Channels

function N1700StartContinuousRequestData(numChannels: integer;      // Number of Channels
                                         pChannelIdxArray : pointer; // Pointer to array of ChannelIdx
                                         Interval: dword): integer; stdcall; external DllName;
function N1700StopContinuousRequestData(numChannels: integer;      // Number of Channels
                                        pChannelIdxArray : pointer): integer; stdcall; external DllName;  //   Pointer to array of ChannelIdx
function N1700StartContinuousRequestAllData(Interval: dword; Par: integer): integer; stdcall; external DllName;
function N1700StopContinuousRequestAllData: integer; stdcall; external DllName;

function N1700StartContinuousRequestFootSwitch: integer; stdcall; external DllName;
function N1700StopContinuousRequestFootSwitch: integer; stdcall; external DllName;

function N1700SetData(ChannelIdx: dword; Data: dWord): integer; stdcall; external DllName;

function N1700SetLED(ChannelIdx: dword; State: tLedState): integer; stdcall; external DllName;
function N1700GetLed(ChannelIdx: dWord; var LedState: tLedState): integer; stdcall; external DllName;
function N1700SetSerialNo(ChannelIdx: dword; SerNoArr: aSerialNo): integer; stdcall; external DllName;
function N1700GetIdentNo(ChannelIdx: dword; var IdentNoArr: aIdentNo): integer; stdcall; external DllName;
function N1700GetCalibration(ChannelIdx: dword; var OffsetMM: single; var DigitsToMM: single; var Gain: single): integer; stdcall; external DllName;
function N1700GetCalibrationDate(ChannelIdx: dWord; var Day: word; var  Month: word; var Year: word): integer; stdcall; external DllName;
function N1700GetCustomerCalibration(ChannelIdx: dword; var OffsetMM: single; var DigitsToMM: single; var Gain: single; var IsActive: boolean): integer; stdcall; external DllName;
function N1700GetCustomerCalibrationDate(ChannelIdx: dWord; var Day: word; var  Month: word; var Year: word): integer; stdcall; external DllName;
function N1700SetGain(ChannelIdx: dword; Gain: single): integer; stdcall; external DllName;
function N1700CalibrateChannelStart(ChannelIdx: dword): integer; stdcall; external DllName;
function N1700CalibrateChannelPos(CalPos: integer; CalValMM: double; var CalValDigits: integer): integer; stdcall; external DllName;
function N1700CalibrateChannelSave: integer; stdcall; external DllName;
function N1700SetCustomerGain(ChannelIdx: dword; Gain: single): integer; stdcall; external DllName;
function N1700CustomerCalibrateChannelStart(ChannelIdx: dword): integer; stdcall; external DllName;
function N1700CustomerCalibrateChannelPos(CalPos: integer; CalValMM: double; var CalValDigits: integer): integer; stdcall; external DllName;
function N1700CustomerCalibrateChannelSave: integer; stdcall; external DllName;
function N1700ActivateCustomerCalibration(ChannelIdx: dword; Activate: boolean): integer; stdcall; external DllName;
function N1700ClearCustomerCalibration(ChannelIdx: dword): integer; stdcall; external DllName;
function N1700SetDecimals(ChannelIdx: dword; Decimals: byte): integer; stdcall; external DllName;
// Measuring Value := ((Indcator Digits/ DigitsToMM) - OffsetMM) * Gain
function N1700SetOffsetMM(ChannelIdx: dword; OffsetMM: single): integer; stdcall; external DllName;
function N1700SetDigitsToMM(ChannelIdx: dword; DigitsToMM: single): integer; stdcall; external DllName;
function N1700GetFilter(ChannelIdx: dword; var Filter: integer): integer; stdcall; external DllName;
function N1700SetFilter(ChannelIdx: dword; Filter: integer): integer; stdcall; external DllName;
function N1700GetPeType(ChannelIdx: dword; var PeType: integer): integer; stdcall; external DllName;
function N1700SetPeType(ChannelIdx: dword; PeType: integer): integer; stdcall; external DllName;
function N1700GetCnfVSS(ChannelIdx: dWord; ReadNew: boolean; var CnfVSS: rN1700_CnfVSS): integer; stdcall; external DllName;
function N1700SetCnfVSS(ChannelIdx: dWord; CnfVSS: rN1700_CnfVSS): integer; stdcall; external DllName;
function N1700DoResetVSS(ChannelIdx: dWord): integer; stdcall; external DllName;
function N1700ActivatePhaseCorrVSS(ChannelIdx: dWord): integer; stdcall; external DllName;


    // Register a callback which is called every time new values arrive
    // The caller have to make sure that all Channels use the same root hub !
function N1700RegisterDataCallback(callback_func     : tPFN_N1700_DATA_HANDLER;   // Callback handler
                                   numChannels       : integer;                   // # of Channels
                                   pChannelIdxArray  : pointer;                   // Pointer to array of ChannelIdx
                                   pContext          : pointer): integer; stdcall; external DllName;
function N1700RegisterDataCallbackO(callback_func    : tPFNO_N1700_DATA_HANDLER;  // Callback handler
                                    numChannels      : integer;                   // # of Channels
                                    pChannelIdxArray : pointer;                   // Pointer to array of ChannelIdx
                                    pContext         : pointer): integer; stdcall; external DllName;

    // Deregister a callback function/data pair
function N1700UnregisterDataCallback(callback_func : tPFN_N1700_DATA_HANDLER): integer; stdcall; external DllName;   // Callback handler
function N1700UnregisterDataCallbackO(callback_func : tPFNO_N1700_DATA_HANDLER): integer; stdcall; external DllName;  // Callback handler

function N1700RegisterMsgCallback(callback_func : tPFN_N1700_MSG_HANDLER): integer; stdcall; external DllName;     // Callback handler
function N1700RegisterMsgCallbackO(callback_func : tPFNO_N1700_MSG_HANDLER): integer; stdcall; external DllName;     // Callback handler
function N1700UnregisterMsgCallback: integer; stdcall; external DllName;
function N1700UnregisterMsgCallbackO: integer; stdcall; external DllName;

function N1700FirmwareUpdate(ChannelIdx: dWord; FilePath: string; OverwriteInfoA: boolean): integer; stdcall; external DllName;
function N1700FirmwareUpdateUnknownModule(ChannelIdx: integer; ModuleGroup: tModuleGroup; FilePath: string; OverwriteInfoA: boolean): integer;  stdcall; external DllName;

procedure N1700StopEngine; stdcall; external DllName;
procedure N1700ReStartEngine; stdcall; external DllName;
function N1700ReadValue(ChannelIdx: dWord; var Value: double): integer; stdcall; external DllName;
function N1700Reset(par: integer): integer; stdcall; external DllName;
//function N1700TimeMeasure(Par: integer): integer; stdcall; external 'N1700';

{$endif}


