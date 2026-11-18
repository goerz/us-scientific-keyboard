@echo off
rem Build the keyboard layout DLL for x64, x86, x86-on-64-bit (WOW64), and
rem ARM64 with the Visual Studio C++ build tools.
rem
rem Requirements: Visual Studio 2022 or later, or the free "Build Tools for
rem Visual Studio", with the workload "Desktop development with C++" plus the
rem components "MSVC ... ARM64/ARM64EC build tools" and a Windows 11 SDK.
rem
rem Usage: build.cmd   (from a normal Command Prompt, in this directory)

setlocal
cd /d "%~dp0"
set NAME=@@DLL@@

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo ERROR: Visual Studio or the Build Tools for Visual Studio are not installed.
    exit /b 1
)
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
if not defined VSDIR (
    echo ERROR: The C++ build tools are missing from the Visual Studio installation.
    exit /b 1
)
set "VCVARS=%VSDIR%\VC\Auxiliary\Build\vcvarsall.bat"

rem vcvarsall argument for each target, depending on the host CPU
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set HOST_X64=arm64_x64
    set HOST_X86=arm64_x86
    set HOST_ARM64=arm64
) else (
    set HOST_X64=x64
    set HOST_X86=x64_x86
    set HOST_ARM64=x64_arm64
)

call :build x64   %HOST_X64%   X64   ""                || exit /b 1
call :build x86   %HOST_X86%   X86   ""                || exit /b 1
call :build wow64 %HOST_X86%   X86   "/DBUILD_WOW6432" || exit /b 1
call :build arm64 %HOST_ARM64% ARM64 ""                || exit /b 1

echo.
echo Built %NAME%.dll in x64\, x86\, wow64\, and arm64\.
echo To install, run in an Administrator PowerShell:
echo     powershell -ExecutionPolicy Bypass -File install.ps1
exit /b 0

:build
rem %1 output directory, %2 vcvarsall argument, %3 linker machine, %4 extra cl flags
rem Windows loads layout DLLs with file offsets equal to memory offsets
rem (/FILEALIGN:0x1000) and the tables in .data, as in its own layout DLLs.
setlocal
echo.
echo === %1 ===
call "%VCVARS%" %2 > nul || exit /b 1
if not exist %1 mkdir %1
cl /nologo /c /O1 /GS- /Zl /W3 /utf-8 %~4 /Fo%1\%NAME%.obj %NAME%.c || exit /b 1
rc /nologo /fo %1\%NAME%.res %NAME%.rc || exit /b 1
link /nologo /DLL /NOENTRY /NODEFAULTLIB /SUBSYSTEM:NATIVE /FILEALIGN:0x1000 /MERGE:.rdata=.data /MACHINE:%3 /DEF:%NAME%.def /OUT:%1\%NAME%.dll %1\%NAME%.obj %1\%NAME%.res || exit /b 1
del %1\%NAME%.obj %1\%NAME%.res %1\%NAME%.lib %1\%NAME%.exp 2> nul
endlocal
exit /b 0
