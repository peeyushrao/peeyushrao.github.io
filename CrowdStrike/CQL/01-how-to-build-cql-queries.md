# How to Build CQL Queries: Discovery-First Methodology

CrowdStrike's Query Language (CQL/LQL — the syntax behind Falcon LogScale, Advanced Event Search, and Next-Gen SIEM) doesn't hand you a schema up front. Every `event_simpleName` carries its own fields, documentation lags behind what's actually in the platform, and guessing your way to a working query wastes cycles you don't get back. This post is the methodology: how to go from "I need to find X" to a query you actually trust.

---

## The Golden Rule: start with a tagged field

Before anything else, anchor the query to a tagged field — almost always `#event_simpleName`:

```lql
#event_simpleName=ProcessRollup2
```

Tagged fields let LogScale discard irrelevant data immediately instead of scanning everything and filtering after the fact. Every example in this post starts here for a reason — it's the difference between a query that returns in seconds and one that times out.

## Repository scoping matters as much as event type

It's tempting to search **All** repositories out of convenience. Don't. Endpoint telemetry and detections live in the **Falcon** repository specifically, and searching **All** forces a cross-repository scan:

| Scope | Typical execution time |
|---|---|
| Falcon repo | Seconds |
| All repositories | 10+ minutes |

Identify which repository your data lives in once (`Falcon`, `IT Automation`, `Third Party`, `Forensics`, `FCS Cloud Logs`, `Risks`, `Query Audit` are common ones in a Falcon tenant), then scope every subsequent query to it.

## Discover values with `groupBy()` before you filter on them

The second-biggest source of wasted time, after wrong field names, is **guessing field values**. A field like `Tactic` or `IOCSource` has a fixed, discoverable set of real values — don't filter on a value you assume exists.

Real example: building a scheduled report for "AI Powered IOA" detections. Rather than guess the exact filter values, discover them first:

```lql
#event_simpleName=AssociateTreeIdWithRoot
| match(file="falcon/investigate/detect_patterns.csv", field=[PatternId])
| show_in_ui="True"
| groupBy(Tactic)
```

This returns the actual tactic strings present in the data — in this case, confirming `AI Powered IOA` is the real value before it's ever used as a filter. The same pattern discovers `IOCSource` values once `Tactic` is locked in:

```lql
#event_simpleName=AssociateTreeIdWithRoot
| match(file="falcon/investigate/detect_patterns.csv", field=[PatternId])
| show_in_ui="True"
| Tactic="AI Powered IOA"
| groupBy(IOCSource)
```

**A hard-won lesson from this exact workflow:** applying `IOCSource="Anomalous process execution"` and `IOCType="Compounded behavioral activity"` returned zero results — both in LogScale and in the Falcon UI. That's not automatically a broken query. The validation sequence that confirms it:

| Validation step | Result | Conclusion |
|---|---|---|
| LogScale query | 0 results | Not a syntax problem |
| Falcon UI (same filters) | 0 results | Data absent |
| Query without the IOC filters | 42 detections | Data does exist |

> **Zero results in both LogScale and the Falcon UI usually means the data doesn't exist for that filter combination — not that the query is wrong.** Don't spend an hour debugging syntax before checking whether the filtered-out value was ever real to begin with.

## Understand the event before you query it: ProcessRollup2 fundamentals

`ProcessRollup2` (commonly "PR2") is the most important single event type in Falcon telemetry — generated whenever a process starts, and the foundation of process-tree reconstruction, threat hunting, and detection engineering. Three fields matter more than any others:

**`TargetProcessId_decimal`** — a Falcon-internal identifier, unique per process instance. Not the OS PID. Running the same binary twice produces two different `TargetProcessId_decimal` values even if the OS PIDs look similar.

**`ContextProcessId_decimal`** — every child event a process generates (DNS requests, network connections, file writes, registry changes) carries this field pointing back to the process that generated it. When `ContextProcessId_decimal == TargetProcessId_decimal`, the event belongs to that process.

**`ParentProcessId_decimal`** — links a process back to whatever created it: `Child.ParentProcessId_decimal == Parent.TargetProcessId_decimal`. This relationship is the foundation of every process-tree investigation.

Each platform's termination event differs, which matters if you're building lifecycle queries:

| Platform | Termination event |
|---|---|
| Windows | `EndOfProcess` |
| macOS | `EndOfProcess` |
| Linux | `TerminateProcess` |

For Linux and macOS, additional process detail often lives in a companion event, `ProcessRollup2Stats`, rather than `ProcessRollup2` itself — another reason to confirm which event actually carries the field you need before building around it.

## Build incrementally — a full worked example

Here's the complete build-up for hunting encoded PowerShell execution by SYSTEM, one clause at a time, exactly as it should be developed and tested:

**Step 1 — anchor to platform and event type:**
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
```

**Step 2 — narrow to PowerShell processes:**
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
```

**Step 3 — narrow to encoded command invocation:**
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
| CommandLine=/\-e(nc|ncodedcommand|ncoded)?\s+/i
```

**Step 4 — capture which flag variant was used, as a named field:**
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
| CommandLine=/\-(?<encodedFlagUsed>e(nc|ncodedcommand|ncoded)?)\s+/i
```

**Step 5 — restrict to SYSTEM context (`S-1-5-18`) if that's the hunt's focus:**
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
| CommandLine=/\-(?<encodedFlagUsed>e(nc|ncodedcommand|ncoded)?)\s+/i
| UserSid="S-1-5-18"
```

**Step 6 — aggregate and surface the rare cases**, which is usually where the actual hunting value is:
```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
| CommandLine=/\-(?<encodedFlagUsed>e(nc|ncodedcommand|ncoded)?)\s+/i
| groupBy([encodedFlagUsed, CommandLine], function=(count(aid, as=executionCount)))
| test(executionCount < 10)
| sort(executionCount, order=asc)
```

Every step was independently testable before adding the next — that's the discipline. If step 5 had returned nothing, the fix is a single-line rollback, not a full rewrite.

To keep long command lines readable in the output rather than blowing up the table view:

```lql
| format("%,.100s", field=CommandLine, as=CommandLine)
```

## Reference: frequently used event names

Worth keeping on hand rather than re-discovering every time:

| Category | Events |
|---|---|
| Process | `ProcessRollup2`, `SyntheticProcessRollup2`, `EndOfProcess` |
| File | `FileCreateInfo`, `FileDeleteInfo`, `FileRenameInfo`, `FileWritten` |
| Network | `DnsRequest`, `NetworkConnectIP4` |
| Registry | `AsepKeyUpdate`, `AsepValueUpdate`, `RegGenericValueUpdate`, `RegSystemConfigValueUpdate` |
| Device | `DcUsbDeviceConnected` |
| Snapshot | `VolumeSnapshotCreated`, `VolumeSnapshotDeleted` |
| Detection | `ProcessBlocked`, `AssociateIndicator`, `AssociateTreeIdWithRoot` |

And the single query that answers "what event types am I even generating" when you don't know where to start:

```lql
#repo="base_sensor"
| groupBy([#event_simpleName], function=count(), limit=1000)
| sort(field=#event_simpleName, type=string, order=ascending, limit=1000)
```

## Query-time variables: build it once, reuse it forever

Once a query works, the next question is whether it needs to be rebuilt every time for a different host, user, or filter value — or whether it should become a reusable dashboard tile. LogScale supports query parameters (`?FieldName`) that render as fill-in-the-blank fields in the Search UI:

```lql
#repo = "base_sensor" ComputerName=?HostName #event_simpleName=InstalledApplication
| Time:=formatTime(format="%Y-%m-%d %H:%M:%S%p", field=@timestamp, timezone="CET")
| table([Time, event_platform, ComputerName, UserName, AppName, AppPath, AppVendor, AppVersion], sortby=Time, order=desc)
```

Anything you find yourself editing by hand and re-running with a new hostname or username each time is a candidate for this treatment.

## Takeaways

1. Anchor every query to a tagged field, almost always `#event_simpleName`.
2. Scope to the correct repository — searching **All** is 10x–100x+ slower than a targeted repo.
3. Discover field *values* with `groupBy()` before filtering on them — don't guess.
4. Zero results validated in both the query tool and the source UI means the data isn't there, not that the query is broken.
5. Know the three process-linking fields (`TargetProcessId_decimal`, `ContextProcessId_decimal`, `ParentProcessId_decimal`) before building anything process-tree related.
6. Build one clause at a time, test at each step, and only widen scope once each stage is confirmed.
7. Once a query works and you find yourself re-running it with different values, convert it to a query-parameter version.

Next up: [Security queries](02-security-cql-queries.md) — hunting and detection engineering built on this methodology, and [General-purpose queries](03-general-purpose-cql-queries.md) — fleet inventory, upgrade tracking, and capacity reporting.
