$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Build command failed: $LASTEXITCODE" } }
python -m pip install -r requirements.txt
Check-Exit
python -m pip install 'pyinstaller>=6,<7' xlrd pywin32-ctypes
Check-Exit
npm ci --prefix frontend
Check-Exit
npm run build --prefix frontend
Check-Exit
python -m unittest discover -s tests -v
Check-Exit
python -m PyInstaller --noconfirm --clean --onedir --windowed --name AuthorScopeScreening --paths . --add-data 'frontend/dist;frontend/dist' --collect-all keyring --hidden-import keyring.backends.Windows --hidden-import win32ctypes.pywin32.win32cred --hidden-import openpyxl --hidden-import xlrd distribution/launcher.py
Check-Exit
Copy-Item distribution/QUICKSTART.txt dist/AuthorScopeScreening/READ_ME_FIRST.txt
$testRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$testHome = Join-Path $testRoot 'author-screening-smoke'
$oldHome = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = $testHome
    $marker = Join-Path $testHome 'AuthorScopeScreening/smoke-test-ok.txt'
    if (Test-Path $marker) { Remove-Item $marker }
    $process = Start-Process dist/AuthorScopeScreening/AuthorScopeScreening.exe -ArgumentList '--smoke-test' -PassThru
    if (!$process.WaitForExit(120000)) { $process.Kill(); throw 'Packaged app smoke test timed out' }
    if ($process.ExitCode -ne 0 -or !(Test-Path $marker)) { throw 'Packaged app smoke test failed' }
} finally { $env:LOCALAPPDATA = $oldHome }
Compress-Archive -Path dist/AuthorScopeScreening -DestinationPath dist/AuthorScopeScreening-Windows-x64-portable.zip -Force
