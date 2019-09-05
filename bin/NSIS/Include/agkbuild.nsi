; Description	AgkBuild NSIS Install Script Template
; Author		Adam Biser
; Copyright		2019

; This script can be used to create x86, x64, or x86_64 installers.
; x86_64 installers will only extract the EXE for the current OS.

;--------------------------------------------
; Required Macros:
;
; !macro InstallFiles	; Do NOT include any main EXE files.  They are already handled in this script.
; !macro UninstallFiles	; Do NOT include any main EXE files.  They are already handled in this script.

;--------------------------------------------
; Optional Macros:
;
; !macro InstallStartMenuShortCuts StartMenuFolder		; Not yet implemented.
; !macro UninstallStartMenuShortCuts StartMenuFolder	; Not yet implemented.

;--------------------------------------------
; User Defines
;
; !define DEVELOPER_NAME		; Required.
; !define HOMEPAGE				; Optional.  Used for "Add or Remove Programs" information.
; !define COPYRIGHT_YEAR		; Optional.  Defaults to current year.
; !define PROJECT_LICENSE_PATH	; Optional.  When set, this file is shown on a license page in the installer.
; !define PROJECT_GUID			; Optional.  Used for storing the uninstall information in the Windows Registry.  Should NEVER be changed once released.  Defaults to "${DEVELOPER_NAME} ${PROJECT_NAME}".

; !define PROJECT_ICON			; Optional.  AgkBuild sets this to "icon.ico" if found.
; !define SHORTCUT_ICON			; Optional.  Defaults to "${PROJECT_ICON}" when set; otherwise this defaults to "${EXE_NAME}".
; !define SHORTCUT_ICON_INDEX	; Optional.  Defaults to "0".

; !define HELPLINK				; Optional.  Defaults to "${HOMEPAGE}" if set.  "Add or Remove Programs" information.
; !define URLINFOABOUT			; Optional.  Defaults to "${HOMEPAGE}" if set.  "Add or Remove Programs" information.
; !define URLUPDATEINFO			; Optional.  Defaults to "${HOMEPAGE}" if set.  "Add or Remove Programs" information.

; !define INCLUDE_DEVELOPER_NAME_IN_PATHS	; Optional.  When defined, the install and start menu folders default to "${DEVELOPER_NAME}\${PROJECT_NAME}" otherwise they default to "${PROJECT_NAME}".
; !define UNINSTALL_PREVIOUS_VERSION		; Optional.  When defined, checks for and uninstalls any previously installed version.  User is asked to confirm.  Aborts if declined.
; !define INSTALLER_ICON					; Optional.  The installer icon.  Defaults to the NSIS icon.

;--------------------------------------------
; AgkBuild Defines
;
; !define PROJECT_NAME			; Required.
; !define SAFE_PROJECT_NAME		; Required.  PROJECT_NAME containing only letters, numbers and underscores.  All other characters removed.
; !define RELEASE_FILE_PATH		; Required.  Relative to project folder.
; !define ESTIMATEDSIZE			; Required.  Installed size in kb.
;
; !define PROJECT_VERSION_MAJOR	; Optional.  Defaults to 1.  Read from #constant VERSION within main.agc.
; !define PROJECT_VERSION_MINOR	; Optional.  Defaults to 0.  Read from #constant VERSION within main.agc.
; !define PROJECT_VERSION_PATCH	; Optional.  Only shown in product version if set.  Read from #constant VERSION within main.agc.
;
; !define WINDOWS_86			; 
; !define WINDOWS_64			; One of these three values must be defined.
; !define WINDOWS_86_64			;

!define PROJECT_PATH	".." 	; Required.  Relative to base install script
!cd "${PROJECT_PATH}"

; Includes
!include MUI2.nsh
!include LogicLib.nsh
!include x64.nsh

;--------------------------------------------
; Variables
Var StartMenuFolder

; Internal defines
!ifndef PROJECT_VERSION_MAJOR
	!define PROJECT_VERSION_MAJOR	1
!endif
!ifndef PROJECT_VERSION_MINOR
	!define PROJECT_VERSION_MINOR	0
!endif
!ifdef PROJECT_VERSION_PATCH
	!define PRODUCT_VERSION		"${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}"
	!define INSTALLER_VERSION	"${PRODUCT_VERSION}.0"
!else
	!define PRODUCT_VERSION		"${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}"
	!define INSTALLER_VERSION	"${PRODUCT_VERSION}.0.0"
!endif

!ifndef COPYRIGHT_YEAR
	!define /date COPYRIGHT_YEAR "%Y"
!endif

!define EXE_NAME			"${PROJECT_NAME}.exe"
!ifdef WINDOWS_86
	!define ARCHITECTURE	"x86"
!else ifdef WINDOWS_64
	!define ARCHITECTURE	"x64"
!else ifdef WINDOWS_86_64
	!define ARCHITECTURE	"x86_64"
	!define EXE_NAME_64		"${PROJECT_NAME}64.exe"
!else
	!error "A platform flag must be defined!"
!endif

!define	INSTALLER_EXE		"${SAFE_PROJECT_NAME}-${PRODUCT_VERSION}-${ARCHITECTURE}-setup.exe"
!define	UNINSTALL_EXE		"Uninstall.exe"
!ifdef INCLUDE_DEVELOPER_NAME_IN_PATHS
	!define DEFAULT_PROGRAMFILES_FOLDER		"${DEVELOPER_NAME}\${PROJECT_NAME}"
	!define DEFAULT_STARTMENU_FOLDER		"${DEVELOPER_NAME}\${PROJECT_NAME}"
!else
	!define DEFAULT_PROGRAMFILES_FOLDER		"${PROJECT_NAME}"
	!define DEFAULT_STARTMENU_FOLDER		"${PROJECT_NAME}"
!endif
!ifndef PROJECT_GUID
	!define PROJECT_GUID	"${DEVELOPER_NAME} ${PROJECT_NAME}"
!endif
!define	UNINSTALLREGKEY		"Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROJECT_GUID}"
!define	NOMODIFY			1
!define	NOREPAIR			1

!ifdef HOMEPAGE
	!ifndef HELPLINK
		!define HELPLINK		"${HOMEPAGE}"
	!endif
	!ifndef URLINFOABOUT
		!define URLINFOABOUT	"${HOMEPAGE}"
	!endif
	!ifndef URLUPDATEINFO
		!define URLUPDATEINFO	"${HOMEPAGE}"
	!endif
!endif

!ifdef INSTALLER_ICON
	Icon					"${INSTALLER_ICON}"
	!define MUI_ICON		"${INSTALLER_ICON}"
!endif

!define SHORTCUT_EXE_ARGS	""
!ifndef SHORTCUT_ICON
	!ifdef PROJECT_ICON
		!define SHORTCUT_ICON		"${PROJECT_ICON}"
	!else
		!define SHORTCUT_ICON		"${EXE_NAME}"
	!endif
!endif
!ifndef SHORTCUT_ICON_INDEX
	!define SHORTCUT_ICON_INDEX	"0"
!endif

!define DIRECTXDIR			"${NSISDIR}\..\DirectX"

;--------------------------------------------
; Installer Attributes
RequestExecutionLevel	admin
CRCCheck				on
XPStyle					on
SetCompressor			/SOLID lzma
ShowInstDetails			show
ShowUninstDetails		show

Name					"${PROJECT_NAME} ${PRODUCT_VERSION}"
BrandingText 			"Copyright ${COPYRIGHT_YEAR} ${DEVELOPER_NAME}"
OutFile					"release\${INSTALLER_EXE}"
; InstallDir is set in .onInit depending on the set Platform flag !define.
InstallDirRegKey		HKLM	"${UNINSTALLREGKEY}"	"InstallLocation"

;--------------------------------------------
; Version info for installer
VIProductVersion	"${INSTALLER_VERSION}"
VIAddVersionKey		ProductName			"${PROJECT_NAME}"
VIAddVersionKey		ProductVersion		"${PRODUCT_VERSION}"
VIAddVersionKey		CompanyName			"${DEVELOPER_NAME}"
VIAddVersionKey		LegalCopyright		"Copyright ${COPYRIGHT_YEAR} ${DEVELOPER_NAME}"
VIAddVersionKey		FileDescription		"${PROJECT_NAME} Installer"
VIAddVersionKey		FileVersion			"${INSTALLER_VERSION}"
VIAddVersionKey		OriginalFilename	"${INSTALLER_EXE}"

;--------------------------------------------
; Modern Interface Configuration

; Interface settings
;--------------------------------------------
; Page header
;----------------------------------
; !define MUI_ICON icon_file
; The icon for the installer.
; Default: ${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico

; !define MUI_UNICON icon_file
; The icon for the uninstaller.
; Default: ${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico

; !define MUI_HEADERIMAGE
; Display an image on the header of the page.

; 	!define MUI_HEADERIMAGE_BITMAP bmp_file
; Bitmap image to display on the header of installers pages (recommended size: 150x57 pixels).
; Default: ${NSISDIR}\Contrib\Graphics\Header\nsis.bmp

; 		!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
; Do not stretch the installer header bitmap to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; 		!define MUI_HEADERIMAGE_BITMAP_RTL bmp_file
; Bitmap image to display on the header of installers pages when using a RTL language (recommended size: 150x57 pixels).
; Default: Non-RTL bitmap

; 			!define MUI_HEADERIMAGE_BITMAP_RTL_NOSTRETCH
; Do not stretch the installer header bitmap when using a RTL language to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; 	!define MUI_HEADERIMAGE_UNBITMAP bmp_file
; Bitmap image to display on the header of uninstaller pages (recommended size: 150x57 pixels).
; Default: Installer header bitmap

; 		!define MUI_HEADERIMAGE_UNBITMAP_NOSTRETCH
; Do not stretch the uninstaller header bitmap to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; 		!define MUI_HEADERIMAGE_UNBITMAP_RTL bmp_file
; Bitmap image to display on the header of uninstallers pages when using a RTL language (recommended size: 150x57 pixels).
; Default: Installer RTL header bitmap

; 			!define MUI_HEADERIMAGE_UNBITMAP_RTL_NOSTRETCH
; Do not stretch the uninstaller header bitmap when using a RTL language to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; 	!define MUI_HEADERIMAGE_RIGHT
; Display the header image on the right side instead of the left side (when using a RTL language it will be displayed on the left side instead of the right side).

; !define MUI_BGCOLOR (color: RRGGBBR hexadecimal)
; Background color for the header, the Welcome page and the Finish page.
; Default: FFFFFF

; !define MUI_HEADER_TRANSPARENT_TEXT
; Set a transparent background for the header's label controls. Useful for custom user interfaces that set a bigger header image.

; Interface resources
;----------------------------------
; !define MUI_UI ui_file
; The interface file with the dialog resources. Change this if you have made your own customized UI.
; Default: ${NSISDIR}\Contrib\UIs\modern.exe

; !define MUI_UI_HEADERIMAGE ui_file
; The interface files with the dialog resource IDD_INST that contains a bitmap control and space for the header bitmap.
; Default: ${NSISDIR}\Contrib\UIs\modern_headerbmp.exe

; !define MUI_UI_HEADERIMAGE_RIGHT ui_file
; The interface files with the dialog resource IDD_INST that contains a bitmap control and space for the header bitmap on the right side.
; Default: ${NSISDIR}\Contrib\UIs\modern_headerbmpr.exe

; !define MUI_UI_COMPONENTSPAGE_SMALLDESC ui_file
; The interface files with a customized dialog resource IDD_SELCOM with a small description area.
; Default: ${NSISDIR}\Contrib\UIs\modern_smalldesc.exe

; !define MUI_UI_COMPONENTSPAGE_NODESC ui_file
; The interface files with a customized dialog resource IDD_SELCOM without a description area.
; Default: ${NSISDIR}\Contrib\UIs\modern_nodesc.exe

; Installer welcome/finish page
;----------------------------------
; !define MUI_WELCOMEFINISHPAGE_BITMAP bmp_file
; Bitmap for the Welcome page and the Finish page (recommended size: 164x314 pixels).
; Default: ${NSISDIR}\Contrib\Graphics\Wizard\win.bmp

; 	!define MUI_WELCOMEFINISHPAGE_BITMAP_NOSTRETCH
; Do not stretch the bitmap for the Welcome and Finish page to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; Uninstaller welcome/finish page
;----------------------------------
; !define MUI_UNWELCOMEFINISHPAGE_BITMAP bmp_file
; Bitmap for the Welcome page and the Finish page (recommended size: 164x314 pixels).
; Default: ${NSISDIR}\Contrib\Graphics\Wizard\win.bmp

; 	!define MUI_UNWELCOMEFINISHPAGE_BITMAP_NOSTRETCH
; Do not stretch the bitmap for the Welcome and Finish page to fit the size of the field. Use this option only if you have an image that does not use the whole space. If you have a full size bitmap that fits exactly, you should not use this option because the size of the field will be different if the user has a custom DPI setting.

; License page
;----------------------------------
; !define MUI_LICENSEPAGE_BGCOLOR (/windows | /grey | (color: RRGGBB hexadecimal))
; The background color for the license textbox. Use /windows for the Windows text background color (usually white). Use the /grey for the window background color (usually grey).
; Default: /windows


; Components page
;----------------------------------
; !define MUI_COMPONENTSPAGE_CHECKBITMAP bitmap_file
; The bitmap with images for the checks of the component select treeview.
; Default: ${NSISDIR}\Contrib\Graphics\Checks\modern.bmp

; !define MUI_COMPONENTSPAGE_SMALLDESC
; A small description area on the bottom of the page. Use this layout if you have a lot of sections and don't need large descriptions.

; !define MUI_COMPONENTSPAGE_NODESC
; No description area.

; Directory page
;----------------------------------
; !define MUI_DIRECTORYPAGE_BGCOLOR (color: RRGGBB hexadecimal)
; The background color for the directory textbox.

; Start Menu folder page
;----------------------------------
; !define MUI_STARTMENUPAGE_BGCOLOR (color: RRGGBB hexadecimal)
; The background color for the startmenu directory list and textbox.

; Installation page
;----------------------------------
; !define MUI_INSTFILESPAGE_COLORS (/windows | "(foreground color: RRGGBB hexadecimal) (background color: RRGGBB hexadecimal)")
; The colors of the details screen. Use /windows for the default Windows colors.
; Default: /windows

; !define MUI_INSTFILESPAGE_PROGRESSBAR ("" | colored | smooth)
; The style of the progress bar. Colored makes it use the MUI_INSTALLCOLORS.
; Default: smooth

; Installer finish page
;----------------------------------
!define MUI_FINISHPAGE_NOAUTOCLOSE
;	Do not automatically jump to the finish page, to allow the user to check the install log.

; Uninstaller finish page
;----------------------------------
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
;	Do not automatically jump to the finish page, to allow the user to check the uninstall log.

; Abort warning
;----------------------------------
!define MUI_ABORTWARNING
;	Show a message box with a warning when the user wants to close the installer.

; !define MUI_ABORTWARNING_TEXT text
; Text to display on the abort warning message box.

; !define MUI_ABORTWARNING_CANCEL_DEFAULT
; Set the Cancel button as the default button on the message box.

; Uninstaller abort warning
;----------------------------------
!define MUI_UNABORTWARNING
; Show a message box with a warning when the user wants to close the uninstaller.

; !define MUI_UNABORTWARNING_TEXT text
; Text to display on the abort warning message box.

; !define MUI_UNABORTWARNING_CANCEL_DEFAULT
; Set the Cancel button as the default button on the message box.

;--------------------------------------------
; Installer pages
!insertmacro	MUI_PAGE_WELCOME

!ifdef PROJECT_LICENSE_PATH
!insertmacro	MUI_PAGE_LICENSE	"${PROJECT_LICENSE_PATH}"
!endif
!insertmacro	MUI_PAGE_LICENSE	"${DIRECTXDIR}\Microsoft DirectX End-User Runtime License.rtf"

; !insertmacro	MUI_PAGE_COMPONENTS

!define 		MUI_DIRECTORYPAGE_VERIFYONLEAVE
!insertmacro	MUI_PAGE_DIRECTORY

!define			MUI_STARTMENUPAGE_DEFAULTFOLDER			"${DEFAULT_STARTMENU_FOLDER}"
!define			MUI_STARTMENUPAGE_REGISTRY_ROOT			"HKLM"
!define			MUI_STARTMENUPAGE_REGISTRY_KEY			"${UNINSTALLREGKEY}"
!define			MUI_STARTMENUPAGE_REGISTRY_VALUENAME	"StartMenuFolder"
!insertmacro	MUI_PAGE_STARTMENU Application	$StartMenuFolder

!insertmacro	MUI_PAGE_INSTFILES

; The "run" function is hijacked to optionally create a desktop shortcut instead.
; !define			MUI_FINISHPAGE
!define			MUI_FINISHPAGE_RUN					""
!define			MUI_FINISHPAGE_RUN_CHECKED
!define			MUI_FINISHPAGE_RUN_TEXT				"Create Desktop Shortcut"
!define			MUI_FINISHPAGE_RUN_FUNCTION			CreateDesktopShortcut
!insertmacro	MUI_PAGE_FINISH

;--------------------------------------------
; Uninstaller pages
!insertmacro	MUI_UNPAGE_WELCOME

!insertmacro	MUI_UNPAGE_CONFIRM

; !insertmacro	MUI_UNPAGE_LICENSE textfile

; !insertmacro	MUI_UNPAGE_COMPONENTS

; !insertmacro	MUI_UNPAGE_DIRECTORY

!insertmacro	MUI_UNPAGE_INSTFILES

!insertmacro	MUI_UNPAGE_FINISH

;--------------------------------------------
; Languages
!insertmacro MUI_LANGUAGE "English"

;--------------------------------------------
; Creates the desktop shortcut.
Function CreateDesktopShortcut
	SetShellVarContext	all
	CreateShortCut	"$DESKTOP\${PROJECT_NAME}.lnk"	"$INSTDIR\${EXE_NAME}"		"${SHORTCUT_EXE_ARGS}"	"$INSTDIR\${SHORTCUT_ICON}" "${SHORTCUT_ICON_INDEX}"
	SetShellVarContext	current
FunctionEnd

Function .onInit
	InitPluginsDir
!ifdef WINDOWS_86
	StrCpy $INSTDIR	"$PROGRAMFILES32\${DEFAULT_PROGRAMFILES_FOLDER}"
!else ifdef WINDOWS_64
	${If} ${RunningX64}
		StrCpy $INSTDIR	"$PROGRAMFILES64\${DEFAULT_PROGRAMFILES_FOLDER}"
	${Else}
		; Don't allow the installation of 64-bit game on 32-bit systems.
		MessageBox MB_ICONEXCLAMATION "This program requires a 64-bit operating system to run.  Aborting..."
		Abort
	${EndIf}
!else ifdef WINDOWS_86_64
	${If} ${RunningX64}
		StrCpy $INSTDIR	"$PROGRAMFILES64\${DEFAULT_PROGRAMFILES_FOLDER}"
	${Else}
		StrCpy $INSTDIR	"$PROGRAMFILES32\${DEFAULT_PROGRAMFILES_FOLDER}"
	${EndIf}
!endif
FunctionEnd

;--------------------------------------------
; Check for and require uninstallation of previous version.
!ifdef UNINSTALL_PREVIOUS_VERSION
Section "-Uninstall Previous Version"
	SectionIn RO
	SetShellVarContext	all
	push $0 ; install path
	push $1 ; uninstaller exe path
	push $2 ; temp uninstaller exe path
	push $3 ; uninstaller result
	DetailPrint "Checking for old version."
	ReadRegStr $0 HKLM  "${UNINSTALLREGKEY}" "InstallLocation"
	ClearErrors
	${If} $0 != ""
		DetailPrint "Previous version found at: $0"
		ReadRegStr $1 HKLM  "${UNINSTALLREGKEY}" "UninstallString"
		ClearErrors
		${If} $1 != ""
			DetailPrint "Uninstaller path: $1"
			; MessageBox MB_YESNO|MB_ICONQUESTION "A previous version of ${PROJECT_NAME} has been found. It is recommended that you uninstall it before installing this version.$\n$\nWould you like to uninstall the previous version now?" IDNO UninstallPreviousVersionUserAbort
			MessageBox MB_YESNO|MB_ICONQUESTION "A previous version of ${PROJECT_NAME} has been found and needs to be uninstalled before continuing this installation.$\n$\nDo you wish to continue?" IDYES +2
			Abort "User aborted uninstallation of previous version."
			DetailPrint "Uninstalling previous version."
			; Move the uninstaller to a temp file and run the temp file while pointing it to the install folder then delete the temp uninstaller.
			GetTempFileName $2
			CopyFiles $1 $2
			ExecWait '$2 /S _?=$0' $3
			Delete $2
			${If} $3 != 0
				Abort "Uninstallation of previous version failed with code $3"
			${EndIf}
			DetailPrint "Uninstall return code: $3"
		${Else}
			Abort "Could not find uninstaller for previous version."
		${EndIf}
	${EndIf}
	pop $3
	pop $2
	pop $1
	pop $0
	SetShellVarContext	current
SectionEnd
!endif

Section "-DirectX Runtime"
	; NOTE: This cannot be uninstalled.
	SectionIn RO
	SetShellVarContext all
	DetailPrint "Installing DirectX End-User Runtime files"
	File /oname=$PLUGINSDIR\DSETUP.dll "${DIRECTXDIR}\DSETUP.dll"
	File /oname=$PLUGINSDIR\dsetup32.dll "${DIRECTXDIR}\dsetup32.dll"
	File /oname=$PLUGINSDIR\DXSETUP.exe "${DIRECTXDIR}\DXSETUP.exe"
	File /oname=$PLUGINSDIR\dxupdate.cab "${DIRECTXDIR}\dxupdate.cab"
	File /oname=$PLUGINSDIR\dxdllreg_x86.cab "${DIRECTXDIR}\dxdllreg_x86.cab" ; Windows XP SP 1
	File /oname=$PLUGINSDIR\Jun2010_XAudio_x64.cab "${DIRECTXDIR}\Jun2010_XAudio_x64.cab"
	File /oname=$PLUGINSDIR\Jun2010_XAudio_x86.cab "${DIRECTXDIR}\Jun2010_XAudio_x86.cab"
	File /oname=$PLUGINSDIR\Oct2005_xinput_x64.cab "${DIRECTXDIR}\Oct2005_xinput_x64.cab"
	File /oname=$PLUGINSDIR\Oct2005_xinput_x86.cab "${DIRECTXDIR}\Oct2005_xinput_x86.cab"
	ExecWait '"$PLUGINSDIR\DXSETUP.exe" /silent' $0
	DetailPrint "Exit code: $0"
	SetShellVarContext	current
SectionEnd

Section "-Game"
	SectionIn RO
	SetShellVarContext all

	SetOutPath	"$INSTDIR"
	; Install the game files
	!ifdef WINDOWS_86_64
		${If} ${RunningX64}
			; Rename to the base EXE name so shortcuts, deletion, etc, can just use that name.
			File "/oname=${EXE_NAME}" "${RELEASE_FILE_PATH}\${EXE_NAME_64}"
		${Else}
	!endif
			File "${RELEASE_FILE_PATH}\${EXE_NAME}"
	!ifdef WINDOWS_86_64
		${EndIf}
	!endif
	!insertmacro InstallFiles
	SetOutPath	"$INSTDIR"

	; Create start menu shortcuts.
	!insertmacro MUI_STARTMENU_WRITE_BEGIN Application
		; TODO Allow for script-defined start menu items?
		CreateDirectory	"$SMPROGRAMS\$StartMenuFolder"
		CreateShortCut	"$SMPROGRAMS\$StartMenuFolder\${PROJECT_NAME}.lnk"				"$INSTDIR\${EXE_NAME}"		"${SHORTCUT_EXE_ARGS}"	"$INSTDIR\${SHORTCUT_ICON}" "${SHORTCUT_ICON_INDEX}"
		CreateShortCut	"$SMPROGRAMS\$StartMenuFolder\Uninstall ${PROJECT_NAME}.lnk"	"$INSTDIR\${UNINSTALL_EXE}"
		!ifmacrodef InstallStartMenuShortCuts
			!insertmacro InstallStartMenuShortCuts "$SMPROGRAMS\$StartMenuFolder"
		!endif
	!insertmacro MUI_STARTMENU_WRITE_END
	SetShellVarContext	current
SectionEnd

Section	"-CreateUninstaller"
	; https://nsis.sourceforge.io/mediawiki/index.php?title=Add_uninstall_information_to_Add/Remove_Programs&oldid=19858
	SectionIn RO
	SetShellVarContext all
	; Create Uninstaller
	WriteUninstaller	"$INSTDIR\${UNINSTALL_EXE}"
	; Store information for the Add/Remove Programs list.
	WriteRegStr		HKLM	"${UNINSTALLREGKEY}"		"DisplayName"		"${PROJECT_NAME}"
	!ifdef SHORTCUT_ICON
		WriteRegStr		HKLM	"${UNINSTALLREGKEY}"	"DisplayIcon"		"$INSTDIR\${SHORTCUT_ICON},${SHORTCUT_ICON_INDEX}"
	!endif
	WriteRegStr		HKLM	"${UNINSTALLREGKEY}"		"DisplayVersion"	"${PRODUCT_VERSION}"
	!ifdef HELPLINK
		WriteRegStr		HKLM	"${UNINSTALLREGKEY}"	"HelpLink"			"${HELPLINK}"
	!endif
	WriteRegStr		HKLM	"${UNINSTALLREGKEY}"		"InstallLocation"	"$INSTDIR"
	WriteRegDWORD	HKLM	"${UNINSTALLREGKEY}"		"NoModify"			${NOMODIFY}
	WriteRegDWORD	HKLM	"${UNINSTALLREGKEY}"		"NoRepair"			${NOREPAIR}
	WriteRegStr		HKLM	"${UNINSTALLREGKEY}"		"Publisher"			"${DEVELOPER_NAME}"
	WriteRegStr		HKLM	"${UNINSTALLREGKEY}"		"UninstallString"	"$INSTDIR\${UNINSTALL_EXE}"
	!ifdef URLINFOABOUT
		WriteRegStr		HKLM	"${UNINSTALLREGKEY}"	"URLInfoAbout"		"${URLINFOABOUT}"
	!endif
	!ifdef URLUPDATEINFO
		WriteRegStr		HKLM	"${UNINSTALLREGKEY}"	"URLUpdateInfo"		"${URLUPDATEINFO}"
	!endif
	WriteRegDWORD		HKLM	"${UNINSTALLREGKEY}"	"EstimatedSize"		"${ESTIMATEDSIZE}"
	
	SetShellVarContext	current
SectionEnd

;--------------------------------------------
; Uninstaller sections
Section	"un.Game"
	SectionIn RO ; Read only (always checked)
	SetShellVarContext all
	
	; Delete the game files.
	!insertmacro UninstallFiles
	Delete /REBOOTOK	"$INSTDIR\${EXE_NAME}"

	; Delete start menu shortcuts.
	!insertmacro MUI_STARTMENU_GETFOLDER	Application	$StartMenuFolder
	${If} $StartMenuFolder != ""
		!ifmacrodef UninstallStartMenuShortCuts
			!insertmacro UninstallStartMenuShortCuts "$SMPROGRAMS\$StartMenuFolder"
		!endif
		Delete	/REBOOTOK	"$SMPROGRAMS\$StartMenuFolder\${PROJECT_NAME}.lnk"
		Delete	/REBOOTOK	"$SMPROGRAMS\$StartMenuFolder\Uninstall ${PROJECT_NAME}.lnk"
		RMDir	/REBOOTOK	"$SMPROGRAMS\$StartMenuFolder"
		!ifdef INCLUDE_DEVELOPER_NAME_IN_PATHS
			RMDir	"$SMPROGRAMS\${DEVELOPER_NAME}"
			ClearErrors
		!endif
	${EndIf}
	; Delete the desktop shortcut
	Delete	/REBOOTOK	"$DESKTOP\${PROJECT_NAME}.lnk"
	; Delete uninstall information registry keys.
	DeleteRegKey	HKLM	"${UNINSTALLREGKEY}"
	; Delete the uninstaller.
	Delete	/REBOOTOK	"$INSTDIR\${UNINSTALL_EXE}"
	; Delete the install folder.
	RMDir	/REBOOTOK	"$INSTDIR"
	!ifdef INCLUDE_DEVELOPER_NAME_IN_PATHS
		!ifdef WINDOWS_86
			RMDir	"$PROGRAMFILES32\${DEVELOPER_NAME}"
		!else ifdef WINDOWS_64
			RMDir	"$PROGRAMFILES64\${DEVELOPER_NAME}"
		!else ifdef WINDOWS_86_64
			${If} ${RunningX64}
				RMDir	"$PROGRAMFILES64\${DEVELOPER_NAME}"
			${Else}
				RMDir	"$PROGRAMFILES32\${DEVELOPER_NAME}"
			${EndIf}
		!endif
		ClearErrors
	!endif
	SetShellVarContext	current
SectionEnd
