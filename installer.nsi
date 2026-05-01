!define PRODUCT_NAME "Naughty Cat"
!define PRODUCT_VERSION "0.1.0"
!define PRODUCT_PUBLISHER "Naughty Cat"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "NaughtyCat-Setup.exe"
InstallDir "$PROGRAMFILES\NaughtyCat"
RequestExecutionLevel admin

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\NaughtyCat\*.*"

    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Naughty Cat.lnk" "$INSTDIR\NaughtyCat.exe"

    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd
