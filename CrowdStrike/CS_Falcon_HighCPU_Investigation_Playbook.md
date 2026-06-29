# CrowdStrike Falcon — High CPU Investigation Playbook

> **Two tracks. Same answer.**
> Track A when you have a diagnostic bundle. Track B when you're working live in the Falcon console.

---

## Table of Contents

1. [Overview](#overview)
2. [How the Analysis Works](#how-the-analysis-works)
3. [The Root Cause Pattern](#the-root-cause-pattern)
4. [Track A — Diagnostic Bundle](#track-a--diagnostic-bundle-investigation)
5. [Track B — Advanced Event Search](#track-b--advanced-event-search-aes)
6. [Applying the Fix — SVE](#applying-the-fix--sensor-visibility-exclusions)
7. [Quick Reference](#quick-reference)
8. [Notes and Adaptations](#notes-and-adaptations)

---

## Overview

Falcon high CPU is almost never a sensor bug. It is caused by **what Falcon is being asked to monitor**. The goal of this investigation is to identify what is generating the excessive process execution volume — and then either exclude it (if known-good automation) or investigate it (if unknown).

| Track | Use When |
|-------|----------|
| **Track A — Diagnostic Bundle** | You have a `.7z` bundle from the affected host |
| **Track B — Advanced Event Search** | No bundle available, or you want faster answers directly in the Falcon console |

Both tracks converge on the same answer. Choose based on what is available.

---

## How the Analysis Works

### The Three-File Method

The vendor methodology uses four files together to build a complete picture. Each file answers a specific question.

| File | Question It Answers |
|------|-------------------|
| `falcon-cstel_um.log` | How many process execs has Falcon monitored since startup? Are there BPF drops? |
| `perf_sched_report.txt` | Which specific processes are executing at high volume? |
| `perf_stats.txt` | Cross-validates the exec rate from an independent source |
| `ps-agxz.txt` | Which automation daemon is causing it? |

### The Math (Real Field Example)

```
From falcon-cstel_um.log:
  FALCON_MSG_EXEC : 7,246,855
  Process uptime  : 58,496 seconds  =  973 minutes
  Exec rate       : 7,246,855 ÷ 973  =  ~7,450 exec/min

Cross-check from perf_stats.txt:
  sched:sched_process_exec : 8,716 events in 59.7 seconds
  Exec rate                : ~8,760 exec/min

Normal server baseline     : ~200 exec/min
This host                  : ~43x above normal
```

Both sources agree within 20% — the rate is confirmed.

### The BPF Drop Signal

Inside `falcon-cstel_um.log` there is a `BPF Messages Dropped` counter. If this is **non-zero**:

- The process execution volume was so high that Falcon's own internal telemetry pipeline hit its rate limit
- Events were being lost inside the sensor — not just monitored slowly
- This is **definitive proof** the volume is the cause, not a sensor bug

> If you see BPF drops, stop looking for a sensor issue. Start looking for the automation source.

---

## The Root Cause Pattern

In the documented field case, the root cause followed this chain:

```
CUPS print jobs
    → Creates temp files in spool directory
        → incrond watches the directory, fires on every new file
            → Shell script executes
                → Script calls: date, cut, rev, dirname, basename...
                    → Falcon monitors every single exec
                        → CPU spike
```

With 70+ active print jobs constantly creating temporary files, these triggers were firing **thousands of times per minute**.

### How to Recognise This Pattern

| Signal Observed | What It Means |
|----------------|---------------|
| `date`, `cut`, `rev`, `dirname`, `basename` in top 10 by exec count | Shell script running in a loop — these utilities only appear at this frequency when called inside automation |
| All top processes are basic shell utilities | A single script is being called repeatedly, not many different applications |
| `incrond` or `crond` in `ps-agxz.txt` | Automation daemon is the trigger — watching a directory, firing on every file event |
| 70+ CUPS entries in `ps-agxz.txt` | Print spool is generating constant file events triggering the incron watch |
| `BPF Messages Dropped > 0` | Volume is definitively the cause — sensor pipeline is saturated |

---

## Track A — Diagnostic Bundle Investigation

### Step A1 — Extract the Bundle

The `[.7z](https://github.com/peeyushrao/peeyushrao.github.io/blob/main/Arsenal/Downloads/extract.zip)` contains nested archives. The structure is not predictable — always list before extracting.

```bash
# See what is inside first
python extract.py FR-XXXXX.7z --list

# Extract everything (files often have no extension — pattern matching misses them)
python extract.py FR-XXXXX.7z --all --save-to extracted
```

The extractor handles any nesting combination of `.7z` → `.tar.xz` → `.zip` → `.tar.gz` automatically using magic-byte detection, not file extensions.

---

### Step A2 — Open `falcon-cstel_um.log`

This is the most valuable file in the bundle. Search for the **BPF event counter section**:

```
CST/EventBus/BPF/
FALCON_MSG_EXEC
BPF Messages Dropped
uptime
```

Record these values:

| Value | Location |
|-------|----------|
| `FALCON_MSG_EXEC: N` | Under `CST/EventBus/BPF/` section |
| `BPF Messages Dropped: N` | Same section — **non-zero = volume is the cause** |
| `Process uptime: N seconds` | Same log — used to calculate exec/min |

Calculate exec rate:

```
exec_rate_per_min = FALCON_MSG_EXEC ÷ (uptime_seconds ÷ 60)

Example: 7,246,855 ÷ 973 = 7,450 exec/min
Normal:  ~200 exec/min
Ratio:   7,450 ÷ 200 = ~37x above normal
```

---

### Step A3 — Open `perf_sched_report.txt`

This captures 60 seconds of Linux scheduler events (`sched:sched_process_exec`). It tells you **which processes** are executing at high volume.

Look for:
- The total execution count at the top of the file
- The per-process breakdown sorted by execution count
- Whether the top 5–10 processes are basic shell utilities

**Red flag — this is the pattern to look for:**

```
Top processes by execution count (60-second window):
  date      — 2,962 times
  cut       — 2,577 times
  rev       — 1,614 times
  dirname   — 1,349 times
  basename  — 1,345 times
```

> These utilities have no standalone purpose at this frequency. They only appear in the top 10 when called repeatedly inside a shell script triggered by automation. This pattern immediately points to a script loop, not user activity.

---

### Step A4 — Cross-validate with `perf_stats.txt`

Search the file for:

```
sched:sched_process_exec
```

The line shows the count and elapsed time:

```
sched:sched_process_exec    8,716    [59.7 seconds]
```

Calculate: `8716 ÷ 59.7 × 60 = 8,760 exec/min`

If this matches your `falcon-cstel_um.log` figure within ~20%, the rate is confirmed from two independent sources.

---

### Step A5 — Open `ps-agxz.txt`

This connects the exec rate to the automation daemon causing it. Search for known automation daemons:

```
incrond
cupsd
nrpe
crond
anacron
```

Also count how many CUPS-related lines appear. **70+ CUPS entries alongside `incrond`** is the classic combination that produces this pattern — the print spool directory is the watched directory, and print jobs are the trigger.

---

### Step A6 — Check `top.txt`

This is a snapshot of Linux `top` at the moment the diagnostic was captured. Look at the `%CPU` column:

- Is Falcon (`falcond`, `csagent`) at the top?
- Is the automation daemon (`incrond`, `cupsd`) also elevated?
- Are there many short-lived shell utilities cycling through rapidly?

---

## Track B — Advanced Event Search (AES)

Navigate to: **Falcon Console → Investigate → Advanced Event Search**

> **Before running any query:** set the time range in the top-right. A 2-hour window is usually sufficient. Use several days for intermittent issues.
>
> **The `?aid` field:** do NOT replace it in the query text — AES will show a dedicated input field for it.

---

### Step B1 — Find the Most Active Processes

**Purpose:** Identify which executables are running at high frequency and what command lines they use.

**What to look for:** `date`, `cut`, `rev`, `basename`, `dirname`, `md5sum` appearing thousands of times.

**Action:** Note the full `ImageFileName` paths of suspicious processes — you need them for Step B3.

```
aid = ?aid (#event_simpleName = "ProcessRollup2" OR "ProcessRollup2Stats" OR "DeliverLocalFXToCloud")
| groupBy(
  field=["SHA256HashData", "CommandLine"],
  function=[
    collect(ImageFileName),
    groupBy(field="SHA256HashData",function=[count("ImageFileName", as="PRcount")]),
    sum("ProcessCount", as="Bounded")
  ], limit=max)
| eval("PR count"=PRcount)
| eval(Total=PRcount + Bounded)
| sort(Total, order=desc, limit=100)
| table([ImageFileName, CommandLine, "PR count", Bounded, Total], limit=100)
```

---

### Step B2 — Find Which Parent is Spawning the Most Children

**Purpose:** Identify the automation daemon responsible for launching all the high-frequency child processes.

**What to look for:** `incrond`, `cupsd`, `bash`, or `nrpe` with thousands of `ChildProcessCount`.

**Action:** Note the `ParentBaseFileName` values with the highest `ChildProcessCount` — you need them for Step B3.

```
aid=?aid (#event_simpleName = "ProcessRollup2" OR "SyntheticProcessRollup2")
| groupBy([ParentProcessId, ParentBaseFileName], function=[
    count(as="ChildProcessCount"),
    count(field=ImageFileName, distinct=true, as="UniqueChildTypes"),
    count(field=TargetProcessId, distinct=true, as="UniqueChildren"),
    collect(ImageFileName, limit=10)
])
| ChildProcessCount > 100
| sort(ChildProcessCount, order=desc, limit=100)
| table([ParentBaseFileName, ParentProcessId, ChildProcessCount, UniqueChildTypes, UniqueChildren, ImageFileName])
```

> Adjust the `ChildProcessCount > 100` threshold down to `50` on quiet servers where moderate automation is still significant.

---

### Step B3 — Map Parent-to-Child and Generate Process Explorer Links

**Purpose:** Confirm the relationship between parent and child processes. Generates clickable Process Explorer links.

**Before running — substitute these values:**

| Placeholder | Replace With |
|-------------|-------------|
| `ParentBaseFileName = "bash" OR "incrond" OR ...` | `ParentBaseFileName` values from Step B2 with high `ChildProcessCount` |
| `in(field=ImageFileName, values=[...])` | Full `ImageFileName` paths from Step B1 |
| `https://falcon.eu-1.crowdstrike.com/` | Change `eu-1` to your cloud region if needed (`us-1`, `us-2`, `gov`) |

```
aid=?aid (#event_simpleName = "ProcessRollup2" OR "SyntheticProcessRollup2")
| (ParentBaseFileName = "bash" OR ParentBaseFileName = "incrond"
   OR ParentBaseFileName = "crond" OR ParentBaseFileName = "cupsd"
   OR ParentBaseFileName = "nrpe")
| in(field=ImageFileName, values=["/usr/bin/rev", "/usr/bin/bash", "/usr/bin/tr",
   "/usr/bin/pgrep", "/usr/bin/groups", "/usr/libexec/platform-python3.6"])
| groupBy([ParentProcessId], function=[
    count(as="UtilityCallCount"),
    count(field=ImageFileName, distinct=true, as="UniqueUtils"),
    selectFromMax(field="@timestamp", include=[ComputerName, aid])
], limit=100000)
| UtilityCallCount > 5
| sort(UtilityCallCount, order=desc, limit=500)
| rootURL := "https://falcon.eu-1.crowdstrike.com/"
| format("[Process Explorer](%sgraphs/process-explorer/tree?id=pid:%s:%s)",
   field=["rootURL", "aid", "ParentProcessId"], as="Bash Parent")
| table([ComputerName, ParentProcessId, UtilityCallCount, UniqueUtils, "Bash Parent"], limit=500)
```

---

### Step B4 — Visually Confirm in Process Explorer

Click any **Process Explorer** link from the Step B3 output.

1. Click the `[+]` icon on any process node to expand its children
2. Continue expanding to trace the full chain: parent daemon → shell → utilities
3. This gives a visual confirmation you can share with application teams to explain the execution depth

---

## Applying the Fix — Sensor Visibility Exclusions

> **SVE is not the same as a Detection Exclusion.**
> SVE reduces sensor telemetry collection — it tells Falcon not to generate events for these processes.
> Use this when the process is confirmed known-good automation, not a potential threat.

### Correct SVE Configuration

| Setting | Correct Value |
|---------|--------------|
| Path (incrond) | `/usr/sbin/incrond` |
| Path (nrpe) | `/usr/sbin/nrpe` |
| Path (cupsd) | `/usr/sbin/cupsd` |
| Path (crond) | `/usr/sbin/crond` |
| Apply to descendant processes | **ENABLED — this is critical** |

---

### Mistake 1 — Wrong Path Format

```
# WRONG
/usr/sbin/incrond/**

# CORRECT
/usr/sbin/incrond
```

SVEs match against the **process image path**. The `/**` suffix tells Falcon to match paths *inside a directory called `incrond`*. That directory does not exist. The exclusion will never fire.

---

### Mistake 2 — Descendant Processes Not Enabled

Without **Apply to all descendant processes = YES**, Falcon still fully inspects every child process spawned by `incrond`.

The overhead comes **from the child processes** (`date`, `cut`, `rev`...), not from `incrond` itself. Excluding only the parent daemon has no measurable effect on CPU. This setting is mandatory — the exclusion is ineffective without it.

---

## Quick Reference

### Signal → Meaning

| Signal Observed | What It Means |
|----------------|---------------|
| `date`, `cut`, `rev` executing thousands of times | Shell script running in a loop or triggered too frequently |
| `incrond` with very high `ChildProcessCount` | Incron watching a high-traffic directory |
| `cupsd` generating many file events | Print queue creating temp files that trigger incron |
| High `UniqueChildTypes` from a single parent | Script spawns many different utilities per execution — examine the script |
| `BPF Messages Dropped > 0` | Volume is the cause — sensor pipeline overloaded, definitively not a bug |
| Exec rate > 10x baseline | Abnormal — investigate source even if individual utilities seem harmless |

---

### File Priority in Diagnostic Bundle

| Priority | File | What to Extract |
|----------|------|----------------|
| 1 — Start here | `falcon-cstel_um.log` | `FALCON_MSG_EXEC`, `BPF Messages Dropped`, uptime → exec/min rate |
| 2 — Identify culprit | `perf_sched_report.txt` | Per-process exec counts — look for shell utility pattern |
| 3 — Cross-validate | `perf_stats.txt` | `sched:sched_process_exec` count + elapsed → confirms rate |
| 4 — Find the source | `ps-agxz.txt` | Automation daemons, CUPS count |
| 5 — CPU snapshot | `top.txt` | Which process was at the top at capture time |
| 6 — Process tree | `pstree.txt` | Visualise parent → child chain |

---

### AES Query Sequence

| Step | Query Target | Output |
|------|-------------|--------|
| B1 | `ProcessRollup2` grouped by `SHA256 + CommandLine` | Top executables by frequency + command lines |
| B2 | Group by `ParentProcessId` | Which daemon is spawning the most children |
| B3 | Filter parent + child, generate links | Clickable Process Explorer links per offending parent |
| B4 | Process Explorer | Visual execution tree — confirms depth and chain |

---

## Notes and Adaptations

- **Time range:** 2 hours is sufficient in most cases. Use several days for intermittent issues.
- **ChildProcessCount threshold:** Default is `100`. Lower to `50` on quiet servers.
- **Cloud region:** Step B3 defaults to `eu-1`. Change to `us-1`, `us-2`, or `gov` as needed.
- **Multiple CIDs:** Run AES queries per CID. The `?aid` field scopes results to a single host.
- **Different daemon:** If `incrond` is not present but another daemon has high `ChildProcessCount` — apply the same logic. Find what directories it watches and what scripts it triggers.
- **Normal exec rate but CPU still high:** The cause is likely ML/behavioural analysis on a specific process, not exec volume. Use the Process Explorer to look for associated detections on that process.
- **SVE scope:** Apply exclusions at the host group level, not globally, until you have confirmed the behaviour is consistent across the group.

---

*CrowdStrike Falcon EDR — High CPU Diagnostic Playbook*
*Based on vendor field analysis methodology*
