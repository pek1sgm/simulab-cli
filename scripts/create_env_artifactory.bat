@echo off
setlocal

set /p "USERNAME=Artifactory-Benutzername: "
set /p "PASSWORD=Artifactory-Passwort/Token: "

setx UV_INDEX_SIMULABCLI_USERNAME "%USERNAME%" >nul
setx UV_INDEX_SIMULABCLI_PASSWORD "%PASSWORD%" >nul

echo Done!
echo Please open a new terminal session.