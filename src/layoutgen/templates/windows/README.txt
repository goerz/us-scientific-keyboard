@@NAME@@: native Windows keyboard layout
================================================================

This folder contains the source of a native Windows keyboard layout DLL,
generated from the macOS layout. It has everything except the math bold,
math script, and double-struck alphabets, which Windows dead keys cannot
produce. The full layout is available for Windows through Keyman.

Build
-----

1. Install the free "Build Tools for Visual Studio" (or Visual Studio) from
   https://visualstudio.microsoft.com/downloads/ . In the installer, select
   the workload "Desktop development with C++" and, under "Individual
   components", "MSVC ... ARM64/ARM64EC build tools (Latest)".
2. Open a Command Prompt in this folder and run build.cmd. It creates
   x64\, x86\, wow64\, and arm64\ folders with @@DLL@@.dll.

Install
-------

1. Open PowerShell as Administrator and change to this folder.
2. Run:  powershell -ExecutionPolicy Bypass -File install.ps1
3. Sign out and back in. Switch to the layout with Win+Space.

The Option key on the Mac corresponds to the right Alt key (AltGr).

Uninstall
---------

Run:  powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall
and sign out and back in.
