# CrowdStrike Falcon CQL: A Practical Beginner-to-Intermediate Field Guide

**For:** SOC analysts, EDR investigators, threat hunters, and Falcon administrators  
**Focus:** Falcon LogScale / Advanced Event Search using CrowdStrike Query Language (CQL)  
**Revision:** 2026-10-24  
**Prerequisites:** Access to a LogScale repository containing relevant events. This guide does **not** assume a particular tenant, license, data connector, or parser.

> **How to use this guide:** Run the *discovery* queries first. Confirm that the named event types and fields exist in **your** dataset. Then run the investigation examples. Queries are examples and have not been executed against your Falcon tenant.

---

## Table of contents

1. [Mental model: events, fields, tags, and queries](#1-mental-model-events-fields-tags-and-queries)
2. [Your first CQL search](#2-your-first-cql-search)
3. [Core syntax and functions](#3-core-syntax-and-functions)
4. [Three event-identification fields: `#event_simpleName`, `EventType`, `ExternalApiType`](#4-three-event-identification-fields)
5. [Discover your event inventory](#5-discover-your-event-inventory)
6. [Falcon sensor event families](#6-falcon-sensor-event-families)
7. [Essential fields for investigations](#7-essential-fields-for-investigations)
8. [Understanding process identity and relationships](#8-understanding-process-identity-and-relationships)
9. [Understanding `PatternDisposition`](#9-understanding-patterndisposition)
10. [Investigating endpoint detection summaries](#10-investigating-endpoint-detection-summaries)
11. [Walkthrough: Falcon killed a process](#11-walkthrough-falcon-killed-a-process)
12. [Threat-hunting query cookbook](#12-threat-hunting-query-cookbook)
13. [CQL aggregation and reporting](#13-cql-aggregation-and-reporting)
14. [Data sources and schema differences](#14-data-sources-and-schema-differences)
15. [Mistakes, caveats, and troubleshooting](#15-mistakes-caveats-and-troubleshooting)
16. [Practice exercises and learning path](#16-practice-exercises-and-learning-path)
17. [Cheat sheet](#17-cheat-sheet)
18. [Sources and verification notes](#18-sources-and-verification-notes)

---

## 1. Mental model: events, fields, tags, and queries

### What is CQL?

**CrowdStrike Query Language (CQL)** is the search and analysis language used by **Falcon LogScale**, including the LogScale-backed search experience in Falcon. You use it to filter, transform, correlate, summarize, and visualize event data.

A useful analogy:

- An **event** is one recorded observation.
- A **field** describes an attribute of that observation.
- A **field value** is the actual value in that record.
- A **query** finds and processes matching observations.
- A **repository** is where event data is stored; the selected repository and time range determine what the query can see.

Example event (illustrative, simplified):

```text
@timestamp           2026-10-24T08:30:00Z
#event_simpleName    ProcessRollup2
aid                  endpoint-123
ImageFileName        C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
CommandLine          powershell.exe -NoProfile
TargetProcessId      123456789
```

The query:

```cql
#event_simpleName=ProcessRollup2
```

asks for events whose tagged event name is `ProcessRollup2`.

### Three categories of fields

| Kind | Typical notation | Meaning |
|---|---|---|
| Metadata | `@timestamp`, `@rawstring` | LogScale-managed event metadata |
| Indexed tags | `#event_simpleName`, `#repo` | Parser-defined tags; `#` is part of query syntax |
| Parsed data | `aid`, `CommandLine`, `ExternalApiType` | Actual attributes extracted from source data |

**Important:** The `#` before `#event_simpleName` is **not** a count operator. It identifies an indexed tag. Whether a given field is tagged is determined by ingestion and parsing.

### An essential distinction

A **detection** is a higher-level security finding. **Sensor telemetry** represents observed activity, such as process creation or a network connection. A **platform audit event** represents administrative or user activity in Falcon.

One detection may relate to multiple telemetry events. One incident may produce multiple detections. Consequently:

**Number of event records ≠ number of distinct processes ≠ number of detections ≠ number of incidents.**

---

## 2. Your first CQL search

Start small.

### Step 1: Show process events

```cql
#event_simpleName=ProcessRollup2
```

### Step 2: Restrict to Windows

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
```

Writing conditions next to one another means **AND**.

### Step 3: Find PowerShell

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell\.exe$/i
```

The regex searches for an executable path ending with `\powershell.exe`; `/i` means case-insensitive.

### Step 4: Select useful columns

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell\.exe$/i
| table([@timestamp, aid, ImageFileName, CommandLine, TargetProcessId])
```

### Step 5: Group repeated observations

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell\.exe$/i
| groupBy([aid, ImageFileName], function=count(as=Executions))
| sort(Executions, order=desc)
```

The output is now aggregated: one row per host and executable path, rather than one row per event.

**Tip:** Set a reasonable time range in the search UI (for example, 24 hours) before beginning. Increase it deliberately.

---

## 3. Core syntax and functions

### 3.1 Filter expressions

```cql
// Exact match
#event_simpleName=ProcessRollup2

// Implicit AND
#event_simpleName=ProcessRollup2 event_platform=Win

// OR, with parentheses to avoid ambiguity
#event_simpleName=ProcessRollup2
| (ImageFileName=/\\cmd\.exe$/i OR ImageFileName=/\\powershell\.exe$/i)

// Field existence
CommandLine=*

// Case-insensitive regex match
CommandLine=/encodedcommand/i
```

Queries are evaluated in stages. Use parentheses when combining alternatives with other conditions. Parentheses avoid silently broadening the result set.

### 3.2 The pipe operator: `|`

The pipe passes the events produced by one stage to the next:

```cql
#event_simpleName=ProcessRollup2
| event_platform=Win
| table([@timestamp, aid, ImageFileName, CommandLine])
| sort(@timestamp, order=desc)
```

A filter can appear before or after a pipe. Functions such as `table()` and `groupBy()` commonly appear after a pipe.

### 3.3 Select columns: `table()`

```cql
#event_simpleName=ProcessRollup2
| table([@timestamp, aid, ImageFileName, CommandLine])
```

This changes the displayed columns; it does not mean that only those fields existed in the original events.

### 3.4 Sort: `sort()`

```cql
#event_simpleName=ProcessRollup2
| sort(@timestamp, order=desc)
```

`desc` sorts newest/highest first; `asc` sorts oldest/lowest first.

### 3.5 Count events: `count()`

```cql
#event_simpleName=ProcessRollup2
| count(as=TotalProcessEvents)
```

This counts matching **event records**, not necessarily unique processes or files.

### 3.6 Group data: `groupBy()`

```cql
#event_simpleName=ProcessRollup2
| groupBy([aid, ImageFileName], function=count(as=Executions), limit=max)
| sort(Executions, order=desc)
```

`limit=max` permits more groups than the usual default, but larger grouping results can cost more time and resources.

### 3.7 Count distinct values

```cql
#event_simpleName=ProcessRollup2
| count(aid, distinct=true, as=DistinctHosts)
```

Distinct host identifiers differ from distinct event counts.

### 3.8 Collect example values

```cql
#event_simpleName=ProcessRollup2
| groupBy(aid, function=[count(as=Events), collect(ImageFileName, limit=10)])
```

Collections are useful for seeing examples, but do not confuse the list of collected values with a complete inventory unless the collection limit and data volume are considered.

### 3.9 Rename or calculate a field

```cql
#event_simpleName=ProcessRollup2
| ProcessPath := ImageFileName
| table([aid, ProcessPath, CommandLine])
```

`:=` assigns a new value to a field within the query's result pipeline. It does **not** modify stored source data.

### 3.10 Multi-value matching with `in()`

```cql
#event_simpleName=ProcessRollup2
| in(FileName, values=["cmd.exe", "powershell.exe"])
| table([aid, FileName, CommandLine])
```

This expects the values to match the contents of **that exact field**. If your records only contain full paths in `ImageFileName`, adapt the query.

### 3.11 Numeric comparisons with `test()`

```cql
#event_simpleName=NetworkConnectIP4
| test(RemotePort > 49151)
| groupBy(RemotePort, function=count(as=Connections))
```

Use `test()` for explicit numeric comparison in a pipeline.

### 3.12 Conditional processing with `case`

```cql
#event_simpleName=NetworkConnectIP4
| case {
    test(RemotePort < 1024);
    test(RemotePort > 49151);
  }
| groupBy(RemotePort, function=count(as=Connections))
```

Here `case` keeps events meeting either condition. Do **not** conclude that ports are malicious simply because they are low or high.

### 3.13 Regular expressions vs wildcards

```cql
// Wildcard-style field search
CommandLine=*powershell*

// Regex: matches regardless of capitalization
CommandLine=/powershell/i

// Regex: match specific executable name at end of path
ImageFileName=/\\powershell\.exe$/i
```

Regex and wildcards have different escaping and matching behavior. For important hunts, inspect sample matches to ensure your filter is neither too broad nor too narrow.

### 3.14 Comments

```cql
// Look for PowerShell process executions
#event_simpleName=ProcessRollup2
| ImageFileName=/\\powershell\.exe$/i
```

Use comments to record intent and assumptions.

---

## 4. Three event-identification fields

Three names caused confusion in our earlier discussion:

| Field | Typical value | What it identifies |
|---|---|---|
| `#event_simpleName` | `ProcessRollup2` | Event name in common Falcon sensor datasets |
| `EventType` | `Event_ExternalApiEvent` | Broad category on event-stream-style records that have the field |
| `ExternalApiType` | `Event_EppDetectionSummaryEvent` | Specific subtype of an external-API event-stream record |

**These are not three compulsory layers in one universal hierarchy.** Different datasets and parsers expose different combinations.

### Example A: Raw sensor telemetry

```cql
#event_simpleName=ProcessRollup2
| table([@timestamp, aid, ImageFileName, CommandLine])
```

This asks: **what processes were observed?**

### Example B: External API event-stream record

```cql
EventType="Event_ExternalApiEvent"
ExternalApiType="Event_EppDetectionSummaryEvent"
| table([@timestamp, Hostname, Name, SeverityName])
```

This asks: **what endpoint detection summaries are recorded in this schema?**

### Example C: Detection summaries tagged by event name

Your environment's successful query used:

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| table([@timestamp, Hostname, Name, SeverityName])
```

That is valid for **your observed data**. You should not assume every repository tags the same event this way.

### Why does `Event_EppDetectionSummaryEvent` appear in both places?

The underlying detection-summary concept can be represented under different parsers or event-stream formats. In one dataset you may query the parsed subtype field; in another you may query an indexed event-name tag. Check the actual event to know which is present.

### Is `ExternalApiType` an API-call audit field?

Not necessarily. Its name is easy to misread. It commonly identifies the type of **external API event** in a streaming record, including detection summaries. It is **not**, by itself, evidence that someone called a REST API endpoint.

---

## 5. Discover your event inventory

These are among the most useful beginner queries because they avoid assuming which event types are present.

### 5.1 List all observed event names

```cql
#event_simpleName=*
| groupBy(#event_simpleName, function=count(as=EventCount), limit=max)
| sort(EventCount, order=desc)
```

**Answer:** Which event names appear in the selected repository and time window?

### 5.2 Count distinct observed event names

```cql
#event_simpleName=*
| count(#event_simpleName, distinct=true, as=ObservedEventNames)
```

**Does not answer:** How many event types CrowdStrike supports globally. There is no fixed universal list exposed by this query.

### 5.3 List `EventType` values

```cql
EventType=*
| groupBy(EventType, function=count(as=EventCount), limit=max)
| sort(EventCount, order=desc)
```

### 5.4 Count distinct `EventType` values

```cql
EventType=*
| count(EventType, distinct=true, as=ObservedEventTypes)
```

### 5.5 Explore external API subtypes

```cql
EventType="Event_ExternalApiEvent"
| groupBy(ExternalApiType, function=count(as=EventCount), limit=max)
| sort(EventCount, order=desc)
```

In the example from our discussion, the subtype list included the following event families:

| Example `ExternalApiType` | Possible analyst use |
|---|---|
| `Event_EppDetectionSummaryEvent` | Endpoint detection summaries |
| `Event_UserActivityAuditEvent` | Falcon user activity audit events |
| `Event_AuthActivityAuditEvent` | Authentication-related audit records |
| `Event_AuditLogV3Event` | Audit records |
| `Event_RemoteResponseSessionStartEvent` | Remote response session start records |
| `Event_RemoteResponseSessionEndEvent` | Remote response session end records |
| `Event_CorrelationRuleDetectionSummaryEvent` | Correlation rule detection summaries |
| `Event_ModuleSummaryInfoEvent` | Module summary records |

The existence of an event name alone does **not** prove the precise semantics of all of its fields; inspect its actual records and the relevant module documentation.

### 5.6 Inspect raw fields when you are unsure

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| table([@timestamp, #event_simpleName, EventType, ExternalApiType, @rawstring])
```

If `@rawstring` is large, omit it from the final reporting query. It is useful during initial exploration.

### 5.7 Important interpretation of counts

If `Event_EppDetectionSummaryEvent` returns **442 records**, the safe interpretation is **442 matching event records in that time range**. It does not automatically imply 442 unique alerts, 442 hosts, or 442 incidents.

---

## 6. Falcon sensor event families

A few common sensor event names to recognize:

| Sensor event | Typical investigation use |
|---|---|
| `ProcessRollup2` | Process execution context |
| `DnsRequest` | DNS resolution activity |
| `NetworkConnectIP4` | IPv4 network connection activity |
| `NetworkConnectIP6` | IPv6 network connection activity |
| `UserLogon` | Endpoint logon context |
| `PeFileWritten` | Portable Executable (PE) write activity |
| `AssociateTreeIdWithRoot` | Detection-tree-associated sensor detection context |

These are examples, **not** a complete list. Availability depends on sensor/platform telemetry, configured collection, processing, retention, and repository.

### The two broad investigative approaches

**Telemetry-first hunting**

> What did `powershell.exe` do across the estate?

Start with `ProcessRollup2`, `DnsRequest`, network events, and file events.

**Detection-first investigation**

> Falcon detected and reportedly killed a process. What exactly happened?

Start with `Event_EppDetectionSummaryEvent` or relevant detection records, then pivot into sensor telemetry.

### Endpoint detection summary vs process telemetry

| | `Event_EppDetectionSummaryEvent` | `ProcessRollup2` |
|---|---|---|
| Role | Detection summary/metadata | Process activity telemetry |
| Starts from | A Falcon detection | A process observation |
| Typical fields | Detection name, severity, tactic, disposition | Process identifiers, executable path, command line |
| Best for | Triage, prevention reporting | Process lineage, timeline reconstruction |
| Limitation | Doesn't prove every action the process took | Does not by itself prove Falcon produced a detection |

Do **not** assume that `ProcessRollup2` is emitted for *every* process in every environment or that every event source delivers detection summaries in the same way.

---

## 7. Essential fields for investigations

Learn them in groups.

### 7.1 Event and host identity

| Field | Question answered | Important caveat |
|---|---|---|
| `@timestamp` | When did the event occur? | Event time differs from ingest time |
| `@ingesttimestamp` | When did LogScale ingest it? | Useful for delivery-delay investigations |
| `#event_simpleName` | What event name is this? | Tag availability varies |
| `aid` | Which Falcon agent/endpoint? | Treat as an endpoint-specific identifier |
| `Hostname` | What hostname is associated? | May be populated only in certain feeds |
| `event_platform` | Which platform? | Value depends on schema |

### 7.2 Process identity and lineage

| Field | Question answered |
|---|---|
| `TargetProcessId` | Which Falcon-identified process instance is the primary subject of a process event? |
| `ContextProcessId` | Which process is associated with another event's activity? |
| `ParentProcessId` | Which process is the parent, within the given schema? |
| `RawProcessId` | What was the operating-system PID? |
| `ImageFileName` | What was the executable path? |
| `FileName` | What file/process name does **this schema** report? |
| `CommandLine` | How was the process launched? |
| `ParentBaseFileName` | What is the parent executable's base name, where populated? |
| `ParentImageFileName` | What parent executable path does this detection schema report? |
| `GrandParentImageFileName` | What grandparent executable path does this detection schema report? |
| `SHA256HashData` | What hash is recorded in **sensor event** schema? |
| `SHA256String` | What hash is recorded in **detection summary** schema, if present? |

**Rule:** Do not assume fields with similar meanings have identical names across datasets.

### 7.3 Detection and prevention

| Field | Why it matters |
|---|---|
| `Name` | Human-readable detection name |
| `SeverityName` | Falcon-assigned detection severity |
| `Tactic` / `Technique` | Detection's ATT&CK-related classification, where present |
| `PatternId` | Detection pattern identifier |
| `PatternDisposition` | Numeric action/flag value on applicable sensor records |
| `PatternDispositionValue` | Numeric disposition field on applicable detection-summary records |
| `PatternDispositionDescription` | Readable action summary |
| `PatternDispositionFlags` | Detailed action/status flags, when populated |
| `CompositeId` | Detection identifier used by some summary schemas |
| `HostGroups` | Falcon host-group context |

### 7.4 Network and user context

| Field | Typical use |
|---|---|
| `RemoteAddressIP4` | IPv4 destination/remote address |
| `RemotePort` | Remote port |
| `ContextProcessId` | Link network/DNS/file activity to its process |
| `UserName` | User context (if the schema provides it) |
| `UserSid` | Windows security identifier |

---

## 8. Understanding process identity and relationships

This is a foundational EDR concept.

### Three different identifiers

Suppose a process event contains:

```text
aid             endpoint-123
TargetProcessId 987654321
RawProcessId    4820
ParentProcessId 876543210
```

**Interpretation:**

- `RawProcessId=4820` is the operating system's PID.
- `TargetProcessId=987654321` identifies the target process within Falcon sensor telemetry.
- `ParentProcessId=876543210` points toward the parent process relationship in that event schema.

**Why this matters:** OS PIDs can be reused. Correlating only on `RawProcessId` across long time periods can combine unrelated processes.

### Parent, child, and grandparent

Illustrative execution chain:

```text
WINWORD.EXE
   └── powershell.exe
         └── suspicious.exe
```

The `suspicious.exe` event may include details about its parent, while a detection summary may already contain readable parent/grandparent names and command lines.

A name like `WINWORD.EXE` is not proof of malicious behavior. Investigate the command line, ancestry, user context, document origin, and related events.

### Match process execution to subsequent activity

**Step A: Find a process**

```cql
#event_simpleName=ProcessRollup2
| ImageFileName=/\\powershell\.exe$/i
| table([@timestamp, aid, TargetProcessId, ParentProcessId, RawProcessId, ImageFileName, CommandLine])
```

**Step B: Pick the actual `aid` and `TargetProcessId` from a result.**

**Step C: Find activity associated with that process**

```cql
aid="YOUR_AID"
| ContextProcessId=YOUR_TARGET_PROCESS_ID
| sort(@timestamp, order=asc)
```

This can expose matching network, DNS, or other context events **if those event families and fields are present**.

### More precise hunt: network activity by that process

```cql
#event_simpleName=NetworkConnectIP4
| aid="YOUR_AID"
| ContextProcessId=YOUR_TARGET_PROCESS_ID
| table([@timestamp, aid, ContextProcessId, RemoteAddressIP4, RemotePort])
| sort(@timestamp, order=asc)
```

### Find child process launches

```cql
#event_simpleName=ProcessRollup2
| aid="YOUR_AID"
| ParentProcessId=YOUR_TARGET_PROCESS_ID
| table([@timestamp, ImageFileName, CommandLine, ParentProcessId, TargetProcessId])
```

**Schema check:** These examples use the process-ID conventions discussed in Falcon sensor event documentation. Validate the values and meanings from your records before doing large-scale joins.

---

## 9. Understanding `PatternDisposition`

**`PatternDisposition` is action/status information associated with certain Falcon detections.** It is not a generic boolean of “malware yes/no”.

### Bitmask mental model

Think of disposition as a set of flags that can be combined into a number.

Examples often documented for Falcon sensor detection context include:

| Numeric value / flag | Common interpretation |
|---|---|
| `16` | Kill process action |
| `128` | Quarantine file action |
| `144` | Combination: kill (`16`) + quarantine (`128`) |
| `256` | Prevention policy disabled modifier |
| `272` | Kill (`16`) + prevention policy disabled (`256`) |
| `131072` | Kill action failed modifier |
| `131088` | Kill (`16`) + kill action failed (`131072`) |

**Critical:** A kill flag **does not automatically prove successful termination**. You must consider all modifiers and the broader detection context. Numeric values and their meanings should be verified against the documentation for the exact schema/version you are using.

### Why equality searches can miss results

```cql
#event_simpleName=AssociateTreeIdWithRoot
| PatternDisposition=16
```

This matches an **exact numeric value** of 16. It does not match combined values such as 144 or 131088.

### Safest beginner discovery query

```cql
#event_simpleName=AssociateTreeIdWithRoot
| groupBy(PatternDisposition, function=count(as=Events), limit=max)
| sort(Events, order=desc)
```

Inspect the values seen in your environment, then interpret them using the documented flag definitions.

### Easier detection-summary view

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(PatternDispositionDescription, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

This is often easier to learn from than the raw integer because the field is already human-readable. Confirm the available `PatternDispositionFlags` and `PatternDispositionValue` fields when you need deeper assurance.

### Questions for a prevented-threat investigation

1. Did Falcon **detect**, **block execution**, **kill**, **quarantine**, or report multiple actions?
2. Was prevention policy enabled for the action?
3. Did the action report failure?
4. Does the detection record describe the outcome, or only the intended action?
5. Is there supporting telemetry indicating process termination or continued behavior?

---

## 10. Investigating endpoint detection summaries

This section builds directly from your working query.

### 10.1 Detection table for one host

```cql
#event_simpleName=Event_EppDetectionSummaryEvent Hostname=/HOSTNAME/i
| table([
    @timestamp, Name, Tactic, Technique, SeverityName,
    PatternId, PatternDispositionDescription,
    FileName, CommandLine,
    ParentImageFileName, ParentCommandLine,
    GrandParentImageFileName, ProcessId, HostGroups
  ])
| sort(@timestamp, order=desc)
```

`Hostname=/HOSTNAME/i` is a **regex pattern**, not an exact-host filter. Replace `HOSTNAME` with a distinctive actual name, and consider an exact-match filter where appropriate.

### 10.2 Explain the fields

| Field | Ask yourself |
|---|---|
| `Name` | What did Falcon call the detection? |
| `Tactic` | What ATT&CK tactic was assigned? |
| `Technique` | What ATT&CK technique was assigned? |
| `SeverityName` | How was it prioritized? |
| `PatternId` | Which pattern triggered? |
| `PatternDispositionDescription` | What prevention action was reported? |
| `FileName`, `CommandLine` | What was executed? |
| `ParentImageFileName`, `ParentCommandLine` | What launched it? |
| `GrandParentImageFileName` | What launched the parent? |
| `ProcessId` | Which process does **this summary schema** identify? |
| `HostGroups` | Which Falcon host group context applies? |

**Warning:** `ProcessId` in a summary is not automatically interchangeable with a sensor event's `TargetProcessId`. Inspect field definitions and values before correlating.

### 10.3 Most common detection names

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(Name, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.4 Prevention action distribution

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(PatternDispositionDescription, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.5 MITRE ATT&CK tactic/technique distribution

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy([Tactic, Technique], function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.6 Hosts with the most detection summaries

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(Hostname, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.7 Severity distribution

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(SeverityName, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.8 Repeated detection patterns

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy([PatternId, Name], function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### 10.9 Suspicious parent process context

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| ParentImageFileName=/\\(winword|excel)\.exe$/i
| table([
    @timestamp, Hostname, Name, SeverityName,
    ParentImageFileName, ParentCommandLine,
    FileName, CommandLine, PatternDispositionDescription
  ])
```

This identifies detections whose parent path ends in `winword.exe` or `excel.exe`. It does **not** mean those programs are malicious.

### 10.10 Rich detection-investigation table

Use this after verifying field availability in a sample event:

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| Hostname=/HOSTNAME/i
| table([
    @timestamp,
    Hostname,
    Name,
    SeverityName,
    Tactic,
    Technique,
    PatternId,
    PatternDispositionValue,
    PatternDispositionDescription,
    PatternDispositionFlags,
    FileName,
    CommandLine,
    ParentImageFileName,
    ParentCommandLine,
    GrandParentImageFileName,
    GrandParentCommandLine,
    ProcessId,
    SHA256String,
    CompositeId
  ])
| sort(@timestamp, order=desc)
```

Not every record will have every field. Blank columns are a clue to inspect the actual schema, not a reason to invent a value.

---

## 11. Walkthrough: Falcon killed a process

**Scenario:** Falcon raises a detection that reports `powershell.exe` or a child process was killed.

You want to answer:

1. What fired?
2. What was the action?
3. What command ran?
4. Who/what launched it?
5. What activity preceded the prevention?
6. Was the action successful?
7. Did activity continue after the reported kill?

### Step 1 — Find the detection

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| Hostname=/YOUR_HOST/i
| table([
    @timestamp, Hostname, Name, SeverityName,
    PatternDispositionDescription, PatternDispositionFlags,
    FileName, CommandLine, ParentCommandLine,
    ProcessId, CompositeId
  ])
| sort(@timestamp, order=desc)
```

Choose the detection and record its time, host, identifier, process information, and disposition.

### Step 2 — Understand the disposition

Check `PatternDispositionDescription` and, where present, `PatternDispositionValue` and `PatternDispositionFlags`.

A label that includes “kill” is a starting point. Check for policy-disabled or failed-action modifiers before declaring the process was successfully terminated.

### Step 3 — Identify the executable and ancestry

Inspect `FileName`, `CommandLine`, `ParentImageFileName`, `ParentCommandLine`, and `GrandParentImageFileName`.

Illustrative chain:

```text
WINWORD.EXE
  └─ powershell.exe -EncodedCommand ...
       └─ downloaded.exe
```

This chain is **not** observed tenant evidence; it simply illustrates the reasoning.

### Step 4 — Find the matching process telemetry

```cql
#event_simpleName=ProcessRollup2
| aid="YOUR_AID"
| table([
    @timestamp, aid, TargetProcessId, ParentProcessId,
    RawProcessId, ImageFileName, CommandLine, SHA256HashData
  ])
| sort(@timestamp, order=desc)
```

Narrow the time range around the detection. Match executable path, command line, host, and timestamp. Use documented identifiers when present; do not assume `CompositeId` equals `TargetProcessId`.

### Step 5 — Pivot to related events

Once you have identified the correct Falcon process identifier:

```cql
aid="YOUR_AID"
| ContextProcessId=YOUR_TARGET_PROCESS_ID
| table([
    @timestamp, #event_simpleName, aid, ContextProcessId,
    RemoteAddressIP4, RemotePort, DomainName, TargetFileName
  ])
| sort(@timestamp, order=asc)
```

This is a **multi-family inspection template**. Fields like `DomainName` and `TargetFileName` will be blank on event families that do not populate them.

### Step 6 — Focus on network behavior

```cql
#event_simpleName=NetworkConnectIP4
| aid="YOUR_AID"
| ContextProcessId=YOUR_TARGET_PROCESS_ID
| table([@timestamp, RemoteAddressIP4, RemotePort])
| sort(@timestamp, order=asc)
```

### Step 7 — Investigate child processes

```cql
#event_simpleName=ProcessRollup2
| aid="YOUR_AID"
| ParentProcessId=YOUR_TARGET_PROCESS_ID
| table([@timestamp, ImageFileName, CommandLine, TargetProcessId])
| sort(@timestamp, order=asc)
```

### Step 8 — Document conclusions by evidence level

**Observed:** “At 08:30 UTC, a detection summary for host X reported a kill action.”

**Correlated:** “A process event on the same host/time shows `powershell.exe` with the observed command line.”

**Not yet proven:** “The process was successfully terminated before making any network connections.”

Use the detection UI and any relevant action outcome events to verify the last claim.

---

## 12. Threat-hunting query cookbook

This section preserves and extends the starter hunting themes from your original `cql-basics.md`. Queries are organized by **underlying data family**.

### 12.1 All PowerShell executions

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell\.exe$/i
| table([@timestamp, aid, ImageFileName, CommandLine, UserName])
| sort(@timestamp, order=desc)
```

**Investigate:** unusual parent processes, encoded commands, download commands, unexpected accounts, repeated execution.

### 12.2 PowerShell with encoded command indicators

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell\.exe$/i
| CommandLine=/\s-(enc|encodedcommand)\b/i
| table([@timestamp, aid, CommandLine, ParentBaseFileName])
```

**Important:** Encoded PowerShell is suspicious context, not proof of maliciousness. The regex looks for command-line switches; not every variant or obfuscation pattern is covered.

### 12.3 Word or Excel launching a shell

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| (ParentBaseFileName=/^winword\.exe$/i OR ParentBaseFileName=/^excel\.exe$/i)
| (ImageFileName=/\\powershell\.exe$/i OR ImageFileName=/\\cmd\.exe$/i)
| table([@timestamp, aid, ParentBaseFileName, ImageFileName, CommandLine])
```

### 12.4 Discovery/reconnaissance commands

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| CommandLine=/(net user|net view|whoami|ipconfig)/i
| table([@timestamp, aid, ImageFileName, CommandLine])
```

This query identifies command-line text; some matches may be part of benign administrative activity.

### 12.5 Scheduled-task creation via `schtasks.exe`

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\schtasks\.exe$/i
| CommandLine=/\/create\b/i
| table([@timestamp, aid, CommandLine, ParentBaseFileName])
```

**Meaning:** A command attempting scheduled-task creation was launched; this process event alone does not prove task creation succeeded.

### 12.6 Remote-execution tooling

```cql
#event_simpleName=ProcessRollup2 event_platform=Win
| (ImageFileName=/\\(psexec|wmic)\.exe$/i OR CommandLine=/Invoke-Command/i)
| table([@timestamp, aid, ImageFileName, CommandLine])
```

This searches for names and text associated with remote-execution tools. The result can include legitimate administration.

### 12.7 Network activity to particular ports

```cql
#event_simpleName=NetworkConnectIP4
| case {
    test(RemotePort < 1024);
    test(RemotePort > 49151);
  }
| groupBy([RemoteAddressIP4, RemotePort], function=count(as=Connections), limit=max)
| sort(Connections, order=desc)
```

**Caution:** The original notes suggested unusual port ranges may indicate C2. Port numbers by themselves do not establish command-and-control activity. Use destinations, processes, timing, reputation, and baselines.

### 12.8 DNS requests

```cql
#event_simpleName=DnsRequest
| table([@timestamp, aid, ContextProcessId, DomainName])
```

**Schema check:** `DomainName` is common in sensor DNS telemetry; confirm the DNS-name field in your repository.

### 12.9 High-volume DNS by name

```cql
#event_simpleName=DnsRequest
| groupBy(DomainName, function=count(as=Requests), limit=max)
| sort(Requests, order=desc)
```

A high count is a triage signal, not inherently malicious.

### 12.10 Portable Executable writes

```cql
#event_simpleName=PeFileWritten
| table([@timestamp, aid, ContextProcessId, TargetFileName])
```

This is a better starting point for PE write activity than filtering `ProcessRollup2` on a `TargetFileName` field that may be absent.

### 12.11 Interesting file-write paths

```cql
#event_simpleName=PeFileWritten
| TargetFileName=/\\(AppData\\Roaming|Temp)\\/i
| table([@timestamp, aid, ContextProcessId, TargetFileName])
```

This checks path text on PE write events. Validate legitimate installer/updater behavior before escalating.

### 12.12 Search by a known file hash

```cql
#event_simpleName=ProcessRollup2
| SHA256HashData="REPLACE_WITH_SHA256"
| table([@timestamp, aid, ImageFileName, CommandLine, SHA256HashData])
```

Requires an actual hash; avoid passing the placeholder unchanged.

### 12.13 Detect use of a specific executable across distinct hosts

```cql
#event_simpleName=ProcessRollup2
| ImageFileName=/\\powershell\.exe$/i
| groupBy(ImageFileName, function=[
    count(as=ProcessEvents),
    count(aid, distinct=true, as=DistinctHosts)
  ])
```

### 12.14 Authentication failures — **third-party-schema template only**

```cql
#event.category="authentication"
| event.outcome="failure"
| groupBy([user.name, source.ip], function=count(as=FailedAttempts))
| test(FailedAttempts > 5)
| sort(FailedAttempts, order=desc)
```

**Do not assume this works on Falcon sensor events.** This template requires an ingested third-party log source exposing the shown ECS-like fields. Confirm tags, dotted field names, and parser output first.

### 12.15 Threat-intelligence enrichment — **integration-dependent**

Your original notes used `ioc:lookup(...)`. That function or package is **not guaranteed to be installed or available** in every LogScale environment.

A safe starting query is:

```cql
#event_simpleName=DnsRequest
| table([@timestamp, aid, DomainName])
```

Only add enrichment after confirming the exact lookup function, package, permissions, input fields, and parameters in your deployment. Do not copy an unverified `ioc:lookup()` example into a production detection rule.

---

## 13. CQL aggregation and reporting

The same event family can answer very different questions depending on the group-by dimension.

### Per-host summary

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(Hostname, function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### Detection name by severity

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy([Name, SeverityName], function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### Technique by reported prevention action

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy([Technique, PatternDispositionDescription], function=count(as=Detections), limit=max)
| sort(Detections, order=desc)
```

### Unique affected endpoints versus total detection records

If `aid` is populated in the selected summary schema:

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(Name, function=[
    count(as=DetectionRecords),
    count(aid, distinct=true, as=DistinctEndpoints)
  ], limit=max)
| sort(DetectionRecords, order=desc)
```

If `aid` is absent, inspect whether the records have another documented stable endpoint identifier before substituting one.

### Aggregation pitfalls

- Grouping **drops individual event detail** unless you explicitly collect it.
- A `count()` counts matching records after all earlier filters.
- `count(field, distinct=true)` counts distinct observed values, subject to LogScale function semantics.
- Large groupings can be expensive.
- Your chosen time range and repository are part of every reported number.
- Some event families can contain several records relevant to one operational action.

---

## 14. Data sources and schema differences

### Why one CQL example works and another returns nothing

CQL is the **language**. The available **fields** are defined by the source records and parsers.

Common sources include:

- Falcon sensor telemetry.
- Falcon detection and event-stream data.
- Falcon audit records.
- Third-party Windows, identity, firewall, DNS, cloud, and SaaS logs.

**Do not mix schemas without confirming the event source.**

Examples:

| Question | Starting event / source | Common fields |
|---|---|---|
| Which process launched PowerShell? | `ProcessRollup2` | `ImageFileName`, `ParentProcessId`, `CommandLine` |
| Did Falcon report a kill? | `Event_EppDetectionSummaryEvent` | `PatternDispositionDescription`, flags |
| What IP did the process contact? | `NetworkConnectIP4` | `ContextProcessId`, `RemoteAddressIP4`, `RemotePort` |
| Which Falcon administrator performed an action? | Falcon audit event | Inspect `Event_UserActivityAuditEvent` or other audit schema |
| Which identity had failed logins? | An actual identity-provider log source | Discover its user, outcome, and IP field names |

### A note on `DetectionSummaryEvent` versus `Event_EppDetectionSummaryEvent`

Your original notes call the former “legacy/deprecated” and the latter its replacement. **That lifecycle claim is preserved here as a statement from the supplied notes, not a verified universal platform rule.** Availability, naming, and lifecycle differ by source, API, connector, and product version. Validate the current migration guidance in official documentation before designing a long-term pipeline around either name.

Similarly, do not claim that all of `ProcessRollup2`, `DetectionSummaryEvent`, and `Event_EppDetectionSummaryEvent` are always present in both Falcon Event Streams and Falcon Data Replicator (FDR). Check the feed's supported event catalog, entitlement, configuration, and parser.

### Schema-discovery workflow

1. Select the intended repository and short time window.
2. Discover event names using `groupBy(#event_simpleName)`.
3. Open a **raw result** for the event of interest.
4. Confirm exact field names, capitalization, types, and tag prefix.
5. Start with `table()` of only confirmed fields.
6. Add filters and aggregation.
7. Expand time range cautiously.
8. Save your query with a note stating the schema assumption.

---

## 15. Mistakes, caveats, and troubleshooting

### Mistake 1: Treating `#event_simpleName` as a CQL function

It is a **tagged field**, not a function.

### Mistake 2: Assuming `EventType` gives every CrowdStrike event type

It gives values present in data carrying **that field**, in the repository and time range searched.

### Mistake 3: Treating `ExternalApiType` as proof of an API call

It is an event subtype field on relevant event-stream schemas. Audit the actual API activity separately.

### Mistake 4: Confusing `RawProcessId` with `TargetProcessId`

Operating system PIDs and sensor process identifiers serve different purposes.

### Mistake 5: Assuming numeric `PatternDisposition` values are mutually exclusive

Actions/status flags can be combined. Check the modifiers.

### Mistake 6: Assuming a detection-summary ProcessId automatically equals a sensor `TargetProcessId`

The schemas may encode process identifiers differently. Correlate only after confirming mapping.

### Mistake 7: Using `ProcessRollup2` to query every file write

Use the appropriate file event family; for PE files, start by exploring `PeFileWritten`.

### Mistake 8: Using third-party field names on Falcon sensor events

`event.outcome`, `user.name`, and `source.ip` are possible for some third-party datasets, but are not universal Falcon sensor fields.

### Mistake 9: Misunderstanding the time range

No results may mean the event did not occur **in the selected repository and period**, not that the endpoint never performed the behavior.

### Mistake 10: Misreading `Hostname=/HOSTNAME/i`

That is a **regex**, and `/i` makes it case-insensitive. It is not automatically an exact host match.

### Mistake 11: Believing every field is present in every event

The field set can vary by event family, OS, parser, and ingestion path.

### Mistake 12: Promoting a hunt directly to a detection rule

First establish a baseline, assess benign causes, confirm field coverage, set practical thresholds, and test alert volume.

### Quick troubleshooting matrix

| Symptom | Check first |
|---|---|
| No results | Repository, time range, entitlement, event name, parser |
| Empty columns | Field capitalization and whether that event family has the field |
| Too many results | Regex scope, parentheses around OR conditions |
| Unexpected count | Time range, repeated records, grouping dimensions |
| Process IDs don't match | Host ID, event schemas, PID type, time windows |
| “Kill” reported but later activity exists | Failed-action flags, timing, process identity, delayed ingestion |
| Query fails on a function | CQL syntax, installed functions/packages, supported parameters |
| High query cost | Narrow time first, filter before high-cardinality grouping |

---

## 16. Practice exercises and learning path

Use a **test/sandbox dataset or authorized SOC environment**. The learning goal is not to find “malware”; it is to understand evidence and query behavior.

### Level 1 — Query basics

- [ ] Run `#event_simpleName=ProcessRollup2`.
- [ ] Show five useful fields using `table()`.
- [ ] Filter to Windows processes.
- [ ] Sort newest first.
- [ ] Count how many records match your selected window.
- [ ] Group results by `aid`.

**Checkpoint:** Explain why `count()` and `count(aid, distinct=true)` answer different questions.

### Level 2 — Event inventory

- [ ] List `#event_simpleName` values.
- [ ] List `EventType` values.
- [ ] List `ExternalApiType` values within `Event_ExternalApiEvent`.
- [ ] Open at least one detection event and one sensor event.
- [ ] Write down which of the three identifier fields each event actually has.

**Checkpoint:** Explain why the three fields are not a universal three-level hierarchy.

### Level 3 — Process investigation

- [ ] Find a benign test process.
- [ ] Record its `aid`, `TargetProcessId`, and `RawProcessId`.
- [ ] Find its parent process.
- [ ] Search for network activity using `ContextProcessId`.
- [ ] Build a five-event timeline if relevant data is available.

**Checkpoint:** Explain why PID reuse matters.

### Level 4 — Detection analysis

- [ ] Query `Event_EppDetectionSummaryEvent`.
- [ ] Group by `Name`.
- [ ] Group by `SeverityName`.
- [ ] Group by `PatternDispositionDescription`.
- [ ] Investigate one detection's process ancestry.

**Checkpoint:** State what the detection proves and what still requires sensor evidence.

### Level 5 — Reporting and responsible hunting

- [ ] Compare detection count with distinct affected hosts.
- [ ] List the top MITRE techniques.
- [ ] Write one finding with observed facts and one explicitly labeled hypothesis.
- [ ] Validate a hunting query against known benign activity.
- [ ] Note source, repository, parser assumptions, and time range in the saved search.

### Five short knowledge checks

1. **What does the `#` in `#event_simpleName` mean?**  
   It marks a tagged/indexed field.

2. **Is `ExternalApiType` a CQL function?**  
   No. It is an event field in relevant schemas.

3. **Does `PatternDisposition=16` catch `144`?**  
   No. An equality filter for 16 will not match a combined numeric value of 144.

4. **Does `ProcessRollup2` tell you that Falcon killed the process?**  
   Not by itself. Look for relevant prevention/detection records and outcomes.

5. **Can 442 EPP summary records be called 442 incidents?**  
   No. That number is a count of matching event records, without deduplication or incident grouping.

---

## 17. Cheat sheet

### Discovery

```cql
// Event name inventory
#event_simpleName=*
| groupBy(#event_simpleName, function=count(as=Events), limit=max)
| sort(Events, order=desc)
```

```cql
// EventType inventory
EventType=*
| groupBy(EventType, function=count(as=Events), limit=max)
| sort(Events, order=desc)
```

```cql
// External API subtype inventory
EventType="Event_ExternalApiEvent"
| groupBy(ExternalApiType, function=count(as=Events), limit=max)
| sort(Events, order=desc)
```

### Endpoint detections

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| table([@timestamp, Hostname, Name, SeverityName, PatternDispositionDescription])
| sort(@timestamp, order=desc)
```

### Prevention action summary

```cql
#event_simpleName=Event_EppDetectionSummaryEvent
| groupBy(PatternDispositionDescription, function=count(as=Detections), limit=max)
```

### Sensor process creation

```cql
#event_simpleName=ProcessRollup2
| table([@timestamp, aid, TargetProcessId, ParentProcessId, ImageFileName, CommandLine])
```

### Process network pivot

```cql
#event_simpleName=NetworkConnectIP4
| aid="YOUR_AID"
| ContextProcessId=YOUR_TARGET_PROCESS_ID
| table([@timestamp, RemoteAddressIP4, RemotePort])
```

### Five rules worth memorizing

1. **Identify the schema before choosing field names.**
2. **Start with a tight time range and simple filters.**
3. **Treat event counts, process counts, detection counts, and incident counts separately.**
4. **Treat prevention actions as structured outcomes with possible modifiers, not simple booleans.**
5. **Use detection summaries for triage and sensor telemetry for activity reconstruction.**

---

## 18. Sources and verification notes

### Primary source: supplied material

- **`cql-basics.md`**, uploaded by the user in this session. Its introductory syntax, hunting themes, and discussion of `ProcessRollup2`, detection summaries, and event-stream schemas form the backbone of this guide.
- The user's working `Event_EppDetectionSummaryEvent` host-investigation query and `ExternalApiType` grouping results, shared in the conversation, inform the detection-summary sections.
- Prior conversation explanations about process IDs, detection summaries, and disposition fields are incorporated **as learning material**, not represented as live tenant validation.

### Official LogScale documentation checked

- [LogScale: Event Structure](https://library.humio.com/crowdstrike-query-language/events-structure.html) — fields and parser-dependent event structure.
- [LogScale: Field Naming and Standards](https://library.humio.com/crowdstrike-query-language/events-standard-fields.html) — metadata, tag fields, and conventions.
- [LogScale: Data Ingestion Overview](https://library.humio.com/training/training-ingestion-overview.html) — metadata, tags, and user fields.
- [CrowdStrike Falcon LogScale FLTR Tutorial](https://library.humio.com/integrations/integrations-crowdstrike-fltr-tutorial-crowdstrike-fltr-tutorial.html) — sample Falcon CQL, including `#event_simpleName`, process analysis, grouping, and timestamps.

### Supplied Falcon reference documentation cited in our discussion

- **`Event Investigation.pdf`**, especially detection-summary queries and CQL examples.
- **`Sensor Events.pdf`**, especially sensor process identity, event families, and disposition fields.

### Evidence labels used in this guide

- **Documented syntax / concept:** Backed by LogScale docs or supplied reference materials.
- **User-observed schema:** The working query and event names from the conversation; not a universal entitlement or schema guarantee.
- **Illustrative example:** Plausible example data, *not* actual Falcon tenant evidence.
- **Schema-dependent template:** Requires verification of fields, parser, availability, or installed packages before use.

### Important boundary

No live Falcon console, tenant data, FDR feed, or API access was used to prepare this guide. All event values shown for examples are illustrative unless explicitly described as user-provided observations.

---

**End of guide.**
