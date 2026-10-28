; -*- coding: utf-8 -*-
Unicode True
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

!ifndef STAGING
  !error "STAGING must point to the validated executable bundle"
!endif
!ifndef OUTPUT
  !error "OUTPUT must be an absolute installer path"
!endif
!ifndef UNINSTALL_LIST
  !error "UNINSTALL_LIST must point to the generated file manifest"
!endif

Name "ChimpiBridge"
OutFile "${OUTPUT}"
InstallDir "$PROGRAMFILES64\SnoopyOS Company\ChimpiBridge"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
VIProductVersion "0.1.1.0"
VIAddVersionKey "ProductName" "ChimpiBridge"
VIAddVersionKey "FileDescription" "ChimpiBridge Setup"
VIAddVersionKey "FileVersion" "0.1.1"
VIAddVersionKey "CompanyName" "Chimpi-hackintosh"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 Chimpi-hackintosh"
!define MUI_ICON "..\assets\mark.ico"
!define MUI_UNICON "..\assets\mark.ico"
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "PortugueseBR"

LangString DesktopShortcut ${LANG_ENGLISH} "Desktop shortcut"
LangString DesktopShortcut ${LANG_PORTUGUESEBR} "Atalho na area de trabalho"
LangString NeedX64 ${LANG_ENGLISH} "ChimpiBridge requires Windows x64"
LangString NeedX64 ${LANG_PORTUGUESEBR} "O ChimpiBridge requer Windows x64"
LangString NeedWindows ${LANG_ENGLISH} "ChimpiBridge requires Windows 10 or Windows 11"
LangString NeedWindows ${LANG_PORTUGUESEBR} "O ChimpiBridge requer Windows 10 ou Windows 11"

!macro InitLanguage
  System::Call 'kernel32::GetUserDefaultUILanguage() i .r0'
  IntOp $0 $0 & 0x3ff
  ${If} $0 == 22
    StrCpy $LANGUAGE ${LANG_PORTUGUESEBR}
  ${Else}
    StrCpy $LANGUAGE ${LANG_ENGLISH}
  ${EndIf}
  SetRegView 64
  SetShellVarContext all
!macroend

Function .onInit
  !insertmacro InitLanguage
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "$(NeedX64)"
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK|MB_ICONSTOP "$(NeedWindows)"
    Abort
  ${EndIf}
  ReadRegStr $1 HKLM "Software\SnoopyOS Company\ChimpiBridge" "InstallDir"
  ${If} $1 != ""
    StrCpy $INSTDIR $1
  ${EndIf}
FunctionEnd

Function un.onInit
  !insertmacro InitLanguage
FunctionEnd

Section "!ChimpiBridge" Core
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "${STAGING}\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\ChimpiBridge"
  CreateShortcut "$SMPROGRAMS\ChimpiBridge\ChimpiBridge.lnk" "$INSTDIR\ChimpiBridge.exe"
  WriteRegStr HKLM "Software\SnoopyOS Company\ChimpiBridge" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "DisplayName" "ChimpiBridge"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "DisplayVersion" "0.1.1"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "Publisher" "Chimpi-hackintosh"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "DisplayIcon" "$INSTDIR\ChimpiBridge.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge" "NoRepair" 1
SectionEnd

Section /o "$(DesktopShortcut)" Desktop
  CreateShortcut "$DESKTOP\ChimpiBridge.lnk" "$INSTDIR\ChimpiBridge.exe"
SectionEnd

Section "Uninstall"
  !include "${UNINSTALL_LIST}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\ChimpiBridge\ChimpiBridge.lnk"
  RMDir "$SMPROGRAMS\ChimpiBridge"
  Delete "$DESKTOP\ChimpiBridge.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChimpiBridge"
  DeleteRegKey HKLM "Software\SnoopyOS Company\ChimpiBridge"
  ; Per-user preferences and operation history in LocalAppData are preserved
SectionEnd
