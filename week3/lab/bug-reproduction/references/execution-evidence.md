# Capture execution evidence

First obtain the real reproduction command from the repository and chosen harness. The examples below specify shell mechanics, not a language or test runner. Replace `REPRO_COMMAND` with the actual executable and arguments before running; do not evaluate untrusted text as a command. Run from the recorded working directory and select fresh output filenames to preserve earlier attempts.

## POSIX shell

```sh
mkdir -p evidence
pwd > evidence/run-cwd.txt
# Disable errexit in this subshell so an expected failure still records its code.
(
  set +e
  REPRO_COMMAND > evidence/run-output.txt 2>&1
  repro_status=$?
  printf '%s\n' "$repro_status" > evidence/run-exit.txt
  exit "$repro_status"
)
```

The subshell returns the actual command status. A caller using `set -e` may stop afterward; the output and code have already been saved. Do not use a logging pipeline whose exit code could be the logger's rather than the test's.

## PowerShell: native executable

```powershell
New-Item -ItemType Directory -Force evidence | Out-Null
(Get-Location).Path | Set-Content evidence/run-cwd.txt
$LASTEXITCODE = $null
REPRO_COMMAND > evidence/run-output.txt 2>&1
$reproStatus = $LASTEXITCODE
if ($null -eq $reproStatus) {
    throw 'No native process exit code captured; inspect command launch failure.'
}
$reproStatus | Set-Content evidence/run-exit.txt
Get-Content evidence/run-output.txt
Write-Output "Reproduction exit code: $reproStatus"
```

This records a native process status; it does not set the enclosing PowerShell process's exit code. In a dedicated runner script, end with `exit $reproStatus` when propagation is required. Cmdlets and PowerShell functions need their own success/error handling; do not reuse a stale native exit code for them. Preserve launch errors as setup evidence.

## Interpret and preserve

- Record the exact substituted command in the report, including executable version, arguments, configuration, and working directory. A command that did not reach the target is not a product test.
- Preserve special values and complete error messages. If serialization changes values, retain a human-readable output or explicit type marker.
- A nonzero code alone does not establish the reported bug: inspect whether it is an assertion, crash, launch error, or dependency failure. A zero code alone does not establish correctness.
- Keep raw evidence distinct from commentary and derived summaries. Redact credentials or personal data if present, marking omissions rather than silently changing results.
