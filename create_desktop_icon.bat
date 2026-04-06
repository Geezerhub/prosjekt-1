@echo off
setlocal

set "APP_DIR=%~dp0"
set "APP_SCRIPT=%APP_DIR%recipe_app.py"
set "SHORTCUT=%USERPROFILE%\Desktop\Oppskriftsapp.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ws = New-Object -ComObject WScript.Shell;" ^
"$s = $ws.CreateShortcut('%SHORTCUT%');" ^
"$s.TargetPath = 'pyw';" ^
"$s.Arguments = '""%APP_SCRIPT%""';" ^
"$s.WorkingDirectory = '%APP_DIR%';" ^
"$s.Description = 'Oppskriftsapp med forholdstall';" ^
"$s.Save();"

if %ERRORLEVEL% EQU 0 (
  echo Desktop-ikon opprettet: %SHORTCUT%
) else (
  echo Klarte ikke opprette desktop-ikon.
)

endlocal
