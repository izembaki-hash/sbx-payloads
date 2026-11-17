# Re-plant the crafted download database and reboot the device.
# The device must be fully booted with a working network before itunesstored
# re-reads the database, otherwise its download tasks stall with -1009.

$ErrorActionPreference = 'Continue'
$UDID = '00008030-001C499814C0802E'
$AFC = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\afcclient.exe'
$SBX = 'E:\bypass\work\sbx'

Write-Host "== clear scratch + sidecars =="
foreach ($f in @('/Downloads/downloads.28.sqlitedb', '/Downloads/downloads.28.sqlitedb-wal',
                 '/Downloads/downloads.28.sqlitedb-shm')) {
    & $AFC -u $UDID rm $f 2>&1 | Out-Null
}
Write-Host "== plant crafted download database =="
& $AFC -u $UDID put "$SBX\crafted-downloads.28.sqlitedb" /Downloads/downloads.28.sqlitedb 2>&1 | Out-String -Width 120

Remove-Item 'E:\bypass\work\live\verifyC.sqlitedb' -ErrorAction SilentlyContinue
& $AFC -u $UDID get /Downloads/downloads.28.sqlitedb 'E:\bypass\work\live\verifyC.sqlitedb' 2>&1 | Out-Null
$deviceHash = (Get-FileHash -Algorithm SHA1 'E:\bypass\work\live\verifyC.sqlitedb').Hash
$craftedHash = (Get-FileHash -Algorithm SHA1 "$SBX\crafted-downloads.28.sqlitedb").Hash
Write-Host "device copy sha1 : $deviceHash"
Write-Host "crafted copy sha1: $craftedHash"
if ($deviceHash -ne $craftedHash) {
    Write-Host "MISMATCH - aborting reboot"
    exit 1
}

Write-Host "== reboot =="
python -m pymobiledevice3 diagnostics restart 2>&1 | Out-String -Width 120
Write-Host "restart issued at $(Get-Date -Format o)"
