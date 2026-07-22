param([string]$QueueRoot = "V:\AI\Miller\.miller\gemma-queue", [int]$PollSec = 2)
$ErrorActionPreference='Stop'
$dirs=@('pending','running','completed','failed','logs','status') | % { Join-Path $QueueRoot $_ }
$dirs | % { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
$lock=Join-Path $QueueRoot 'status\supervisor.lock'
$mutex=[Threading.Mutex]::new($false,'Global\MillerGemmaSupervisor')
if(-not $mutex.WaitOne(0)){ exit 12 }
Get-ChildItem (Join-Path $QueueRoot 'running') -Filter *.json -ErrorAction SilentlyContinue | ForEach-Object {
  $j=Get-Content -Raw $_.FullName|ConvertFrom-Json; $h=[ordered]@{}; $j.psobject.Properties | % {$h[$_.Name]=$_.Value}; $h.finishTime=(Get-Date).ToUniversalTime().ToString('o'); $h.exitCode=125; $h.timeoutStatus=$false; $h.resultExists=Test-Path -LiteralPath $j.outputPath; $h.interruptedOnRestart=$true; $dest=Join-Path $QueueRoot "failed\$($_.BaseName).json"; $h|ConvertTo-Json -Depth 10|Set-Content $dest -Encoding UTF8; Remove-Item $_.FullName -Force
}
function Write-JsonAtomic($path,$obj){$tmp="$path.$PID.tmp"; $obj | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $tmp -Encoding UTF8; Move-Item -LiteralPath $tmp -Destination $path -Force}
function Heartbeat($msg){$h=[pscustomobject]@{pid=$PID;time=(Get-Date).ToUniversalTime().ToString('o');message=$msg}; Write-JsonAtomic (Join-Path $QueueRoot 'status\heartbeat.json') $h}
Set-Content $lock "$PID $(Get-Date -Format o)"; Heartbeat 'started'
try { while($true){
  Heartbeat 'polling'
  $jobPath=Get-ChildItem (Join-Path $QueueRoot 'pending') -Filter *.json | Sort-Object Name | Select-Object -First 1
  if($jobPath){
    $id=$jobPath.BaseName; $run=Join-Path $QueueRoot "running\$id.json"; Move-Item -LiteralPath $jobPath.FullName -Destination $run -Force
    $raw=Get-Content -Raw $run | ConvertFrom-Json; $job=[ordered]@{}; $raw.psobject.Properties | % {$job[$_.Name]=$_.Value}; $started=Get-Date; $job.startTime=$started.ToUniversalTime().ToString('o'); Write-JsonAtomic $run $job
    $log=Join-Path $QueueRoot "logs\$id.log"; Add-Content $log "[$(Get-Date -Format o)] START job=$id prompt=$($job.promptPath) output=$($job.outputPath) model=$($job.model) preDelaySec=$($job.preDelaySec)"
    if([int]$job.preDelaySec -gt 0){ for($i=0;$i -lt $job.preDelaySec;$i++){ Start-Sleep 1; if($i%10 -eq 9){Add-Content $log "[$(Get-Date -Format o)] heartbeat preDelay elapsed=$($i+1)"} } }
    $stdout=Join-Path $QueueRoot "logs\$id.stdout.txt"; $stderr=Join-Path $QueueRoot "logs\$id.stderr.txt"
    & pwsh -NoProfile -ExecutionPolicy Bypass -File (Join-Path $HOME 'gemma-worker.ps1') -PromptFile $job.promptPath -OutputFile $job.outputPath -Model $job.model -TimeoutSec ([int]$job.timeoutSec) -LogFile $log 1>$stdout 2>$stderr; $exit=$LASTEXITCODE
    $finished=Get-Date; $job.finishTime=$finished.ToUniversalTime().ToString('o'); $job.elapsedSec=[math]::Round(($finished-$started).TotalSeconds,2); $job.exitCode=$exit; $job.stdoutPath=$stdout; $job.stderrPath=$stderr; $job.timeoutStatus=($exit -ne 0 -and ((Get-Content $log -Raw) -match 'TIMEOUT')); $job.resultExists=Test-Path -LiteralPath $job.outputPath
    $dest=if($exit -eq 0 -and $job.resultExists){'completed'}else{'failed'}; Add-Content $log "[$(Get-Date -Format o)] worker_exit_code=$exit result_exists=$($job.resultExists) SUCCESS=$($dest -eq 'completed') elapsed=$($job.elapsedSec)"; Write-JsonAtomic (Join-Path $QueueRoot "$dest\$id.json") $job; Remove-Item -LiteralPath $run -Force
  } else { Start-Sleep $PollSec }
}}
finally { Heartbeat 'stopped'; Remove-Item $lock -Force -ErrorAction SilentlyContinue; $mutex.ReleaseMutex(); $mutex.Dispose() }
