@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Telefondan (Expo Go) kullanmak için: forumu ve Expo'yu iki ayrı pencerede başlatır.

echo Forum sunucusu yeni pencerede aciliyor...
start "Agora - forum sunucusu" cmd /k python calistir.py --ag --tarayici-acma

cd mobil-expo
if not exist node_modules (
  echo Ilk calistirma: Expo paketleri kuruluyor, birkac dakika surebilir...
  call npm install
)
echo Expo yeni pencerede aciliyor. QR kodu telefondaki Expo Go ile okut.
start "Agora - Expo" cmd /k npx expo start
