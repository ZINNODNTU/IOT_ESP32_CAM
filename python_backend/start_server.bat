@echo off
echo ========================================
echo KHOI DONG SERVER ATTENDAI IOT (Windows)
echo ========================================
echo.

echo [1] Kiem tra Python version...
python --version

echo.
echo [2] Kiem tra cac thu vien...
python -c "import tornado; import cv2; import numpy; print('✅ Tat ca thu vien da cai dat')"

echo.
echo [3] Khoi dong server tren port 3000...
echo    - IP Local: 192.168.5.183
echo    - URL: http://192.168.5.183:3000
echo    - WebSocket: ws://192.168.5.183:3000/ws
echo.

echo [4] Neu ESP32 khong ket noi duoc:
echo    - Sua file Arduino: ws_url = "ws://192.168.5.183:3000/ws"
echo    - Dam bao ESP32 va PC cung mang WiFi
echo.

echo [5] Bat dau khoi dong server...
python websockets_stream.py

pause