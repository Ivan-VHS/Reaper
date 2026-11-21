param(
  [Parameter(Mandatory=$true)][string]$FilePath,
  [string[]]$Arguments = @(),
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [string]$ActionKey = "",
  [int]$StartupSeconds = 12
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class DesktopCaptureNative {
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
try { Set-DisplayResolution -Width 1920 -Height 1080 -Force -ErrorAction Stop } catch { Write-Warning "Runner resolution could not be changed; captured desktop will be normalized." }
$target = Join-Path (Get-Location) $OutputPath
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
$process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru -WindowStyle Normal
$handle = [IntPtr]::Zero
for ($i = 0; $i -lt ($StartupSeconds * 4); $i++) {
  Start-Sleep -Milliseconds 250
  $process.Refresh()
  if ($process.HasExited) { throw "Application exited before capture (code $($process.ExitCode))." }
  if ($process.MainWindowHandle -ne [IntPtr]::Zero) { $handle = $process.MainWindowHandle; break }
}
if ($handle -eq [IntPtr]::Zero) { throw "No visible application window was created by $FilePath." }
[void][DesktopCaptureNative]::ShowWindowAsync($handle, 3)
[void][DesktopCaptureNative]::SetForegroundWindow($handle)
Start-Sleep -Seconds 2
if ($ActionKey) { [System.Windows.Forms.SendKeys]::SendWait($ActionKey); Start-Sleep -Seconds 2 }
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$source = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($source)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap = New-Object System.Drawing.Bitmap(1920, 1080)
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$canvas.DrawImage($source, 0, 0, 1920, 1080)
$bitmap.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)
$canvas.Dispose(); $bitmap.Dispose(); $graphics.Dispose(); $source.Dispose()
Write-Host "Saved live desktop capture: $OutputPath (source: $($bounds.Width)x$($bounds.Height))."
try { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue } catch {}
