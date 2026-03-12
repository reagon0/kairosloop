program MillimarN1700DllTestDelphi;

uses
  Vcl.Forms,
  DllTestMain in 'DllTestMain.pas' {FrmDllTestMain};

{$R *.res}

begin
  Application.Initialize;
  Application.MainFormOnTaskbar := True;
  Application.CreateForm(TFrmDllTestMain, FrmDllTestMain);
  Application.Run;
end.
