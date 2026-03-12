using MillimarN1700LibCSharp;
      
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Permissions;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MillimarN1700TestCSharp
{
    public partial class FrmN1700Test : Form
    {
        public N1700Lib.N1700MsgCallback MCallback;
        public N1700Lib.N1700ExtDataCallback DCallback;

        bool DataCallbackRegistered = false;

        int iResult;
        uint NumModules;
        uint NumChannels;

        bool Measuring = false;

        int LastTick;

        static int MaxModuleCount = 100;
        static int MaxChannelCount = 400;

        static int iContext = 0x33; // Add Velocity and Multiturn on VSS Modules

        N1700Lib.sN1700_Module[] aN1700_Module = new N1700Lib.sN1700_Module[MaxModuleCount];
        N1700Lib.sN1700_Channel[] aN1700_Channel = new N1700Lib.sN1700_Channel[MaxChannelCount];
        N1700Lib.sN1700_CnfVSS CnfVSS;


        N1700Lib.N1700version ver = new N1700Lib.N1700version();

        //------------------------------------------------------------------------------------------------------------------------------------------
        public FrmN1700Test()
        //------------------------------------------------------------------------------------------------------------------------------------------
        {
            InitializeComponent();
            dataGridView.RowCount = MaxChannelCount;


            int iSize = Marshal.SizeOf(CnfVSS);




            iResult = N1700Lib.N1700InitializeLibrary(false, out NumModules, out NumChannels, 0);

            IntPtr ptr = Marshal.AllocHGlobal(Marshal.SizeOf(ver));
            int result = N1700Lib.N1700GetVersion(ptr);
            ver = (N1700Lib.N1700version)Marshal.PtrToStructure(ptr, typeof(N1700Lib.N1700version));

            LblVersion.Text = (ver.N1700lib.major).ToString("D2") + "." + ver.N1700lib.minor.ToString("D2") + "-" + ver.N1700lib.micro.ToString("D2");

            MCallback = new N1700Lib.N1700MsgCallback(MsgCallback);
            N1700Lib.N1700RegisterMsgCallback(MCallback);

            GetModulesData();
            GetChannelsData();


        }
        //------------------------------------------------------------------------------------------------------------------------------------------
        private void FrmN1700Test_Load(object sender, EventArgs e)
        //------------------------------------------------------------------------------------------------------------------------------------------
        {

        }

        //------------------------------------------------------------------------------------------------------------------------------------------
        private void FrmN1700Test_FormClosing(object sender, FormClosingEventArgs e)
        //------------------------------------------------------------------------------------------------------------------------------------------
        {
            N1700Lib.N1700UnregisterExtDataCallback(DCallback);
            N1700Lib.N1700FreeLibrary();
        }

        //------------------------------------------------------------------------------------------------------------------------------------------
        unsafe public void MsgCallback(int msg, uint channel, int param)
        //------------------------------------------------------------------------------------------------------------------------------------------
        {
            switch (msg)
            {
                //----------------------------------------------------------------------------------------------------------------------------------
                case N1700Lib.WM_N1700_Tick:
                    if (PnlLedUsbStick.BackColor == Color.Gray) PnlLedUsbStick.BackColor = Color.Lime;
                    else                                        PnlLedUsbStick.BackColor = Color.Gray;
                    break;
                //----------------------------------------------------------------------------------------------------------------------------------
                case N1700Lib.WM_N1700_ModuleCountChanged:
                    NumModules = (uint)param;
                    GetModulesData();

                    break;

                //----------------------------------------------------------------------------------------------------------------------------------
                case N1700Lib.WM_N1700_ChannelCountChanged:
                    NumChannels = (uint) param;
                    GetChannelsData();

//                    N1700Lib.N1700UnregisterDataCallback(DataCallbackFunc);
//                    RegisterDataCallback;
                    break;
                case N1700Lib.WM_N1700_MwProSek:
                    LblValsSec.Text = param.ToString();
                    break;
                case N1700Lib.WM_N1700_Switch:
                    if (param > 0)  PnlLedSwitch.BackColor = Color.Lime;
                    else            PnlLedSwitch.BackColor = Color.Gray;
                    break;
                case N1700Lib.WM_N1700_Communication:
                    break;

            }
        }

        //------------------------------------------------------------------------------------------------------------------------------------------
        unsafe public void DataCallback(int numData, IntPtr pData, IntPtr context)
        //------------------------------------------------------------------------------------------------------------------------------------------
        {
            if (Environment.TickCount > LastTick+10)
            {
                int i;
                int iContext; 
                N1700Lib.sN1700_ChannelExtData[] DataArray = new N1700Lib.sN1700_ChannelExtData[numData];
                uint ChIdx;

                iContext = Marshal.ReadInt32(context);


                int size = Marshal.SizeOf(DataArray[0]);
                for (i = 0; i < numData; i++)
                {
                    DataArray[i] = (N1700Lib.sN1700_ChannelExtData)Marshal.PtrToStructure(pData, typeof(N1700Lib.sN1700_ChannelExtData));
                    pData += size;
                }
//                Marshal.Copy(pData, DataArray, 0, numData);
                bool IsVelocity = false;
                bool IsMultiturn = false;
                bool RefActive = false;
                bool Referenced = false; ;
                int Col;


                for (i = 0; i < numData; i++)
                {
                    ChIdx = DataArray[i].ChannelIdx;
                    Col = 5;

                    IsVelocity = DataArray[i].ValueType == N1700Lib.tDataValueType.dvtVelocity;
                    if (IsVelocity) Col = 6;

                    IsMultiturn = DataArray[i].ValueType == N1700Lib.tDataValueType.dvtTurn;
                    if (IsMultiturn) Col = 7;


                    RefActive = DataArray[i].ReferenceActive > 0;
                    Referenced = DataArray[i].Referenced > 0;


                    dataGridView.Rows[(int)ChIdx].Cells[Col].Value = DataArray[i].dValue.ToString();
                }
                LastTick = Environment.TickCount;
            }
        }

        //------------------------------------------------------------------------------
        unsafe public void RegisterDataCallback()
        //------------------------------------------------------------------------------
        {
            int i;
            uint[] pChannelIdxArray = new uint[MaxChannelCount];
            IntPtr pContext;
            //            = { 0,0,0,0 };
           

            pContext = Marshal.AllocHGlobal(Marshal.SizeOf(iContext));
            Marshal.WriteInt32(pContext, iContext);
            for (i = 0; i < NumChannels; i++)
            {
                pChannelIdxArray[i] = aN1700_Channel[i].ChannelIdx;
            }
            DCallback = new N1700Lib.N1700ExtDataCallback(DataCallback);
            N1700Lib.N1700RegisterExtDataCallback(DCallback, (int)NumChannels, pChannelIdxArray, pContext);
        }


        //------------------------------------------------------------------------------
        unsafe public void GetModulesData()
        //------------------------------------------------------------------------------
        {
            uint i, q;
            IntPtr ptr;

            for (i = 0; i < NumModules; i++)
                if (i < MaxModuleCount)
                {
                    ptr = Marshal.AllocHGlobal(Marshal.SizeOf(aN1700_Module[i]));
                    iResult = N1700Lib.N1700GetModule(i, ptr);
                    aN1700_Module[i] = (N1700Lib.sN1700_Module)Marshal.PtrToStructure(ptr, typeof(N1700Lib.sN1700_Module));

                }

        }

        //------------------------------------------------------------------------------
        unsafe public void GetChannelsData()
        //------------------------------------------------------------------------------
        {
            uint i, q;
            IntPtr ptr;

            ComboBoxPollDataChannel.Items.Clear();

            for (i = 0; i < NumChannels; i++)
            if (i < MaxChannelCount)
            {

                ptr = Marshal.AllocHGlobal(Marshal.SizeOf(aN1700_Channel[i]));
                iResult = N1700Lib.N1700GetChannel(i, ptr);
                aN1700_Channel[i] = (N1700Lib.sN1700_Channel)Marshal.PtrToStructure(ptr, typeof(N1700Lib.sN1700_Channel));
                if (aN1700_Channel[i].ChannelIdx == 0) {

                }
                ComboBoxPollDataChannel.Items.Add(aN1700_Channel[i].ChannelIdx.ToString());

                dataGridView.Rows[(int)i].Cells[0].Value = aN1700_Channel[i].ChannelIdx.ToString();
                dataGridView.Rows[(int)i].Cells[1].Value = System.Text.Encoding.UTF8.GetString(aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sModuleType);
                dataGridView.Rows[(int)i].Cells[2].Value = System.Text.Encoding.UTF8.GetString(aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sDescription);
                dataGridView.Rows[(int)i].Cells[3].Value = System.Text.Encoding.UTF8.GetString(aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sIdentNo);
                dataGridView.Rows[(int)i].Cells[4].Value = System.Text.Encoding.UTF8.GetString(aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sSerialNo);


            }
            for (i = NumChannels; i < MaxChannelCount; i++)
                for (q = 0; q <= 7; q++)
                    dataGridView.Rows[(int)i].Cells[(int)q].Value = "";

            if (DataCallbackRegistered) N1700Lib.N1700UnregisterExtDataCallback(DCallback);
            RegisterDataCallback();
            DataCallbackRegistered = true;


            N1700Lib.N1700RequestAllData(0);

        }

        private void BtnMeasure_Click(object sender, EventArgs e)
        {
            if (!Measuring)
            {
                N1700Lib.N1700StartContinuousRequestAllData(0, 0);
                BtnMeasure.Text = "Stop Measuring";
            }
            else
            {
                N1700Lib.N1700StopContinuousRequestAllData();
                BtnMeasure.Text = "Start Measuring";
            }
            Measuring = !Measuring;

        }

        private void BtnGetCalib_Click(object sender, EventArgs e)
        {
            float fOffsetMM = 0;
            float fDigitsToMM = 0;
            float fGain = 0;
            bool bIsActive = false;

            N1700Lib.N1700GetCustomerCalibration(1, ref fOffsetMM, ref fDigitsToMM, ref fGain, ref bIsActive);
        }

        private void ButtonPollDataChannel_Click(object sender, EventArgs e)
        {
            double DblData;

            N1700Lib.N1700PollData(Convert.ToUInt32(ComboBoxPollDataChannel.SelectedItem), out DblData);

            TextBoxPollDataVal.Text = DblData.ToString();
        }

        private void dataGridView_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {

        }

        private void BtnGetConfigVSS_Click(object sender, EventArgs e)
        {
            IntPtr ptr;

            ptr = Marshal.AllocHGlobal(Marshal.SizeOf(CnfVSS));
            iResult = N1700Lib.N1700GetCnfVSS(1, false, ptr);
            CnfVSS = (N1700Lib.sN1700_CnfVSS)Marshal.PtrToStructure(ptr, typeof(N1700Lib.sN1700_CnfVSS));

        }

    }
}


