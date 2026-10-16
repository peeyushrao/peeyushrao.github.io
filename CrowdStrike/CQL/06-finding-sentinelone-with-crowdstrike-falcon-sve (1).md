# Finding SentinelOne on Your Fleet with CrowdStrike Falcon (and Turning It into an SVE)

> A practical workflow: confirm SentinelOne is present on a host, size the problem fleet-wide with Falcon queries, extract the exact install directories, and convert them into a tight Sensor Visibility Exclusion (SVE).

**Scope note:** The queries use Falcon Advanced Event Search (LogScale syntax). Field names, event availability and retention differ between tenants and licences, so always run a query on a small sample before trusting the output.

---

## Why this matters

Two EDR agents on one host is one of the most common causes of high CPU, driver conflicts and unexplained telemetry gaps. Before you can fix it you need three answers:

1. **Which hosts** have SentinelOne (S1)?
2. **Where** is it installed (exact directories)?
3. **What exclusion** should Falcon carry so the two agents stop fighting?

This article walks through those three questions in order.

---

## Step 1 - Check a single host

### Windows (PowerShell)

```powershell
Get-Service Sentinel* | Select Name,Status,StartType
Get-Process Sentinel* -ErrorAction SilentlyContinue
Test-Path "C:\Program Files\SentinelOne"
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*, HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* |
  Where-Object DisplayName -match "Sentinel" | Select DisplayName,DisplayVersion
```

Typical services: `SentinelAgent`, `SentinelHelperService`, `SentinelStaticEngine`, `LogProcessorService`.
Typical kernel drivers: `SentinelMonitor.sys`, `SentinelELAM.sys`.

### Linux

```bash
systemctl status sentinelone
/opt/sentinelone/bin/sentinelctl control status
```

### macOS

```bash
sudo sentinelctl status
ls /Library/Sentinel
```

### Through Falcon Real Time Response (RTR)

~~~
ls "C:\Program Files\SentinelOne"
reg query HKLM\SYSTEM\CurrentControlSet\Services\SentinelAgent
runscript -Raw=```Get-Service Sentinel* | ft -auto```
~~~

---

## Step 2 - Find every host, fleet-wide

### Query 1: process-based (Windows)

```
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\(SentinelAgent|SentinelServiceHost|SentinelStaticEngine|SentinelStaticEngineScanner|SentinelHelperService|SentinelUI|SentinelCtl)\.exe$/i
| match(file="aid_master_main.csv", field=[aid], include=[ComputerName], strict=false)
| groupBy([aid, ComputerName], function=[count(as=Events), min(@timestamp, as=FirstSeen), max(@timestamp, as=LastSeen)])
| formatTime("%Y-%m-%d %H:%M:%S", field=FirstSeen, as=FirstSeen)
| formatTime("%Y-%m-%d %H:%M:%S", field=LastSeen, as=LastSeen)
```

**Linux / macOS variant:**

```
#event_simpleName=ProcessRollup2 event_platform=/^(Lin|Mac)$/
| ImageFileName=/sentinelone|sentinelctl|sentineld/i
| groupBy([aid], function=[count(as=Events)])
```

### Query 2: driver-based

Useful when the S1 service is stopped but its driver is still loaded.

```
#event_simpleName=DriverLoad ImageFileName=/Sentinel(Monitor|ELAM)/i
| groupBy([aid, ImageFileName])
```

### Query 3: installed-application inventory

Longer lookback than process telemetry, so it catches "installed but idle" hosts.

```
#event_simpleName=InstalledApplication AppName=/sentinel/i
| groupBy([aid, AppName, AppVendor, AppVersion])
```

Verify the field names against a sample event in your tenant. Alternatively, use **Exposure Management > Applications** (formerly Discover) and search for "Sentinel Agent". That is the quickest way to export a host list for a coexistence or uninstall cleanup.

---

## Step 3 - Find the directories S1 is using

Say Query 1 returned 41 hosts. You do not need 41 rows of exclusions, you need the handful of unique directories. Group by path instead of by host.

### 3a. Directory of each S1 process

```
#event_simpleName=ProcessRollup2
| ImageFileName=/\\(SentinelAgent|SentinelServiceHost|SentinelStaticEngine|SentinelStaticEngineScanner|SentinelHelperService|SentinelUI|SentinelCtl)\.exe$/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Exe], function=[count(field=aid, distinct=true, as=Hosts), count(as=Events)])
```

### 3b. Directory of each S1 driver

```
#event_simpleName=DriverLoad ImageFileName=/Sentinel/i
| regex("^(?<Directory>.+)\\\\(?<Driver>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Driver])
```

### 3c. Catch-all: anything running out of an S1 folder

This finds helper binaries whose names you did not anticipate.

```
#event_simpleName=ProcessRollup2 ImageFileName=/\\(SentinelOne|Sentinel Agent[^\\]*)\\/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Exe])
```

### What the output looks like

Falcon reports paths in **device-path format**, which is also the format SVE patterns use:

```
\Device\HarddiskVolume3\Program Files\SentinelOne\Sentinel Agent 23.4.5.226\SentinelAgent.exe
\Device\HarddiskVolume3\Program Files\SentinelOne\Sentinel Agent 23.4.5.226\SentinelStaticEngine.exe
\Device\HarddiskVolume3\Windows\System32\drivers\SentinelMonitor.sys
```

Two things to notice:

- The **volume number** (`HarddiskVolume3`) differs per host.
- The agent folder is **versioned** (`Sentinel Agent 23.4.5.226`) and changes on every S1 upgrade.

An exclusion that hard-codes either of those will silently stop working.

---

## Step 4 - Build the SVE

In the console: **Endpoint Security > Exclusions > Sensor Visibility Exclusions > Create exclusion** (menu names shift between console releases).

Wildcard the volume and cover the version folder and its children:

```
\Device\HarddiskVolume*\Program Files\SentinelOne\**
```

Or, if you want to pin the versioned folder explicitly:

```
\Device\HarddiskVolume*\Program Files\SentinelOne\Sentinel Agent *\**
```

Also check whether your Step 3 results show `\ProgramData\Sentinel\**` and add it if so. The driver in `System32\drivers` is shared with other software, so exclude the specific file only if you really need to.

**Scope it:** apply the exclusion to the host group holding the hosts from Step 2, not to all hosts.

Confirm wildcard behaviour (`*` versus `**`) against Falcon's current exclusion documentation and test on a pilot group before broad rollout.

---

## Step 5 - Validate

1. Apply the SVE to a small pilot group (3 to 5 hosts).
2. After the policy has propagated, re-run Query 1 restricted to the pilot hosts and a time window **after** the change. New S1 process events should stop appearing.
3. Compare CPU on the pilot hosts before and after, if performance was the original complaint.
4. Roll out to the full host group once satisfied, and record the pattern, scope, owner and reason.

---

## Caveats worth remembering

- **Retention:** process telemetry in Advanced Event Search has limited retention (it depends on your licence and any long-term storage). A dormant S1 agent may not appear in process events. Prefer the driver and inventory queries for "installed but idle".
- **Tamper protection:** while S1 is active, its passphrase-protected uninstall is the usual blocker. Hand the host list to whoever owns the S1 console.
- **An SVE reduces visibility:** Falcon stops collecting telemetry and detections for the excluded paths. Keep patterns as narrow as possible and never exclude broad locations such as `Program Files\**`.
- **SVE is one direction only:** it removes Falcon's monitoring of S1 processes. It does nothing about S1's own hooks on Falcon, so it may reduce a CPU or driver conflict without curing it. The permanent fix is retiring one of the two agents.
- **Scanning is separate:** to stop Falcon *scanning* those files you need an **ML exclusion** (and an **IOA exclusion** if IOAs are firing on them). SVE does not cover either.
- **Consider mutual exclusions:** vendors usually recommend excluding each agent's folders in the other product. Check S1's own exclusion settings for Falcon's directories.

---

## Cheat sheet

| Goal | Query focus |
|---|---|
| Which hosts run S1? | `ProcessRollup2` filtered on S1 image names, grouped by `aid` |
| Installed but not running? | `DriverLoad` on `SentinelMonitor` / `SentinelELAM`, or `InstalledApplication` |
| Which directories? | Same filters plus `regex()` to split `Directory` / `Exe`, grouped by directory |
| Hidden helper binaries? | Path-based match on `\SentinelOne\` or `\Sentinel Agent*\` |
| Exclusion pattern | `\Device\HarddiskVolume*\Program Files\SentinelOne\**` scoped to a host group |
| Did it work? | Re-run process query after the change, expect no new events on pilot hosts |
