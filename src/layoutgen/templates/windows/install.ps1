# Install or uninstall the "@@NAME@@" keyboard layout.
#
# Run in an Administrator PowerShell, in the directory that holds the x64\,
# x86\, wow64\, and arm64\ build folders:
#
#     powershell -ExecutionPolicy Bypass -File install.ps1
#     powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall
#
# Sign out and back in afterwards.

param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'

$Dll = '@@DLL@@.dll'
$Text = '@@NAME@@'
$Lang = '0409'  # English (United States)
$LayoutsKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Keyboard Layouts'

$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script in an Administrator PowerShell.'
}
if ([Environment]::Is64BitOperatingSystem -and -not [Environment]::Is64BitProcess) {
    throw 'Run this script in 64-bit PowerShell, not the (x86) version.'
}

$System32 = Join-Path $env:SystemRoot 'System32'
$SysWOW64 = Join-Path $env:SystemRoot 'SysWOW64'

# Registry keys of this layout from earlier installs
$existing = @(Get-ChildItem $LayoutsKey | Where-Object {
    (Get-ItemProperty $_.PSPath).'Layout File' -eq $Dll
})

function Remove-FromLanguageList([string[]]$Klids) {
    $list = Get-WinUserLanguageList
    foreach ($language in $list) {
        foreach ($klid in $Klids) {
            $tip = "${Lang}:$($klid.ToUpper())"
            while ($language.InputMethodTips.Remove($tip)) { }
        }
    }
    Set-WinUserLanguageList $list -Force
}

if ($Uninstall) {
    $klids = $existing | ForEach-Object { $_.PSChildName }
    if ($klids) { Remove-FromLanguageList $klids }
    $existing | ForEach-Object { Remove-Item $_.PSPath -Recurse }
    foreach ($dir in @($System32, $SysWOW64)) {
        $path = Join-Path $dir $Dll
        if (Test-Path $path) {
            try { Remove-Item $path }
            catch { Write-Warning "$path is in use; sign out and run the uninstall again to delete it." }
        }
    }
    Write-Host "Uninstalled $Text. Sign out and back in to finish."
    exit 0
}

# DLLs for this machine: System32 gets the native build, SysWOW64 the
# 32-bit build with 64-bit pointers (WOW64) used by 32-bit programs.
$arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
switch ($arch) {
    'X64'   { $copies = @{ 'x64' = $System32; 'wow64' = $SysWOW64 } }
    'Arm64' { $copies = @{ 'arm64' = $System32; 'wow64' = $SysWOW64 } }
    'X86'   { $copies = @{ 'x86' = $System32 } }
    default { throw "Unsupported architecture: $arch" }
}
foreach ($build in $copies.Keys) {
    $source = Join-Path (Join-Path $PSScriptRoot $build) $Dll
    if (-not (Test-Path $source)) { throw "Missing $source; run build.cmd first." }
    $target = Join-Path $copies[$build] $Dll
    try { Copy-Item $source $target -Force }
    catch {
        # A loaded DLL can't be overwritten, but it can be renamed.
        $old = "$target.old-$(Get-Date -Format yyyyMMddHHmmss)"
        Rename-Item $target $old
        Copy-Item $source $target
        Write-Warning "Replaced a DLL that was in use; delete $old after signing out."
    }
}

if ($existing) {
    $key = $existing[0].PSPath
    $klid = $existing[0].PSChildName
} else {
    # Layout identifier: a....0409, unique among installed layouts
    $klid = $null
    for ($i = 1; $i -le 0xfff; $i++) {
        $candidate = ('a{0:x3}{1}' -f $i, $Lang)
        if (-not (Test-Path (Join-Path $LayoutsKey $candidate))) { $klid = $candidate; break }
    }
    if (-not $klid) { throw 'No free keyboard layout identifier.' }
    # "Layout Id" must be unique across all layouts; stay below 0x1000.
    $used = Get-ChildItem $LayoutsKey | ForEach-Object {
        $id = (Get-ItemProperty $_.PSPath).'Layout Id'
        if ($id) { [Convert]::ToInt32($id, 16) }
    }
    $layoutId = $null
    for ($i = 0xc0; $i -le 0xfff; $i++) {
        if ($used -notcontains $i) { $layoutId = '{0:x4}' -f $i; break }
    }
    if (-not $layoutId) { throw 'No free Layout Id.' }
    $key = Join-Path $LayoutsKey $klid
    New-Item $key | Out-Null
    New-ItemProperty $key -Name 'Layout Id' -Value $layoutId -PropertyType String | Out-Null
}
Set-ItemProperty $key -Name 'Layout File' -Value $Dll
Set-ItemProperty $key -Name 'Layout Text' -Value $Text
Set-ItemProperty $key -Name 'Layout Display Name' -Value "@%SystemRoot%\system32\$Dll,-1000"

# Add the layout to the current user's English (United States) input methods
$list = Get-WinUserLanguageList
$language = $list | Where-Object { $_.LanguageTag -eq 'en-US' } | Select-Object -First 1
if (-not $language) {
    $list.Add('en-US')
    $language = $list | Where-Object { $_.LanguageTag -eq 'en-US' } | Select-Object -First 1
}
$tip = "${Lang}:$($klid.ToUpper())"
if (-not $language.InputMethodTips.Contains($tip)) {
    $language.InputMethodTips.Add($tip)
    Set-WinUserLanguageList $list -Force
}

Write-Host "Installed $Text ($klid)."
Write-Host 'Sign out and back in, then switch layouts with Win+Space.'
