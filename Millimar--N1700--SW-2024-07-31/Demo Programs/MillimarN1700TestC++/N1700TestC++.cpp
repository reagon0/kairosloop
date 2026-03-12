#include <string>
using namespace std;

#include "stdafx.h"
#include "windows.h"
#include "N1700.h"


#define MTrace_AddToLevel3 printf
#define MTrace_AddToLevel5 printf
#define MErrLog_Add printf


F_N1700InitializeLibrary                   N1700InitializeLibrary;
F_N1700FreeLibrary                         N1700FreeLibrary;
F_N1700Refresh                             N1700Refresh;
F_N1700GetVersion                          N1700GetVersion;
F_N1700GetNumModules                       N1700GetNumModules;
F_N1700GetNumChannels                      N1700GetNumChannels;
F_N1700GetModule                           N1700GetModule;
F_N1700GetChannel                          N1700GetChannel;
F_N1700RequestData                         N1700RequestData;
F_N1700RequestAllData                      N1700RequestAllData;
F_N1700StartContinuousRequestAllData       N1700StartContinuousRequestAllData;
F_N1700StopContinuousRequestAllData        N1700StopContinuousRequestAllData;
F_N1700StartContinuousRequestFootSwitch    N1700StartContinuousRequestFootSwitch;
F_N1700StopContinuousRequestFootSwitch     N1700StopContinuousRequestFootSwitch;
F_N1700SetData                             N1700SetData;
F_N1700SetLED                              N1700SetLED;
F_N1700SetDecimals                         N1700SetDecimals;
F_N1700RegisterExtDataCallback             N1700RegisterExtDataCallback;
F_N1700UnregisterExtDataCallback           N1700UnregisterExtDataCallback;
F_N1700RegisterMsgCallback                 N1700RegisterMsgCallback;
F_N1700UnregisterMsgCallback               N1700UnregisterMsgCallback;
F_N1700DoResetVSS                          N1700DoResetVSS;


//-----------------------------------------------------------------------------------------------------------------------------------------	
static int __stdcall messagecallback_handler(int Msg, UI32 DeviceId, int Param)
//-----------------------------------------------------------------------------------------------------------------------------------------	
{
//	MTrace_AddToLevel3("Msg: %i DeviceId: %i Param: %i\r\n", Msg, DeviceId, Param);
	switch (Msg) {
	case WM_N1700_Tick:
		MTrace_AddToLevel3("WM_N1700_Tick\r\n");
		break;
	case WM_N1700_ModuleCountChanged:
		MTrace_AddToLevel3("WM_N1700_ModuleCountChanged\r\n");
		break;
	case WM_N1700_ChannelCountChanged:
		MTrace_AddToLevel3("WM_N1700_ChannelCountChanged\r\n");
		break;
	}
	return 0;
}

//-----------------------------------------------------------------------------------------------------------------------------------------	
static int __stdcall datacallback_handler(int numChannels, sN1700_ChannelExtData* pData, int* pContext)
//-----------------------------------------------------------------------------------------------------------------------------------------	
{
	int Channel;
//	struct sN1700_ChannelExtData Data[100] = (sN1700_ChannelExtData) *pData;

	int iContext = (int) (*pContext);
	MTrace_AddToLevel3("Data Callback... ");
	MTrace_AddToLevel3("Context: %i / ", iContext);

	for (int i = 0; i < numChannels; i++)
	{
		Channel = pData[i].ChannelIdx;
		MTrace_AddToLevel3("Channel: %i: %f", Channel, pData[i].dValue);
		if (i < numChannels - 1) MTrace_AddToLevel3(" / ");
	}
	MTrace_AddToLevel3("\r\n");

	return 0;
}

HMODULE m_hLib;
bool m_bIsCallBackregisterd = false;
N1700version m_Version;

//-----------------------------------------------------------------------------------------------------------------------------------------	
bool Open()
//-----------------------------------------------------------------------------------------------------------------------------------------	
{
	UI32 NumModules, NumChannels;
	sN1700_Module Module[10];
	sN1700_Channel Channel[40];
	bool bRet = TRUE;
	int result;
	int i;


	// load dll and get function pointers
#if defined (_WIN64)
	m_hLib = LoadLibrary("N1700_64.dll"); // Projektoptionen Zeichensatz Multibyte
#else
	m_hLib = LoadLibrary("N1700.dll"); // Projektoptionen Zeichensatz Multibyte
#endif

	if (!m_hLib)
	{
		DWORD dwError = GetLastError();
		MErrLog_Add("Open(): LoadLibrary(\"N1700.dll\") failed with %i\r\n", dwError);
		bRet = false;
		goto bailout;
	}

	N1700InitializeLibrary = (F_N1700InitializeLibrary)::GetProcAddress(m_hLib, "N1700InitializeLibrary");
	if (!N1700InitializeLibrary)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700InitializeLibrary) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700FreeLibrary = (F_N1700FreeLibrary)::GetProcAddress(m_hLib, "N1700FreeLibrary");
	if (!N1700FreeLibrary)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700FreeLibrary) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700Refresh = (F_N1700Refresh)::GetProcAddress(m_hLib, "N1700Refresh");
	if (!N1700Refresh)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700Refresh) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700GetVersion = (F_N1700GetVersion)::GetProcAddress(m_hLib, "N1700GetVersion");
	if (!N1700GetVersion)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700GetVersion) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700GetNumModules = (F_N1700GetNumModules)::GetProcAddress(m_hLib, "N1700GetNumModules");
	if (!N1700GetNumModules)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700GetNumModules) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700GetNumChannels = (F_N1700GetNumChannels)::GetProcAddress(m_hLib, "N1700GetNumChannels");
	if (!N1700GetNumChannels)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700GetNumChannels) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700GetModule = (F_N1700GetModule)::GetProcAddress(m_hLib, "N1700GetModule");
	if (!N1700GetModule)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700GetModule) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700GetChannel = (F_N1700GetChannel)::GetProcAddress(m_hLib, "N1700GetChannel");
	if (!N1700GetChannel)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700GetChannel) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700RequestData = (F_N1700RequestData)::GetProcAddress(m_hLib, "N1700RequestData");
	if (!N1700RequestData)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700RequestData) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700RequestAllData = (F_N1700RequestAllData)::GetProcAddress(m_hLib, "N1700RequestAllData");
	if (!N1700RequestAllData)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700RequestAllData) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700StartContinuousRequestAllData = (F_N1700StartContinuousRequestAllData)::GetProcAddress(m_hLib, "N1700StartContinuousRequestAllData");
	if (!N1700StartContinuousRequestAllData)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700StartContinuousRequestAllData) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700StopContinuousRequestAllData = (F_N1700StopContinuousRequestAllData)::GetProcAddress(m_hLib, "N1700StopContinuousRequestAllData");
	if (!N1700StopContinuousRequestAllData)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700StopContinuousRequestAllData) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700StartContinuousRequestFootSwitch = (F_N1700StartContinuousRequestFootSwitch)::GetProcAddress(m_hLib, "N1700StartContinuousRequestFootSwitch");
	if (!N1700StartContinuousRequestFootSwitch)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700StartContinuousRequestFootSwitch) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700StopContinuousRequestFootSwitch = (F_N1700StopContinuousRequestFootSwitch)::GetProcAddress(m_hLib, "N1700StopContinuousRequestFootSwitch");
	if (!N1700StopContinuousRequestFootSwitch)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700StopContinuousRequestFootSwitch) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700SetData = (F_N1700SetData)::GetProcAddress(m_hLib, "N1700SetData");
	if (!N1700SetData)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700SetData) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700SetLED = (F_N1700SetLED)::GetProcAddress(m_hLib, "N1700SetLED");
	if (!N1700SetLED)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700SetLED) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700SetDecimals = (F_N1700SetDecimals)::GetProcAddress(m_hLib, "N1700SetDecimals");
	if (!N1700SetDecimals)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700SetDecimals) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700RegisterExtDataCallback = (F_N1700RegisterExtDataCallback)::GetProcAddress(m_hLib, "N1700RegisterExtDataCallback");
	if (!N1700RegisterExtDataCallback)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700RegisterExtDataCallback) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700UnregisterExtDataCallback = (F_N1700UnregisterExtDataCallback)::GetProcAddress(m_hLib, "N1700UnregisterExtDataCallback");
	if (!N1700UnregisterExtDataCallback)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700UnregisterExtDataCallback) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700RegisterMsgCallback = (F_N1700RegisterMsgCallback)::GetProcAddress(m_hLib, "N1700RegisterMsgCallback");
	if (!N1700RegisterMsgCallback)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700RegisterMsgCallback) failed\r\n");
		bRet = false;
		goto bailout;
	}
	N1700UnregisterMsgCallback = (F_N1700UnregisterMsgCallback)::GetProcAddress(m_hLib, "N1700UnregisterMsgCallback");
	if (!N1700UnregisterMsgCallback)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700UnregisterMsgCallback) failed\r\n");
		bRet = false;
		goto bailout;
	}

	N1700DoResetVSS = (F_N1700DoResetVSS)::GetProcAddress(m_hLib, "N1700DoResetVSS");
	if (!N1700UnregisterMsgCallback)
	{
		MErrLog_Add("Open(): GetProcAddress(N1700DoResetVSS) failed\r\n");
		bRet = false;
		goto bailout;
	}

	result = N1700InitializeLibrary(true, &NumModules, &NumChannels, 3912); 
	MTrace_AddToLevel3("Open(): N1700InitializeLibrary() returned %i\r\n", result);
	MTrace_AddToLevel3("Open(): NumModules = %i, NumChannels = %i\r\n", NumModules, NumChannels);

	// register message callback
	result = N1700RegisterMsgCallback(messagecallback_handler);
	MTrace_AddToLevel3("Open(): N1700RegisterMsgCallback returned %i\r\n", result);
	if (result != N1700_SUCCESS)
	{
		MErrLog_Add("Open(): N1700RegisterMsgCallback failed\r\n");
		bRet = false;
		goto bailout;
	}

	// get version info
	result = N1700GetVersion(&m_Version);
	MTrace_AddToLevel3("Open(): N1700GetVersion returned %i (N1700lib v%02i.%02i-%02i)\r\n",
		result,
		m_Version.N1700lib.major,
		m_Version.N1700lib.minor,
		m_Version.N1700lib.micro);



	for (i = 0; i < NumModules; i++) {
		SecureZeroMemory(&Module[i], sizeof(sN1700_Module));
		result = N1700GetModule(i, &Module[i]);
		MTrace_AddToLevel3("Module %i %s\r\n", i, Module[i].sDescription);
	}
	for (i = 0; i < NumChannels; i++) {
		SecureZeroMemory(&Channel[i], sizeof(sN1700_Channel));
		result = N1700GetChannel(i, &Channel[i]);
	}
	Sleep(2000);


	// Optional: if register data callback function, Data will be sent
	char WithDataCallback = 1;

	if (WithDataCallback)
	{
		int pChannelIdxArray[40];
//		pChannelIdxArray[0] = Channel[3].ChannelIdx; // In this excample only one Device
		for (i = 0; i < NumChannels; i++) {
			pChannelIdxArray[i] = Channel[i].ChannelIdx; // In this excample only one Device
		}
		int iContext = 0x33;

		result = N1700RegisterExtDataCallback((F_N1700ExtDataCallback)datacallback_handler, NumChannels, pChannelIdxArray, (int*)&iContext);
//		result = N1700RegisterExtDataCallback((F_N1700ExtDataCallback)datacallback_handler, 1, pChannelIdxArray, (int*)&iContext);
		m_bIsCallBackregisterd = (result == N1700_SUCCESS);
		MTrace_AddToLevel3("Open(): N1700RegisterDataCallback returned %i", result);
		if (result != N1700_SUCCESS)
			MErrLog_Add("Open(): N1700RegisterDataCallback failed\r\n");
	}

	Sleep(1000);
	result = N1700StartContinuousRequestAllData(0,0);
	UI32 pchannelIdxArray[3];
	pchannelIdxArray[0] = 0;
	pchannelIdxArray[1] = 1;
	pchannelIdxArray[2] = 2;

//	N1700RequestData(2, pchannelIdxArray, 0);// Pointer to array of ChannelId

	// give ant devices some time to connect
	Sleep(2000);
	// die gefundenen ant devices werden dann hier oder in msgcallback gemerkt
	result = N1700StopContinuousRequestAllData();
	result = N1700DoResetVSS(3);
	result = N1700StartContinuousRequestAllData(0, 0);

	Sleep(2000);
	result = N1700StopContinuousRequestAllData();
	system("PAUSE");
	//	result = N1700StopContinuousRequestAllData();
bailout:
	return bRet;
}

//-----------------------------------------------------------------------------------------------------------------------------------------	
bool Close()
//-----------------------------------------------------------------------------------------------------------------------------------------	
{
	MTrace_AddToLevel3("Close(): start\r\n");
	// unregister message callback
	int result = N1700UnregisterMsgCallback();
	MTrace_AddToLevel3("Close(): N1700UnregisterMsgCallback returned %i\r\n", result);
	// close callback
	if (m_bIsCallBackregisterd)
	{
		int result = N1700UnregisterExtDataCallback((F_N1700ExtDataCallback)datacallback_handler);
		MTrace_AddToLevel3("Close(): N1700UnregisterDataCallback returned %i\r\n", result);
	}
	// close lib
	result = N1700FreeLibrary();
	MTrace_AddToLevel3("Close(): N1700FreeLibrary returned %i\r\n", result);
	// unload dll
	if (m_hLib)
		FreeLibrary(m_hLib);
	m_hLib = NULL;
	// free m_pDevNoArray
	MTrace_AddToLevel5("Close(): cleanup m_pDevNoArray\r\n");
	MTrace_AddToLevel3("Close(): done\r\n");
	return true;
}

int _tmain(int argc, _TCHAR* argv[])
{
	Open();
	Close();
	return 0;
}

