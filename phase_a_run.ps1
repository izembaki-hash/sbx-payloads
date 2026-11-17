# Phase A runner: capture syslog across the reboot that makes itunesstored and
# bookassetd re-read the planted download database, then report what happened.

$ErrorActionPreference = 'Continue'
$UDID = '00008030-001C499814C0802E'
$AFC = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\afcclient.exe'
$SYSLOG = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\idevicesyslog.exe'
$SBX = 'E:\bypass\work\sbx'
$LOG = 'E:\bypass\work\live\phaseA.log'
$ERR = 'E:\bypass\work\live\phaseA.err'

Remove-Item $LOG, $ERR -ErrorAction SilentlyContinue
New-Item -ItemType File -Path "$SBX\empty.bin" -Force | Out-Null

Write-Host "== clear stale WAL/SHM =="
foreach ($f in @('/Downloads/downloads.28.sqlitedb-wal', '/Downloads/downloads.28.sqlitedb-shm')) {
    & $AFC -u $UDID rm $f 2>&1 | Out-Null
    & $AFC -u $UDID put "$SBX\empty.bin" $f 2>&1 | Out-String -Width 120
}

Write-Host "== verify planted DB =="
Remove-Item 'E:\bypass\work\live\verify-planted.sqlitedb' -ErrorAction SilentlyContinue
& $AFC -u $UDID get /Downloads/downloads.28.sqlitedb 'E:\bypass\work\live\verify-planted.sqlitedb' 2>&1 | Out-Null
Write-Host ("device copy sha1 : " + (Get-FileHash -Algorithm SHA1 'E:\bypass\work\live\verify-planted.sqlitedb').Hash)
Write-Host ("crafted copy sha1: " + (Get-FileHash -Algorithm SHA1 "$SBX\crafted-downloads.28.sqlitedb").Hash)

Write-Host "== syslog capture + reboot =="
$end = (Get-Date).AddSeconds(280)
while ((Get-Date) -lt $end) {
    & $SYSLOG -u $UDID *>> $LOG
    Start-Sleep -Seconds 3
}
Write-Host "capture stopped, size=$((Get-Item $LOG).Length)"
