unit DllTestMain;

interface

uses
  Winapi.Windows, Winapi.Messages, System.SysUtils, System.Variants, System.Classes, Vcl.Graphics,
  Vcl.Controls, Vcl.Forms, Vcl.Dialogs, Vcl.Grids, Vcl.ExtCtrls, Vcl.StdCtrls;

{$I N1700.INC}
type
  TFrmDllTestMain = class(TForm)
    PnlTop: TPanel;
    StringGrid: TStringGrid;
    LBxGridTitles: TListBox;
    PnlLedUsbStick: TPanel;
    BtnMeasure: TButton;
    LblValsSec: TLabel;
    LblTxtValsSec: TLabel;
    PnlLedSwitch: TPanel;
    LblTxtSwitch: TLabel;
    LblTxtDllVersion: TLabel;
    LblDllVersion: TLabel;
    BtnPollDataChannel: TButton;
    CBxPollDataChannel: TComboBox;
    EdtPollDataVal: TEdit;
    BtnGetcalib: TButton;
    procedure FormCreate(Sender: TObject);
    procedure FormClose(Sender: TObject; var Action: TCloseAction);
    procedure BtnMeasureClick(Sender: TObject);
    procedure BtnGetcalibClick(Sender: TObject);
    procedure BtnPollDataChannelClick(Sender: TObject);
    procedure LBxGridTitlesClick(Sender: TObject);
  private
    { Private-Deklarationen }
  public
    { Public-Deklarationen }
    NumModules: dword;
    NumChannels: dword;

    DataCallbackRegistered: boolean;

    iResult : integer;
    Context                   : integer;

    Measuring : boolean;

    LastTick : integer;

    aN1700_Module             : array[0..MaxModuleCount ] of rN1700_Module;
    aN1700_Channel            : array[0..MaxChannelCount] of rN1700_Channel;


    procedure GetModulesData;
    procedure GetChannelsData;
    procedure RegisterDataCallback;
    procedure MsgCallbackFunc(Msg: integer; Channel: integer; Param: integer);
    procedure DataCallbackFunc(numChannels : integer;     // Number of Channels
                               pChNoArray  : pointer;    // Pointer to array of ChNo
                               pDataArray  : pointer;
                               pContext    : pointer);


  end;

var
  FrmDllTestMain: TFrmDllTestMain;


implementation

{$R *.dfm}

//------------------------------------------------------------------------------
function IntToStr2Digits(i: integer): string;
//------------------------------------------------------------------------------
begin
  result := inttostr(i);
  while length(result) < 2 do result := '0'+result;
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.FormCreate(Sender: TObject);
//------------------------------------------------------------------------------
var
   c: integer;
   Version: rN1700_Version;
begin
   Measuring := false;
   for c := 0 to StringGrid.ColCount-1 do
       StringGrid.Cells[c,0] := LBxGridTitles.Items[c];

   N1700InitializeLibrary(false, NumModules, NumChannels, 0);

   N1700GetVersion(Version);

   LblDllVersion.Caption := 'V'+inttostr(Version.N1700lib.major)+'.' + IntToStr2Digits(Version.N1700lib.minor)+'-'+inttostr(Version.N1700lib.micro) + '-' + inttostr(Version.N1700lib.nano);

   N1700RegisterMsgCallbackO(MsgCallbackFunc);

   GetModulesData;
   GetChannelsData;
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.FormClose(Sender: TObject; var Action: TCloseAction);
//------------------------------------------------------------------------------
begin
   N1700UnregisterDataCallbackO(DataCallbackFunc);
   N1700FreeLibrary();
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.GetModulesData;
//------------------------------------------------------------------------------
var
   i: integer;
begin
   if NumModules > 0 then
   begin
      for i := 0 to NumModules-1 do
       if i < MaxModuleCount then
      begin
         N1700GetModule(i, aN1700_Module[i]);
      end;
   end;
end;

procedure TFrmDllTestMain.LBxGridTitlesClick(Sender: TObject);
begin

end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.GetChannelsData;
//------------------------------------------------------------------------------
var
  i  : integer;
  Idx: integer;
begin
   CBxPollDataChannel.Items.Clear();
   StringGrid.RowCount := NumChannels+1;
   for i := 0 to NumChannels-1 do
    if i < MaxChannelCount then
   begin
     N1700GetChannel(i, aN1700_Channel[i]);
     CBxPollDataChannel.Items.Add(inttostr(aN1700_Channel[i].ChannelIdx));

     StringGrid.Cells[0, i+1] := inttostr(aN1700_Channel[i].ChannelIdx);
     StringGrid.Cells[1, i+1] := aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sModuleType;
     StringGrid.Cells[2, i+1] := aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sDescription;
     StringGrid.Cells[3, i+1] := aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sIdentNo;
     StringGrid.Cells[4, i+1] := aN1700_Module[aN1700_Channel[i].ParentModuleIdx].sSerialNo;
   end;
   if DataCallbackRegistered then N1700UnregisterDataCallbackO(DataCallbackFunc);
   RegisterDataCallback();
   DataCallbackRegistered := true;

   if CBxPollDataChannel.Items.Count > 0 then CBxPollDataChannel.ItemIndex := 0;


   N1700RequestAllData(0);

end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.RegisterDataCallback;
//------------------------------------------------------------------------------
type
   aHndArr = array[0..MaxChannelCount-1] of integer;
var
   i,hi : integer;
   HndArr : aHndArr;
   pHndArr: pointer;
   pContext    : pointer;
   ChannelCount: integer;
begin
   hi := 0;
   for i := 0 to NumChannels-1 do
    if i < MaxChannelCount then
   begin
     HndArr[hi] := aN1700_Channel[i].ChannelIdx;
     inc(hi);
   end;
   ChannelCount := hi;

   pHndArr   := @HndArr;

   Context  := $33; // Add Velocity and Multiturn on VSS Modules
   pContext := @Context;

   N1700RegisterDataCallbackO(DataCallbackFunc,ChannelCount,pHndArr,pContext);   // Pointer to array of DevNo
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.MsgCallbackFunc(Msg: integer; Channel: integer; Param: integer);
//------------------------------------------------------------------------------
var
  i: integer;
begin
   case Msg of
     WM_N1700_Tick:
     begin
        if (PnlLedUsbStick.Color = clGray) then PnlLedUsbStick.Color := clLime
        else                                    PnlLedUsbStick.Color := clGray;
     end;
     WM_N1700_ModuleCountChanged:
     begin
        NumModules := Param;
        GetModulesData;
     end;
     WM_N1700_ChannelCountChanged:
     begin
        NumChannels := Param;
        GetChannelsData;
     end;
     WM_N1700_ChannelParChanged:
     begin
        N1700GetChannel(Channel, aN1700_Channel[Channel]);
     end;
     WM_N1700_MwProSek:
     begin
        if Param = 0 then
             LblValsSec.Caption := '...'
        else LblValsSec.Caption := inttostr(Param);
     end;
     WM_N1700_ChannelMwProSek:
     begin

     end;
     WM_N1700_Switch:
     begin
        if Param > 0 then PnlLedSwitch.Color := clLime
        else              PnlLedSwitch.Color := clGray;
     end;
     WM_N1700_Communication:
     begin
     end;
     WM_N1700_DEBUG:
     begin
     end;
     WM_N1700_Error:
     begin
     end;
   end;
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.DataCallbackFunc(numChannels : integer;     // Number of Channels
                                           pChNoArray  : pointer;    // Pointer to array of ChNo
                                           pDataArray  : pointer;
                                           pContext    : pointer);
//------------------------------------------------------------------------------
type
   aHndArr = array[0..MaxChannelCount-1] of integer;
   aDataArr = array[0..MaxChannelCount-1] of double;
var
   i,q: integer;
   pHndArr : ^aHndArr;
   pDataArr: ^aDataArr;
   dwVal: integer;
   SendStr: ansistring;
   OutByte: byte;
   MwStr: string;
   ChIdx: integer;
   IsVelocity : boolean;
   IsMultiturn : boolean;
   Col: integer;


   function CtrlDec(Dec: integer) : integer;
   begin
      result := Dec;
      if result < 0 then result := 0;

   end;

begin
   if (GetTickCount > LastTick+10) then
   begin
      LastTick := GetTickCount;

      pHndArr   := pChNoArray;
      pDataArr  := pDataArray;

      for i := 0 to numChannels-1 do
      begin
         ChIdx := pHndArr^[i] and $FFFF;
         Col := 5;

         if ((integer(pContext^) and $10) > 0) then
         begin
            IsVelocity := (pHndArr^[i] and $100000) > 0;
            if (IsVelocity) then Col := 6;
         end
         else IsVelocity := false;

         if ((integer(pContext^) and $20) > 0) then
         begin
             IsMultiturn := (pHndArr^[i] and $200000) > 0;
             if (IsMultiturn) then Col := 7;
         end
         else IsMultiturn := false;

         case aN1700_Module[aN1700_Channel[ChIdx].ParentModuleIdx].ModuleType of
            mtN1701USB:
            begin
               dwVal := round(pDataArr[i]);
               StringGrid.Cells[Col,ChIdx+1] := inttostr(dwVal);
            end;
            mtN1704IO:
            begin
      //        Memo.Lines.Add(inttostr(pHndArr^[i]) + ': ' + inttostr(round(pDataArr[i])));
               dwVal := round(pDataArr[i]);
               StringGrid.Cells[Col,ChIdx+1] := inttostr(dwVal);
            end
            else
            begin
               MwStr := floattostrF(pDataArr[i], ffFixed, 10, CtrlDec(aN1700_Channel[ChIdx].Decimals));
               StringGrid.Cells[Col,ChIdx+1] := MwStr;
            end;
         end; // case
      end
   end;
end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.BtnMeasureClick(Sender: TObject);
//------------------------------------------------------------------------------
begin
   if not Measuring then
   begin
      N1700StartContinuousRequestAllData(0, 0);
      BtnMeasure.Caption := 'Stop Measuring';
      BtnPollDataChannel.Enabled := false;
   end
   else
   begin
      N1700StopContinuousRequestAllData();
      BtnMeasure.Caption := 'Start Measuring';
      BtnPollDataChannel.Enabled := true;
   end;
   Measuring := not Measuring;

end;

//------------------------------------------------------------------------------
procedure TFrmDllTestMain.BtnGetcalibClick(Sender: TObject);
//------------------------------------------------------------------------------
var
   fOffsetMM : single;
   fDigitsToMM : single;
   fGain : single;
   bIsActive : boolean;
begin
   N1700GetCustomerCalibration(1, fOffsetMM, fDigitsToMM, fGain, bIsActive);

end;


//------------------------------------------------------------------------------
procedure TFrmDllTestMain.BtnPollDataChannelClick(Sender: TObject);
//------------------------------------------------------------------------------
var
   DblData: double;
begin
   if CBxPollDataChannel.ItemIndex >= 0 then
      N1700PollData(StrToInt(CBxPollDataChannel.Items[CBxPollDataChannel.ItemIndex]), DblData);

   EdtPollDataVal.Text := DblData.ToString();

end;


end.
