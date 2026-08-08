# Security-Focused CQL: Threat Hunting, Detection Engineering, and IR Queries

Fleet-visibility queries answer "what does my environment look like." Security queries answer a sharper question: "is something here that shouldn't be." This post is a working reference of hunting and investigation queries against raw `base_sensor` telemetry and Falcon detections — the kind a threat hunter or detection engineer runs directly against sensor events rather than pre-built detections, which is what makes them useful as building blocks for custom hunts and IOA-style logic. Every query here follows the [discovery-first methodology](01-how-to-build-cql-queries.md).

---

## Hunting encoded PowerShell execution

The full step-by-step build-up lives in the [query-building post](01-how-to-build-cql-queries.md); here's the finished hunt, restricted to rare command lines (fewer than 10 executions) to surface anomalies instead of routine automation:

```lql
#event_simpleName=ProcessRollup2 event_platform=Win
| ImageFileName=/\\powershell(_ise)?\.exe/i
| CommandLine=/\-(?<encodedFlagUsed>e(nc|ncodedcommand|ncoded)?)\s+/i
| groupBy([encodedFlagUsed, CommandLine], function=(count(aid, as=executionCount)))
| test(executionCount < 10)
| sort(executionCount, order=asc)
```

Rare encoded command lines are disproportionately high-value in a hunt — routine automation tends to repeat the same command line hundreds of times, while a one-off encoded invocation is far more likely to be interesting.

## Hunting suspicious `chmod` on Linux

A classic technique for making a dropped file executable or world-writable ahead of running it — worth watching for `755` or `a+w` permission changes via `chmod`:

```lql
event_platform = Lin #event_simpleName = "ProcessRollup2" CommandLine = /.*chmod\s+(755|a+w).*/
| table([@timestamp, #event_simpleName, ImageFileName, CommandLine], limit=1000)
```

## Process + file telemetry joined to detections

Two versions of the same idea — pulling raw process/file telemetry and joining it against the detection that fired on the same tree, so you can see the sensor-level activity behind a detection rather than just the detection summary.

**Version 1 — join on `TreeId`**, with timestamps formatted in two different timezones (useful when the sensor event and the tree/detection event are logged in different regions):

```lql
#repo="base_sensor" and TreeId=* and ImageFileName=/BFUS/i
| rename(field="#event_simpleName", as="SensorEventName")
| SensorEventTimeStamp := @timestamp
| SensorEventTimeStamp := formatTime("%Y-%m-%d %H:%M:%S.%L", field=SensorEventTimeStamp, locale=en_US, timezone=CET)
| table([SensorEventTimeStamp, SensorEventName, TreeId, ImageFileName, CommandLine], limit=1000)
| join({#event_simpleName=AssociateTreeIdWithRoot}, field=[TreeId], include=[@timestamp, TargetProcessId, TreeId, DetectName, ComputerName], mode=left)
| TreeTimeStamp := @timestamp
| TreeTimeStamp := formatTime("%Y-%m-%d %H:%M:%S.%L", field=TreeTimeStamp, locale=en_US, timezone=PST)
| groupBy([TreeId, TreeTimeStamp, DetectName, ComputerName], function=[collect([SensorEventName, ImageFileName, CommandLine])])
| sort(field=TreeTimeStamp, type=number, order=descending, limit=1000)
```

**Version 2 — cleaner join on `TargetProcessId`**, using a `case` block to flag detected rows before the join:

```lql
ComputerName = ART-DCTESTVM-SG #event_simpleName = "ProcessRollup2"
| case {
    TreeId=*
    | EventDetails:="Detected";
    *
}
| table([@timestamp, #event_simpleName, TargetProcessId, EventDetails, TreeId, ImageFileName, CommandLine], limit=1000)
| join({#event_simpleName=AssociateTreeIdWithRoot}, field=[TargetProcessId], key=TargetProcessId, include=[@timestamp, #event_simpleName, TargetProcessId, TreeId, DetectName, DetectDescription], mode=left)
```

Prefer version 2 for new work — joining on `TargetProcessId` is the more reliable key than `TreeId` alone.

## DNS request pivoted back to the originating process

Starting from a suspicious domain lookup and joining back to the process that made the request, correlating `ContextProcessId` on the DNS side to `TargetProcessId` on the process side:

```lql
#event_simpleName="DnsRequest" and DomainName = "cookieaquila.com" and FileName != "ZSATunnel.exe"
| in(field="ComputerName", values=["DE-L082605"])
| join({#event_simpleName="ProcessRollup2" and FileName != "ZSATunnel.exe" | in(field="ComputerName", values=["DE-L082605"])}, field=["ContextProcessId"], key="TargetProcessId", include=["FileName", "UserName", "ImageFileName", "CommandLine"], mode=left)
| table(["@timestamp", "ComputerName", "UserName", "DomainName", "FileName", "ImageFileName", "CommandLine"])
```

The `FileName != "ZSATunnel.exe"` exclusion on both sides filters out a known VPN/tunnel client generating expected noise on this domain — a reminder that most real hunts need at least one exclusion for known-good tooling before results are usable.

## Hunting malicious browser extensions against a threat-intel CSV

Cross-references installed extensions against a CSV of known-malicious extension IDs (modeled on the December 2024 Cyberhaven supply-chain attack), decodes the numeric browser enum, and labels each install `BAD` / `UNKNOWN` / `MAYBE_OK`:

```lql
#event_simpleName=InstalledBrowserExtension
| match(file="cyberhaven_bad_extensionId_2.csv", field=[BrowserExtensionId], column=BrowserExtensionId)
| groupBy([aid, ComputerName, UserName, BrowserName, BrowserExtensionId, BrowserExtensionName, BrowserExtensionVersion, Version, BrowserExtensionStatusEnabled, BrowserExtensionPath], function=[collect([BrowserProfileId, BrowserProfileName, event_platform]), selectLast([@timestamp])])
| rename(field="Version", as="knownBad")
| case {
    BrowserName = "0" | BrowserName := "UNKNOWN";
    BrowserName = "1" | BrowserName := "FIREFOX";
    BrowserName = "2" | BrowserName := "SAFARI";
    BrowserName = "3" | BrowserName := "CHROME";
    BrowserName = "4" | BrowserName := "EDGE";
    BrowserName = "5" | BrowserName := "EDGE_CHROMIUM";
    BrowserName = "6" | BrowserName := "INTERNET_EXPLORER";
    BrowserName = "7" | BrowserName := "EDGE_LEGACY";
    BrowserName = "8" | BrowserName := "IE_TYPED_URL";
    BrowserName = "9" | BrowserName := "FIREFOX_APP";
    *
}
| case {
    test(BrowserExtensionVersion==knownBad) | Status:="BAD";
    knownBad="" | Status:="UNKNOWN";
    * | Status:="MAYBE_OK";
}
| formatTime(format="%Y-%m-%dT%H:%M:%S.%L%z", field=@timestamp, as="installts")
| format(format="%s\t%s\t%s", field=[Status, BrowserExtensionVersion, installts], as="Status")
| groupBy(
    [aid, ComputerName, UserName, BrowserName, BrowserExtensionId, BrowserExtensionName, BrowserExtensionStatusEnabled],
    function=[
        collect([Status, BrowserExtensionVersion, Version, BrowserProfileId, BrowserProfileName, event_platform, BrowserExtensionPath]),
        selectLast([@timestamp])
    ]
)
```

`MAYBE_OK` deserves its own mention: a version not on the known-bad list isn't automatically clean — threat intel lists lag real-world compromise, so treat that bucket as unconfirmed rather than cleared.

For a trend view of extension installs over time by browser (same enum decoding, charted instead of tabled):

```lql
#event_simpleName=InstalledBrowserExtension
| case {
    BrowserName="0" | BrowserName:="UNKNOWN";
    BrowserName="1" | BrowserName:="FIREFOX";
    BrowserName="2" | BrowserName:="SAFARI";
    BrowserName="3" | BrowserName:="CHROME";
    BrowserName="4" | BrowserName:="EDGE";
    BrowserName="5" | BrowserName:="EDGE_CHROMIUM";
    BrowserName="6" | BrowserName:="INTERNET_EXPLORER";
    BrowserName="7" | BrowserName:="EDGE_LEGACY";
    BrowserName="8" | BrowserName:="IE_TYPED_URL";
    BrowserName="9" | BrowserName:="FIREFOX_APP";
    *;
}
| timeChart(series=BrowserName)
```

## Hunting known-malicious domains by regex

Combined regex of typosquat/rogue extension-marketplace and C2 domain suffixes, scoped to DNS activity from Chromium-family browsers:

```lql
#repo="base_sensor"
| in(#event_simpleName, values=["DnsRequest", "SuspiciousDnsRequest"])
| ContextBaseFileName=/(?:chrome|chromium|microsoftedge|msedge|brave|opera)/i
| DomainName=/(?:(?:cyberhavenext|primusext|internxtvpn|censortracker|iobit|ultrablock|dearflip|pieadblock)\.pro|(?:castorus|parrottalks|bookmarkfc|yujaverity|readermodeext|tinamind)\.info|(?:vpncity|wayinai|uvoice|vidnozflex)\.live|moonsift\.store|(?:wakelet|locallyext)\.ink|(?:sclpfybn|tnagofsg))/i
| groupBy([aid, ComputerName], function=[selectLast([@timestamp]), count(), collect([DomainName, ContextBaseFileName, UserName])])
```

Regex domain lists like this go stale fast — treat it as a snapshot to be refreshed against current threat intel rather than a permanent hunt.

## Free-text keyword hunting for a known supply-chain compromise

Sometimes the fastest hunt is a raw keyword match rather than a structured field filter — here, searching for "polyfill" (2024 polyfill.io supply-chain compromise) on a specific host, bucketed by day:

```lql
ComputerName=FR-63S3GS3 and "polyfill"
| Time:=formatTime(format="%Y-%m-%d", field=@timestamp, timezone="UTC")
| groupBy(field=[#event_simpleName, Time, ContextBaseFileName, DomainName], function=[collect(ContextBaseFileName), collect(LocalIP), collect(FirstIP4Record), count()])
```

Once a day of interest is identified, the same query with second-level timestamp precision pinpoints the exact activity window:

```lql
ComputerName=FR-63S3GS3 and "polyfill"
| Time:=formatTime(format="%Y-%m-%d %H:%M:%S%p (%Z)", field=@timestamp, timezone="UTC")
| groupBy(field=[#event_simpleName, Time, ContextBaseFileName, DomainName], function=[collect(ContextBaseFileName), collect(LocalIP), collect(FirstIP4Record), count()])
```

## Detection exclusions: auditing what's been suppressed

Every excluded detection is a visibility trade-off — worth auditing regularly rather than trusting that exclusions were all scoped correctly at creation time.

**Reusable dashboard version**, with numeric `ExclusionType`/`ExclusionSource` enums decoded and query parameters for platform, host, and detection name:

```lql
#event_simpleName=DetectionExcluded event_platform=?Platform ComputerName=?ComputerName DetectName=?DetectName
| case {
    ExclusionType=1 | ExclusionType:="BEHAVIORAL_IOA";
    ExclusionType=2 | ExclusionType:="HASH_BASED_IOC";
    ExclusionType=3 | ExclusionType:="CERTIFICATE_BASED";
    *
}
| case {
    ExclusionSource=1 | ExclusionSource:="PPDM_PROCESS_EXCLUSION";
    ExclusionSource=2 | ExclusionSource:="PPDM_TREE_EXCLUSION";
    ExclusionSource=4 | ExclusionSource:="LEGACY_SBDM_EXCLUSION";
    ExclusionSource=5 | ExclusionSource:="ALLOWED_BY_ENGINE";
    ExclusionSource=6 | ExclusionSource:="CUSTOMER_EXCLUSION";
    ExclusionSource=7 | ExclusionSource:="SYSTEM_PROCESS_EXCLUSION";
    ExclusionSource=8 | ExclusionSource:="NGAV_EXCLUSION_MIGO_TEMPLATE";
    ExclusionSource=9 | ExclusionSource:="OFP_ML_EXCLUSION_TEMPLATE";
    *;
}
| ExclusionSource=?ExclusionSource
| groupBy([event_platform, ExclusionType, ExclusionSource, TemplateInstanceId, PatternId, DetectName, ImageFileName, CommandLine], limit=10000)
```

**Targeted variant** — specifically flagging Volume Shadow Copy tampering exclusions (a classic ransomware pre-encryption step) tied to a customer-created exclusion (`ExclusionSource=6`) on a specific binary:

```lql
#event_simpleName=DetectionExcluded and ExclusionType=1 and ExclusionSource=6
| in(field="DetectName", values=["VolumeShadowSnapshotDeleted", "VolumeShadowSnapshotHidden"])
| ImageFileName=/bwork\.exe/i
| groupBy([DetectName], function=[collect([ImageFileName, CommandLine]), selectLast(@timestamp), count()])
```

Same filter, bucketed daily to trend whether the excluded behavior is increasing:

```lql
#event_simpleName=DetectionExcluded and ExclusionType=1 and ExclusionSource=6
| in(field="DetectName", values=["VolumeShadowSnapshotDeleted", "VolumeShadowSnapshotHidden"])
| ImageFileName=/bwork\.exe/i
| bucket(1d, field=["DetectName"], function=count())
| parseTimestamp(field=_bucket, format=millis)
| table([DetectName, @timestamp, _count])
```

## Custom IOA telemetry across multiple rule templates

Pulling all `CustomIOA*` events tied to a known set of Custom IOA rule template IDs — useful when validating a set of related custom rules is actually firing as expected:

```lql
#event_simpleName = CustomIOA*
| in(field="TemplateInstanceId", values=[103,104,105,106,107])
| table([#event_simpleName, TemplateInstanceId, @timestamp, ComputerName, UserName, DomainName, FileName, ImageFileName, CommandLine])
```

## Detections generated by a specific custom-intelligence IOA tactic

For rolling up detections tied to a specific IOA tactic (here, custom threat intelligence rather than a built-in behavioral pattern), scoped across a specific set of CIDs:

```lql
#repo=detections #event_simpleName=Event_EppDetectionSummaryEvent
| in(field=#repo.cid, values=[cid1, cid2, cid3])
| Technique="Indicator of Attack" Tactic="Custom Intelligence"
| groupBy([CommandLine], function=[collect(FileName), count(Hostname, distinct=true)], limit=max)
```

## Scheduled detection reporting (AI Powered IOA example)

Once a hunt or detection filter is validated (see the discovery walkthrough in the [methodology post](01-how-to-build-cql-queries.md)), the production query for a recurring report looks like this:

```lql
#event_simpleName=AssociateTreeIdWithRoot
| match(file="falcon/investigate/detect_patterns.csv", field=[PatternId])
| show_in_ui="True"
| Tactic="AI Powered IOA"
| IOCSource="Anomalous process execution"
| IOCType="Compounded behavioral activity"
| table([
aid,
ComputerName,
Tactic,
Technique,
DetectDescription,
PatternId,
IOCSource,
IOCType
])
```

Saved as a query, this can be scheduled natively in LogScale (daily, with CSV/PDF email delivery) — no external scripting required. If native scheduling isn't available in a given tenant, the FalconPy API fallback (`/detects/queries/detects/v1`, `/detects/entities/summaries/GET/v1`, scoped with `Detections: Read`) supports the same daily-report pattern via cron or Task Scheduler.

## Scoping Sensor Visibility Exclusions from real telemetry volume

Before applying a Sensor Visibility Exclusion (SVE) for a noisy process, confirm it's actually the volume driver rather than guessing from a hunch. This pulls the most active command lines and their generating processes/directories on a specific host:

```lql
aid=HOST_ID #event_simpleName=/(ProcessRollup2|ProcessRollup2Stats)/
| groupBy(field=["CommandLine"],function=[collect(ImageFileName),collect(ParentBaseFileName),groupBy(field="CommandLine", function=[count("ImageFileName", as="PRcount")]),sum("ProcessCount", as="Bounded")], limit=200000)
| eval(Total=PRcount + Bounded)
| rename(field="PRcount", as="PR count")
| sort(Total, order=desc, limit=20000)
```

**Scoping the exclusion correctly matters as much as identifying the process.** A binary invoked directly (`./script.sh`) can be excluded by its own path. A binary invoked through an interpreter (`bash script.sh`) can't be safely excluded that way — excluding `bash` itself creates a broad security gap. Two safer options in that case:
1. Wrap the script in its own launcher, and scope the SVE to the wrapper rather than to `bash`.
2. Place a dedicated copy of the interpreter at a script-specific path (e.g. `/opt/script/bin/bash`), point the script at that copy, and scope the SVE to that specific binary path.

Either approach should be validated against the host's actual workload before rollout — weigh the performance gain against the visibility given up.

## Network containment audit trail

**Which hosts were contained:**

```lql
#event_simpleName=NetworkContainmentCompleted
| table([@timestamp, ComputerName, UserName, aid])
```

**Which admin contained or lifted containment on a host** — joining Falcon admin audit activity to the sensor-side containment/uncontainment events, so the report shows who acted, from where, and on which host:

```lql
#event_simpleName=Event_UserActivityAuditEvent
| OperationName=/containment_(requested|lifted)/i
| Action:=case {
    OperationName="containment_requested" | "Contained";
    OperationName="containment_lifted" | "Lifted";
}
| join(
    {
      #event_simpleName=/Network(Containment|Uncontainment)Completed/
      | table([aid, ComputerName])
    },
    field=agent.id,
    key=aid,
    include=[ComputerName]
  )
| table([@timestamp, Action, UserId, UserIp, ComputerName])
| sort(@timestamp, order=desc)
```

Useful for incident response validation, containment reporting, and confirming an admin action actually completed at the sensor level rather than just being requested in the console.

## IP-in-range (CIDR) matching

Flagging network connections where the remote address falls inside a given subnet — here a single-host `/32`, but the same `cidr()` function scales to wider ranges:

```lql
#repo = "base_sensor"
| case {
    cidr(RemoteAddressIP4, subnet="66.235.175.109/32");
    RemoteAddressIP4 := "66.235.175.109"
}
| table([@timestamp, #event_simpleName, ComputerName, DomainName, LocalAddressIP4, RemoteAddressIP4])
```

## Distinct-count scoping: how widespread is this?

When a specific tool or binary is found on one host, the next question is always "how many others." This pattern hunts for a family of remote-access/VPN client binaries and returns a distinct host count alongside collected metadata:

```lql
"#event_simpleName" = ProcessRollup2 FileName = /barracuda|shrew|globalprotect/i
| groupBy(field=[FileName], function=[collect(event_platform), count(), count(field=ComputerName, distinct=true, as=computer_count), collect(ImageFileName), collect(CommandLine), collect(ParentBaseFileName)])
```

## Quick reference: functions used throughout

| Function | Purpose |
|---|---|
| `groupBy()` | Aggregate rows by field(s), with `function=` (count, collect, selectLast, etc.) |
| `case { }` | Conditional field rewriting — decodes numeric enums into readable labels |
| `join()` | Correlate two event streams on a shared key (`TreeId`, `TargetProcessId`, `ContextProcessId`) |
| `match()` | Look up a field's value against an uploaded CSV reference file |
| `cidr()` | Test whether an IP falls within a subnet |
| `bucket()` / `timeChart()` | Time-series aggregation and charting |
| `formatTime()` | Convert epoch timestamps into readable strings with timezone control |
| `?FieldName` | Query parameter — turns a static query into a reusable dashboard search |

Every pattern above starts the same way: confirm the event type and its fields before writing the logic that matters (see the [methodology post](01-how-to-build-cql-queries.md)). Security queries carry more consequence for being wrong — a mis-scoped exclusion reduces detection coverage, a wrong enum mapping misreports risk, a stale domain list gives false confidence. The discovery step isn't overhead here; it's what makes the result trustworthy under pressure.
