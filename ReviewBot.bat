@echo off
chcp 65001 > nul
title ReviewBot WB
color 0A

echo.
echo  ==========================================
echo   ReviewBot WB
echo  ==========================================
echo.

cd /d C:\DATA\PROJECTS\WB-Bot

call venv\Scripts\activate.bat

echo  Обновление из GitHub...
git fetch origin main --quiet 2>nul
git checkout origin/main -- ReviewBot.ico 2>nul
git pull origin main --quiet && echo   OK || echo   Нет интернета, работаем с локальной версией

powershell -NoProfile -Command "$d=[Environment]::GetFolderPath('Desktop');$lnk=$d+'\ReviewBot WB.lnk';$s=(New-Object -COM WScript.Shell).CreateShortcut($lnk);$s.TargetPath='%CD%\ReviewBot.bat';$s.IconLocation='%CD%\ReviewBot.ico,0';$s.WorkingDirectory='%CD%';$s.Save();Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $env:LOCALAPPDATA 'IconCache.db');Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Explorer') -Filter 'iconcache*' | Remove-Item -Force -ErrorAction SilentlyContinue" 2>nul

echo  Token check...
python -c "from dotenv import load_dotenv; import os, requests; load_dotenv(); t=os.getenv('WB_TOKEN','').strip(); r=requests.get('https://feedbacks-api.wildberries.ru/api/v1/feedbacks',headers={'Authorization':f'Bearer {t}'},params={'isAnswered':'false','take':1,'skip':0},timeout=15); print('  Token: OK' if r.status_code==200 else f'  Token: ERROR {r.status_code}')" 2>nul || echo   Token check skipped

echo.
echo  Server: http://127.0.0.1:8000
echo  Stop: Ctrl+C
echo.

start /b timeout /t 2 /nobreak >nul && start "" "%CD%\wb-reviewbot-v3.html"

python -m uvicorn web.app:app --host 127.0.0.1 --port 8000

pause
