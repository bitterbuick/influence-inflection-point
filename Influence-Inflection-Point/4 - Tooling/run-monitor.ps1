# run-monitor.ps1
# Weekly Common Crawl monitor via Docker. Ephemeral container, persistent ./io.
# Register this with Windows Task Scheduler on a weekly trigger.
#
#   Register-ScheduledTask -TaskName "IIP-CC-Monitor" `
#     -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 3am) `
#     -Action  (New-ScheduledTaskAction -Execute "powershell.exe" `
#                 -Argument "-ExecutionPolicy Bypass -File `"$PWD\run-monitor.ps1`"")
#
# The monitor deliberately does NOT use --gate: a scheduled job must not fail on a hit.
# Use the manual gate command for pre-experiment validation (see the Tracker note / README).

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Io   = Join-Path $Root "io"
$Logs = Join-Path $Io "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$Stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
$Log   = Join-Path $Logs "monitor-$Stamp.log"

Write-Host "Running CC monitor; artifacts -> $Io\runs ; log -> $Log"

# --- Snapshot drift detection --------------------------------------------------
# Probe live indexes and alert if new CC snapshots have appeared since last run.
$SnapshotFile = Join-Path $Io "known-snapshots.txt"
try {
    $IndexOut  = docker run --rm corpus-presence-tracker:1.1 --list-indexes 2>&1
    $LiveSnaps = @($IndexOut |
        Select-String 'cc_\d{4}_\d{2}' |
        ForEach-Object { $_.Matches[0].Value } |
        Sort-Object -Unique)
    if ($LiveSnaps.Count -gt 0) {
        if (Test-Path $SnapshotFile) {
            $KnownSnaps = @(Get-Content $SnapshotFile | Where-Object { $_ -ne '' })
            $NewSnaps   = @($LiveSnaps | Where-Object { $_ -notin $KnownSnaps })
            if ($NewSnaps.Count -gt 0) {
                $Msg = "WARNING: new CC snapshot(s) detected -- update CC_INDEXES in corpus_presence_tracker.py: $($NewSnaps -join ', ')"
                Write-Host $Msg
                $Msg | Out-File -FilePath $Log -Encoding utf8
            }
        }
        $LiveSnaps | Set-Content $SnapshotFile
    }
} catch {
    Write-Host "Snapshot check failed (non-fatal): $_"
}
# ------------------------------------------------------------------------------

docker run --rm `
  -v "${Io}:/data" `
  corpus-presence-tracker:1.1 `
  --entities entities/watchlist.csv --cc-only --out runs *>&1 |
  Tee-Object -FilePath $Log -Append

# --- Obsidian report ----------------------------------------------------------
# Build a Markdown pivot table from the latest run CSV and write it to the vault
# so Obsidian can display it without any plugins.
try {
    $ReportDir = Join-Path $Root "Monitor Reports"
    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

    $LatestCsv = Get-ChildItem (Join-Path $Io "runs") -Filter "*.csv" |
        Sort-Object LastWriteTime -Desc |
        Select-Object -First 1

    if ($LatestCsv) {
        $Data     = Import-Csv $LatestCsv.FullName
        $RunId    = $Data[0].run_id
        # Parse date/time from ISO string directly to avoid locale issues
        $RunDate  = $Data[0].queried_at.Substring(0, 10)
        $RunTime  = $Data[0].queried_at.Substring(11, 5) -replace ':', ''

        # CC snapshots only (exclude pretraining corpora: pile_train, dolma, redpajama, c4_train)
        $CcCorpora = @($Data |
            Where-Object { $_.corpus -match '^(cc_|dclm_)' } |
            Select-Object -ExpandProperty corpus -Unique |
            Sort-Object)
        $Entities = @($Data | Select-Object -ExpandProperty entity -Unique)

        # Markdown table
        $Header = "| Entity | " + ($CcCorpora -join " | ") + " |"
        $Sep    = "| --- |" + (($CcCorpora | ForEach-Object { " --- |" }) -join "")

        $Rows = foreach ($Entity in $Entities) {
            $Counts = foreach ($Corpus in $CcCorpora) {
                $Row = $Data | Where-Object { $_.entity -eq $Entity -and $_.corpus -eq $Corpus }
                if ($Row -and $Row.count -ne '') { $Row.count } else { '--' }
            }
            "| $Entity | " + ($Counts -join " | ") + " |"
        }

        $TableBlock = $Header + "`n" + $Sep + "`n" + ($Rows -join "`n")

        $EmDash    = [char]0x2014
        $MdContent = "---`ntags:`n  - iip/monitor`nrun_id: $RunId`ndate: $RunDate`ntype: cc-only`n---`n`n# CC Monitor $EmDash $RunDate`n`n$TableBlock`n"

        $MdPath = Join-Path $ReportDir "cc-monitor-${RunDate}-${RunTime}.md"
        [System.IO.File]::WriteAllText($MdPath, $MdContent, [System.Text.Encoding]::UTF8)
        Write-Host "Obsidian report -> $MdPath"
        Add-Content -Path $Log -Value "Obsidian report -> $MdPath"
    }
} catch {
    Write-Host "Report generation failed (non-fatal): $_"
}
# ------------------------------------------------------------------------------
