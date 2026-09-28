# Falcon Playbook: Find Any Software, Extract Its Directories, Build an SVE

> A reusable version of the SentinelOne workflow. Fill in the placeholders for whatever software you are investigating (another EDR, a backup agent, a monitoring agent, a line-of-business app) and run the same series.

**Scope note:** Queries use Falcon Advanced Event Search (LogScale syntax). Field names, event availability and retention vary by tenant. Test on a sample first.

---

## 1. Placeholders

Decide these before you start. Every query below uses them.

| Placeholder | Meaning | SentinelOne example |
|---|---|---|
| `<PROC_REGEX>` | Regex matching the process image names | `\\(SentinelAgent\|SentinelStaticEngine\|SentinelHelperService)\.exe$` |
| `<DRIVER_REGEX>` | Regex matching kernel driver names | `Sentinel(Monitor\|ELAM)` |
| `<APP_REGEX>` | Regex matching the product name in inventory | `sentinel` |
| `<PATH_REGEX>` | Regex matching the install folder in a path | `\\(SentinelOne\|Sentinel Agent[^\\]*)\\` |

How to get these values: check one host by hand (services, install folder, `Add/Remove Programs`, vendor docs) and take the process, driver and vendor names from there. Start broad, then tighten after you see real results. If the software is obscure and you cannot fill these in yet, start at **Step 0** below.

---

## 2. The workflow

```
(Seed, if unknown)  ->  Identify  ->  Scope  ->  Locate  ->  Normalize  ->  Draft  ->  Pilot  ->  Roll out  ->  Document
```

### Step 0 - Unknown software: build the footprint from a seed host

Use this when you cannot fill in the placeholders yet, because the product is obscure or you know only its name. Learn the footprint on one host that has it, then pivot to the fleet. Once you have confirmed process, driver and path values, continue at Step A.

**0.1 Pick a seed host.** Get one from the vendor's installer, a ticket, the user who reported it, or **Exposure Management > Applications** (search the product or vendor name). Note its `aid`.

**0.2 Ask the host what it is.** On the seed host, locally or via RTR. Replace `acme` with the product name, vendor name or a fragment of the install folder:

```powershell
Get-CimInstance Win32_Service | Where-Object { $_.PathName -match 'acme' } | Select Name,State,PathName
Get-CimInstance Win32_SystemDriver | Where-Object { $_.PathName -match 'acme' } | Select Name,PathName
Get-ScheduledTask | Where-Object { $_.TaskPath -match 'acme' -or $_.TaskName -match 'acme' }
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*, HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* |
  Where-Object DisplayName -match 'acme' | Select DisplayName,Publisher,InstallLocation
```

The uninstall key's `InstallLocation` and `Publisher` are usually the fastest anchors.

**0.3 Ask Falcon what the seed host did.** This shows what the installer dropped and what autostarts:

```
aid=<SEED_AID> #event_simpleName=/^(ProcessRollup2|DriverLoad|NewExecutableWritten|AsepValueUpdate)$/
| coalesce([ImageFileName, TargetFileName], as=Path)
| Path!=/\\Windows\\|\\Microsoft/i
| groupBy([#event_simpleName, Path])
```

If you can install the software on a test machine, run this over the install window for a cleaner picture. Event names and fields vary by tenant, so check them against a sample first.

**0.4 Combined discovery query (fleet-wide).** One table showing directory, file, event type and prevalence for anything matching your string. Replace `<STRING>` with a product, vendor or folder fragment:

```
#event_simpleName=/^(ProcessRollup2|DriverLoad|NewExecutableWritten)$/
| coalesce([ImageFileName, TargetFileName], as=Path)
| Path=/<STRING>/i or CommandLine=/<STRING>/i
| regex("^(?<Directory>.+)\\\\(?<File>[^\\\\]+)$", field=Path)
| groupBy([Directory, File, #event_simpleName], function=[count(field=aid, distinct=true, as=Hosts), count(as=Events)])
| sort(Hosts, order=desc)
```

`CommandLine` exists only on process events, so the `or` clause matters only for `ProcessRollup2`.

**0.5 Use prevalence to confirm.** Compare the `Hosts` column with the host count from **Exposure Management > Applications**:

- If Applications shows about 40 hosts, the real components should appear on about 40 hosts.
- A file on thousands of hosts is likely a Windows or shared component. Leave it out of the exclusion.
- A file on one or two hosts is likely noise or a different product.

**0.6 Close the gaps.** Take the trusted directory and feed it into the catch-all and "children outside the install folder" queries in Step C. They find helper processes living in `ProgramData`, `Temp` or `System32`.

**Tips for obscure software**

- **Start narrow.** Exclude the specific executable path first and widen to the folder once the pilot is stable. Too narrow is easy to fix. Too wide hides real activity.
- **Check the vendor's documentation** for recommended AV/EDR exclusions and compare with what you found.
- **Verify the binaries.** Check the file signature and hash reputation before excluding anything, so you do not create a blind spot for malware using a similar name.
- **Record how you found it.** Note the seed host, queries and prevalence numbers in the change record.

### Step A - Identify: which hosts have it?

**Process-based:**

```
#event_simpleName=ProcessRollup2
| ImageFileName=/<PROC_REGEX>/i
| match(file="aid_master_main.csv", field=[aid], include=[ComputerName], strict=false)
| groupBy([aid, ComputerName], function=[count(as=Events), min(@timestamp, as=FirstSeen), max(@timestamp, as=LastSeen)])
```

**Driver-based** (catches stopped services with loaded drivers):

```
#event_simpleName=DriverLoad ImageFileName=/<DRIVER_REGEX>/i
| groupBy([aid, ImageFileName])
```

**Inventory-based** (longer lookback, catches installed-but-idle):

```
#event_simpleName=InstalledApplication AppName=/<APP_REGEX>/i
| groupBy([aid, AppName, AppVendor, AppVersion])
```

Also available in the console: **Exposure Management > Applications**.

### Step B - Scope: how big and how varied is it?

Split by platform and version to see whether one exclusion will cover everything.

```
#event_simpleName=ProcessRollup2
| ImageFileName=/<PROC_REGEX>/i
| groupBy([event_platform], function=[count(field=aid, distinct=true, as=Hosts)])
```

### Step C - Locate: which directories?

**Directory per process:**

```
#event_simpleName=ProcessRollup2
| ImageFileName=/<PROC_REGEX>/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Exe], function=[count(field=aid, distinct=true, as=Hosts), count(as=Events)])
```

**Directory per driver:**

```
#event_simpleName=DriverLoad ImageFileName=/<DRIVER_REGEX>/i
| regex("^(?<Directory>.+)\\\\(?<Driver>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Driver])
```

**Catch-all: everything executing from the vendor folder:**

```
#event_simpleName=ProcessRollup2 ImageFileName=/<PATH_REGEX>/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Exe])
```

**Children that live outside the install folder.** Helper binaries spawned by the product often run from `ProgramData`, `Temp` or `System32`:

```
#event_simpleName=ProcessRollup2 ParentBaseFileName=/<PARENT_NAME_REGEX>/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| groupBy([Directory, Exe], function=[count(field=aid, distinct=true, as=Hosts)])
```

Here `<PARENT_NAME_REGEX>` is a regex on the parent process file name, for example `^SentinelAgent\.exe$`.

### Step D - Normalize: remove the parts that change

Falcon returns device paths such as:

```
\Device\HarddiskVolume3\Program Files\Vendor\Product 4.2.1.117\agent.exe
```

Two parts of that path are unstable and will break an exclusion:

1. **Volume number:** replace with `HarddiskVolume*`.
2. **Version folder:** replace with `*`, or exclude the parent folder.

To see how many distinct *patterns* you really have, collapse the volume and version before grouping:

```
#event_simpleName=ProcessRollup2
| ImageFileName=/<PROC_REGEX>/i
| regex("^(?<Directory>.+)\\\\(?<Exe>[^\\\\]+)$", field=ImageFileName)
| replace("HarddiskVolume\\d+", with="HarddiskVolume*", field=Directory, as=Pattern)
| replace("\\d+(\\.\\d+){2,}", with="*", field=Pattern, as=Pattern)
| groupBy([Pattern], function=[count(field=aid, distinct=true, as=Hosts)])
```

Escaping inside `replace()` can be finicky between versions. Check the output on a sample before relying on it.

### Step E - Draft the SVE

Build the narrowest pattern that covers the normalized directories:

```
\Device\HarddiskVolume*\Program Files\<Vendor>\**
```

Linux and macOS paths have no device prefix:

```
/opt/<vendor>/**
/Library/<Vendor>/**
```

Rules of thumb:

- Exclude the **vendor folder**, not its parent.
- Exclude **specific files** for shared locations (`System32\drivers\<file>.sys`), never the whole folder.
- Scope to the **host group** from Step A, not all hosts.
- Confirm `*` versus `**` behaviour in current Falcon exclusion documentation.

### Step F - Pilot

1. Apply to 3 to 5 representative hosts (different OS builds, one server if servers are in scope).
2. After propagation, re-run Step A restricted to those hosts and a window after the change. Events for the excluded paths should stop.
3. If the original problem was performance, compare CPU before and after.

### Step G - Roll out and document

Use the record template in section 5.

---

## 3. Which exclusion type do you need?

| Goal | Exclusion type |
|---|---|
| Stop Falcon collecting telemetry and detections for these processes or paths | **Sensor Visibility Exclusion (SVE)** |
| Stop Falcon machine-learning scanning and blocking of these files | **ML exclusion** |
| Stop specific IOA detections or preventions firing on this behaviour | **IOA exclusion** |

SVE does not imply the other two. A path that is only in the SVE can still be scanned or blocked, and vice versa.

---

## 4. When not to write an exclusion

- **The vendor publishes Falcon-specific guidance.** Follow it and compare to your results.
- **The path is broad or attacker-friendly:** `Temp`, `Downloads`, `ProgramData\**`, `Users\**`, or general-purpose binaries such as `powershell.exe` and `cmd.exe`. An SVE there is a blind spot an attacker can use.
- **The software is a remote-admin or dual-use tool.** Fix the underlying conflict or approve it through a narrower control instead.
- **You only need to know what is installed.** Use the inventory query and stop there.

---

## 5. Change record template

```
Software:            <name, vendor, version range>
Reason:              <conflict / performance / false positives, with evidence>
Hosts affected:      <count and host group name>
Evidence queries:    <Step A and Step C queries, run date>
Exclusion type(s):   <SVE / ML / IOA>
Pattern(s):          <exact patterns>
Scope:               <host group>
Pilot result:        <date, hosts, outcome>
Owner and review:    <who owns it, review date>
Rollback:            <how to remove it>
```

---

## 6. Worked examples (starting points only)

These are illustrative starting values. Always confirm them against your own Step C results before writing patterns.

| Software | Typical process names | Typical install location |
|---|---|---|
| SentinelOne | `SentinelAgent.exe`, `SentinelStaticEngine.exe`, `SentinelHelperService.exe` | `Program Files\SentinelOne\Sentinel Agent <ver>\` |
| Microsoft Defender for Endpoint | `MsSense.exe`, `SenseIR.exe`, `MsMpEng.exe`, `NisSrv.exe` | `Program Files\Windows Defender Advanced Threat Protection\`, `ProgramData\Microsoft\Windows Defender\Platform\<ver>\` |
| Trellix ENS / ePO agent | `masvc.exe`, `macmnsvc.exe`, `mfemms.exe`, `mfetp.exe` | `Program Files\McAfee\`, `Program Files\Common Files\McAfee\` |
| Splunk Universal Forwarder | `splunkd.exe`, `splunk-*.exe` | `Program Files\SplunkUniversalForwarder\` |

For each row, run Step C and the "children outside the install folder" query. The second one usually reveals the extra path that a first-pass exclusion misses.

---

## 7. One-page checklist

- [ ] (Unknown software) Seed host chosen and footprint built with Step 0
- [ ] Placeholders filled in from a manual check of one host
- [ ] Host list built from process, driver and inventory queries
- [ ] Directories extracted and grouped
- [ ] Volume and version normalized
- [ ] Children outside the install folder checked
- [ ] Pattern is as narrow as possible, scoped to a host group
- [ ] Right exclusion type(s) chosen (SVE / ML / IOA)
- [ ] Pilot validated with a post-change query
- [ ] Change record filed and review date set
