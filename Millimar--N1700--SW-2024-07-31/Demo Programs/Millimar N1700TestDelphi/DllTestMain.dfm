object FrmDllTestMain: TFrmDllTestMain
  Left = 0
  Top = 0
  Caption = 'N1700-Test'
  ClientHeight = 562
  ClientWidth = 806
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'Tahoma'
  Font.Style = []
  OldCreateOrder = False
  OnClose = FormClose
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object PnlTop: TPanel
    Left = 0
    Top = 0
    Width = 806
    Height = 113
    Align = alTop
    TabOrder = 0
    ExplicitWidth = 641
    object LblValsSec: TLabel
      Left = 240
      Top = 16
      Width = 12
      Height = 13
      Caption = '...'
    end
    object LblTxtValsSec: TLabel
      Left = 280
      Top = 16
      Width = 56
      Height = 13
      Caption = 'Values/Sec.'
    end
    object LblTxtSwitch: TLabel
      Left = 432
      Top = 15
      Width = 31
      Height = 13
      Caption = 'Switch'
    end
    object LblTxtDllVersion: TLabel
      Left = 665
      Top = 16
      Width = 56
      Height = 13
      Caption = 'DLL-Version'
    end
    object LblDllVersion: TLabel
      Left = 781
      Top = 15
      Width = 12
      Height = 13
      Alignment = taRightJustify
      Caption = '...'
    end
    object PnlLedUsbStick: TPanel
      Left = 8
      Top = 8
      Width = 25
      Height = 25
      Color = clGray
      ParentBackground = False
      TabOrder = 0
    end
    object BtnMeasure: TButton
      Left = 56
      Top = 8
      Width = 161
      Height = 25
      Caption = 'Start Measuring '
      TabOrder = 1
      OnClick = BtnMeasureClick
    end
    object PnlLedSwitch: TPanel
      Left = 392
      Top = 7
      Width = 25
      Height = 25
      Color = clGray
      ParentBackground = False
      TabOrder = 2
    end
    object BtnPollDataChannel: TButton
      Left = 56
      Top = 61
      Width = 161
      Height = 25
      Caption = 'Poll Data from Channel'
      TabOrder = 3
      OnClick = BtnPollDataChannelClick
    end
    object CBxPollDataChannel: TComboBox
      Left = 232
      Top = 64
      Width = 57
      Height = 21
      Style = csDropDownList
      TabOrder = 4
    end
    object EdtPollDataVal: TEdit
      Left = 304
      Top = 63
      Width = 73
      Height = 24
      Font.Charset = DEFAULT_CHARSET
      Font.Color = clWindowText
      Font.Height = -13
      Font.Name = 'Tahoma'
      Font.Style = [fsBold]
      ParentFont = False
      ReadOnly = True
      TabOrder = 5
    end
    object BtnGetcalib: TButton
      Left = 632
      Top = 61
      Width = 161
      Height = 25
      Caption = 'Get Customer Calibration'
      TabOrder = 6
      OnClick = BtnGetcalibClick
    end
  end
  object StringGrid: TStringGrid
    Left = 0
    Top = 113
    Width = 806
    Height = 449
    Align = alClient
    ColCount = 8
    FixedCols = 0
    RowCount = 2
    TabOrder = 1
    ExplicitWidth = 641
    ColWidths = (
      74
      92
      106
      119
      106
      89
      84
      89)
    RowHeights = (
      24
      24)
  end
  object LBxGridTitles: TListBox
    Left = 472
    Top = 226
    Width = 137
    Height = 89
    ItemHeight = 13
    Items.Strings = (
      'Channel'
      'sModuleType'
      'sDescription'
      'sIdentNo'
      'sSerialNo'
      'Value'
      'Velocity'
      'Multiturn')
    TabOrder = 2
    Visible = False
    OnClick = LBxGridTitlesClick
  end
end
