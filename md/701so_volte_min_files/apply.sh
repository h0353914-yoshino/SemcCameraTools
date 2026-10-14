#!/bin/bash
# 把最小 VoLTE 集合(6 檔)用 diag 寫入 701SO。需：Magisk root、Windows 端 python+pyserial、.tmp/diag_efs_batch.py 與 diag_efs_read.py
# 步驟：切 diag → 寫入並讀回驗證 → 等 65 秒落盤 → 重開機 → 開機後到 設定→行動網路→進階 觸發註冊
A="/mnt/f/Android/platform-tools/adb.exe -s BH904YZF9A"
PY=/mnt/c/Users/h035/AppData/Local/Python/pythoncore-3.14-64/python.exe
HERE=$(cd "$(dirname "$0")" && pwd)
W=/mnt/c/Users/h035/volte_min; rm -rf $W; mkdir -p $W; cp $HERE/* $W/
cp /home/h/tmp/SemcCameraUI/.tmp/diag_efs_batch.py /home/h/tmp/SemcCameraUI/.tmp/diag_efs_read.py /mnt/c/Users/h035/
$A push /home/h/tmp/SemcCameraUI/.tmp/usb_diag_on_long.sh /data/local/tmp/ >/dev/null
$A shell "su -c 'sh /data/local/tmp/usb_diag_on_long.sh'"; sleep 10
P=$(powershell.exe -NoProfile -Command "(Get-PnpDevice -PresentOnly | Where-Object { \$_.FriendlyName -like '*Diagnostics*' }).FriendlyName" | tr -d '\r' | grep -oE 'COM[0-9]+' | head -1)
sed 's# # volte_min/#' $W/manifest.txt > /mnt/c/Users/h035/volte_min_manifest.txt
(cd /mnt/c/Users/h035 && timeout 120 $PY diag_efs_batch.py $P volte_min_manifest.txt)
echo "等 65 秒讓 modem 快取落盤..."; sleep 65
$A shell "su -c 'setprop sys.usb.config adb'"; $A reboot
