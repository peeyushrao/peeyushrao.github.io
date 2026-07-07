# CrowdStrike Falcon LogScale (LQL) Hunting Query Samples

> **Platform:** CrowdStrike Falcon LogScale (Next-Gen SIEM / Event Search)
> **Language:** LQL — LogScale Query Language (also referred to as CQL in some CrowdStrike docs)
> **Purpose:** A working reference set of threat hunting / detection engineering queries against `base_sensor` telemetry — process execution, DNS, network connections, browser extensions, installed applications, and exclusions.

These are genuine **CrowdStrike Falcon hunting queries**, written for the LogScale query engine that sits behind Falcon's Event Search / Advanced Event Search. They're the kind of queries a threat hunter or detection engineer runs directly against raw sensor telemetry (`#repo="base_sensor"`) rather than against pre-built detections — which is exactly what makes them useful for building custom hunts, enrichment pipelines, and IOA-style logic on top of raw events.

---

## Table of Contents

1. [Simple Count of Event Types](#1-simple-count-of-event-types)
2. [Simple Endpoint Activity Check (Filtered Events on a Host)](#2-simple-endpoint-activity-check-filtered-events-on-a-host)
3. [Process & File Telemetry + Detections (Join on TreeId)](#3-process--file-telemetry--detections-join-on-treeid)
4. [Process Telemetry and Associated Detection — "Better" Join](#4-process-telemetry-and-associated-detection--better-join)
5. [Leveraging Regex for Command Line Arguments](#5-leveraging-regex-for-command-line-arguments)
6. [List Installed Applications on a Host](#6-list-installed-applications-on-a-host)
7. [Excluded Detections — Customizable Field Filters](#7-excluded-detections--customizable-field-filters)
8. [Excluded Detections — Hardcoded Filter + Regex](#8-excluded-detections--hardcoded-filter--regex)
9. [Merging Several Telemetry Types (Custom IOA Templates)](#9-merging-several-telemetry-types-custom-ioa-templates)
10. [DNS Requests with Associated Process Data (Join)](#10-dns-requests-with-associated-process-data-join)
11. [Checking Network Activity on a Host + Keyword](#11-checking-network-activity-on-a-host--keyword)
12. [Same Query, More Granular Time Frame](#12-same-query-more-granular-time-frame)
13. [Find a List of Extensions from a CSV File](#13-find-a-list-of-extensions-from-a-csv-file)
14. [Find a List of Domain Names Using Regex](#14-find-a-list-of-domain-names-using-regex)
15. [Timechart of Browser Extension Count by Browser Name](#15-timechart-of-browser-extension-count-by-browser-name)
16. [Get Data from the Parent CID](#16-get-data-from-the-parent-cid)
17. [Distinct Counts](#17-distinct-counts)
18. [IP in a Range (CIDR Match)](#18-ip-in-a-range-cidr-match)

---

## 1. Simple Count of Event Types

See the distribution of event types being generated across the fleet.

```lql
#repo="base_sensor"
| groupBy([#event_simpleName], function=count(), limit=1000)
| sort(field=#event_simpleName, type=string, order=ascending, limit=1000)
```

---

## 2. Simple Endpoint Activity Check (Filtered Events on a Host)

Filter to a specific host + agent ID (`aid`) and pull the core process/file lifecycle events.

```lql
ComputerName = DC-TEST-VM-SGO aid = 45c4556db0b347fd8f129b48c42ed1b3
| in(field=#event_simpleName, values=["ProcessRollup2", "*FileWritten", "AssociateTreeIdWithRoot"])
| table([@timestamp, #event_simpleName, ImageFileName, CommandLine], limit=1000)
```

A related, simpler variant — just count event types on one host:

```lql
ComputerName = "DC-TEST-VM-SGO"
| groupBy(["#event_simpleName"])
```

---

## 3. Process & File Telemetry + Detections (Join on TreeId)

**UPDATED** version using regex on `ImageFileName`. Joins raw process/file telemetry with `AssociateTreeIdWithRoot` events on `TreeId` to pull in the associated `DetectName` and `ComputerName`, and formats two separate timestamps in two different timezones (CET for the sensor event, PST for the tree event).

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

---

## 4. Process Telemetry and Associated Detection — "Better" Join

Flags rows that have a `TreeId` (i.e., were part of a detected tree) as `"Detected"` using a `case` block, then joins against `AssociateTreeIdWithRoot` on `TargetProcessId` to pull in `DetectName`/`DetectDescription`. This is the cleaner join pattern versus #3 above.

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

---

## 5. Leveraging Regex for Command Line Arguments

Hunt for suspicious `chmod` permission changes (755 or `a+w`) on Linux hosts — a common technique for making a dropped file executable/world-writable.

```lql
event_platform = Lin #event_simpleName = "ProcessRollup2" CommandLine = /.*chmod\s+(755|a+w).*/
| table([@timestamp, #event_simpleName, ImageFileName, CommandLine], limit=1000)
```

---

## 6. List Installed Applications on a Host

Uses a query-time variable (`?HostName`) so the host can be swapped in at run time from the LogScale UI.

```lql
#repo = "base_sensor" ComputerName=?HostName #event_simpleName=InstalledApplication
| Time:=formatTime(format="%Y-%m-%d %H:%M:%S%p", field=@timestamp, timezone="CET")
| table([Time, event_platform, ComputerName, UserName, AppName, AppPath, AppVendor, AppVersion], sortby=Time, order=desc)
```

---

## 7. Excluded Detections — Customizable Field Filters

Decodes the numeric `ExclusionType` and `ExclusionSource` enums into human-readable labels using nested `case` blocks, with query variables for platform, host, and detection name.

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

<details>
<summary>💡 Tip: reading this one</summary>

The `?Platform`, `?ComputerName`, `?DetectName`, and `?ExclusionSource` tokens are LogScale **query parameters** — they render as fill-in-the-blank fields in the Search UI, so this one query becomes a reusable dashboard tile rather than a one-off hunt.
</details>

---

## 8. Excluded Detections — Hardcoded Filter + Regex

A narrower, hardcoded version of #7 focused specifically on Volume Shadow Copy tampering exclusions (a classic ransomware pre-encryption step) tied to a specific binary name.

```lql
#event_simpleName=DetectionExcluded and ExclusionType=1 and ExclusionSource=6
| in(field="DetectName", values=["VolumeShadowSnapshotDeleted", "VolumeShadowSnapshotHidden"])
| ImageFileName=/bwork\.exe/i
| groupBy([DetectName], function=[collect([ImageFileName, CommandLine]), selectLast(@timestamp), count()])
```

**Detection in monitoring mode** variant — same filter, bucketed into daily counts for trending:

```lql
#event_simpleName=DetectionExcluded and ExclusionType=1 and ExclusionSource=6
| in(field="DetectName", values=["VolumeShadowSnapshotDeleted", "VolumeShadowSnapshotHidden"])
| ImageFileName=/bwork\.exe/i
| bucket(1d, field=["DetectName"], function=count())
| parseTimestamp(field=_bucket, format=millis)
| table([DetectName, @timestamp, _count])
```

---

## 9. Merging Several Telemetry Types (Custom IOA Templates)

Pulls all Custom IOA (`CustomIOA*`) events tied to a specific set of Custom IOA rule template IDs.

```lql
#event_simpleName = CustomIOA*
| in(field="TemplateInstanceId", values=[103,104,105,106,107])
| table([#event_simpleName, TemplateInstanceId, @timestamp, ComputerName, UserName, DomainName, FileName, ImageFileName, CommandLine])
```

---

## 10. DNS Requests with Associated Process Data (Join)

Pivots from a suspicious DNS lookup back to the process that made it, by joining `DnsRequest` to `ProcessRollup2` on `ContextProcessId` ↔ `TargetProcessId`.

```lql
#event_simpleName="DnsRequest" and DomainName = "cookieaquila.com" and FileName != "ZSATunnel.exe"
| in(field="ComputerName", values=["DE-L082605"])
| join({#event_simpleName="ProcessRollup2" and FileName != "ZSATunnel.exe" | in(field="ComputerName", values=["DE-L082605"])}, field=["ContextProcessId"], key="TargetProcessId", include=["FileName", "UserName", "ImageFileName", "CommandLine"], mode=left)
| table(["@timestamp", "ComputerName", "UserName", "DomainName", "FileName", "ImageFileName", "CommandLine"])
```

---

## 11. Checking Network Activity on a Host + Keyword

Free-text keyword search (`"polyfill"` — relevant to the 2024 polyfill.io supply-chain compromise) combined with a host filter, bucketed by day.

```lql
ComputerName=FR-63S3GS3 and "polyfill"
| Time:=formatTime(format="%Y-%m-%d", field=@timestamp, timezone="UTC")
| groupBy(field=[#event_simpleName, Time, ContextBaseFileName, DomainName], function=[collect(ContextBaseFileName), collect(LocalIP), collect(FirstIP4Record), count()])
```

---

## 12. Same Query, More Granular Time Frame

Identical to #11, but formats the timestamp down to the second (with AM/PM and timezone abbreviation) instead of just the date — useful once you've narrowed the day and need to pinpoint the exact activity window.

```lql
ComputerName=FR-63S3GS3 and "polyfill"
| Time:=formatTime(format="%Y-%m-%d %H:%M:%S%p (%Z)", field=@timestamp, timezone="UTC")
| groupBy(field=[#event_simpleName, Time, ContextBaseFileName, DomainName], function=[collect(ContextBaseFileName), collect(LocalIP), collect(FirstIP4Record), count()])
```

---

## 13. Find a List of Extensions from a CSV File

Cross-references installed browser extensions against a CSV lookup list of known-malicious extension IDs (`cyberhaven_bad_extensionId_2.csv` — from the December 2024 Cyberhaven browser extension supply-chain attack), decodes the numeric browser enum, and flags each install as `BAD` / `UNKNOWN` / `MAYBE_OK`.

```lql
#event_simpleName=InstalledBrowserExtension  // Filter on InstalledBrowserExtensions
| match(file="cyberhaven_bad_extensionId_2.csv", field=[BrowserExtensionId], column=BrowserExtensionId)  // Filter the known compromised Browser Extensions
| groupBy([aid, ComputerName, UserName, BrowserName, BrowserExtensionId, BrowserExtensionName, BrowserExtensionVersion, Version, BrowserExtensionStatusEnabled, BrowserExtensionPath], function=[collect([BrowserProfileId, BrowserProfileName, event_platform]), selectLast([@timestamp])])  // Keep only one record per host, extension and version
| rename(field="Version", as="knownBad")
| case {  // Rename the browser from a single number to a real browser name
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
    test(BrowserExtensionVersion==knownBad) | Status:="BAD";  // Label the version
    knownBad="" | Status:="UNKNOWN";
    * | Status:="MAYBE_OK";  // Versions we do not know are BAD are not always GOOD, experience has shown that.
}
| formatTime(format="%Y-%m-%dT%H:%M:%S.%L%z", field=@timestamp, as="installts")  // Format the extension presence report timestamp as a readable string
| format(format="%s\t%s\t%s", field=[Status, BrowserExtensionVersion, installts], as="Status")  // Concatenate some fields together
| groupBy(  // Regroup by host and extension, grouping together
    [aid, ComputerName, UserName, BrowserName, BrowserExtensionId, BrowserExtensionName, BrowserExtensionStatusEnabled],
    function=[
        collect([Status, BrowserExtensionVersion, Version, BrowserProfileId, BrowserProfileName, event_platform, BrowserExtensionPath]),
        selectLast([@timestamp])
    ]
)
```

---

## 14. Find a List of Domain Names Using Regex

Hunts for known malicious/typosquat extension-update or C2 domains (fake/rogue browser extension marketplaces) contacted from a Chromium-family browser process, using a combined regex of domain suffixes.

```lql
#repo="base_sensor"
| in(#event_simpleName, values=["DnsRequest", "SuspiciousDnsRequest"])
| ContextBaseFileName=/(?:chrome|chromium|microsoftedge|msedge|brave|opera)/i
| DomainName=/(?:(?:cyberhavenext|primusext|internxtvpn|censortracker|iobit|ultrablock|dearflip|pieadblock)\.pro|(?:castorus|parrottalks|bookmarkfc|yujaverity|readermodeext|tinamind)\.info|(?:vpncity|wayinai|uvoice|vidnozflex)\.live|moonsift\.store|(?:wakelet|locallyext)\.ink|(?:sclpfybn|tnagofsg))/i
| groupBy([aid, ComputerName], function=[selectLast([@timestamp]), count(), collect([DomainName, ContextBaseFileName, UserName])])
```

> **Note:** the source document's regex had a stray trailing `F` after the closing `/i` — removed here as a likely OCR/copy artifact. Double-check this pattern against your original source before running it in production.

---

## 15. Timechart of Browser Extension Count by Browser Name

Same browser-name decoding as #13, but charted over time by browser using `timeChart`.

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

---

## 16. Get Data from the Parent CID

Enriches `ProcessRollup2` events with a friendly customer/tenant alias by matching the numeric CID against a lookup CSV (`cids.csv`) — handy in multi-tenant / MSSP Falcon setups where you're hunting across child CIDs and want readable names instead of raw CID GUIDs.

**Original sample (host: `aks-ogczlinpool-13679250-vmss000004`):**

```lql
#event_simpleName="ProcessRollup2" ComputerName = "aks-ogczlinpool-13679250-vmss000004"
| cid=~match(file="cids.csv", include="cid_alias", strict=false)
| table([@timestamp, cid_alias, ComputerName, FilePath, FileName, CommandLine, TargetProcessId, ParentProcessId])
```

**Your variant (host: `IPL-1YTJJJJ2`):**

```lql
#event_simpleName="ProcessRollup2" ComputerName = "IPL-1YTJJJJ2"
| cid=~match(file="cids.csv", include="cid_alias", strict=false)
| table([@timestamp, cid_alias, ComputerName, FilePath, FileName, CommandLine, TargetProcessId, ParentProcessId])
```

Same pattern, just swap `ComputerName` per host — this is a good candidate to turn into a query-parameter version (`ComputerName=?HostName`) like #6, if you're going to reuse it often.

---

## 17. Distinct Counts

Hunts for known remote-access/VPN client binaries (Barracuda, ShrewSoft VPN, GlobalProtect) and shows a **distinct** count of affected computers, alongside collected metadata — useful for scoping how widespread a given tool's presence is across the fleet.

```lql
"#event_simpleName" = ProcessRollup2 FileName = /barracuda|shrew|globalprotect/i
| groupBy(field=[FileName], function=[collect(event_platform), count(), count(field=ComputerName, distinct=true, as=computer_count), collect(ImageFileName), collect(CommandLine), collect(ParentBaseFileName)])
```

---

## 18. IP in a Range (CIDR Match)

Normalizes/flags network connection events where `RemoteAddressIP4` falls inside a given CIDR block — here a single-host `/32` match, but the same `cidr()` function works for wider ranges too.

```lql
#repo = "base_sensor"
| case {
    cidr(RemoteAddressIP4, subnet="66.235.175.109/32");
    RemoteAddressIP4 := "66.235.175.109"
}
| table([@timestamp, #event_simpleName, ComputerName, DomainName, LocalAddressIP4, RemoteAddressIP4])
```

---

## Quick Reference: Common LQL Functions Used Above

| Function | Purpose |
|---|---|
| `groupBy()` | Aggregate rows by field(s), with optional `function=` (count, collect, selectLast, etc.) |
| `case { }` | Conditional field rewriting — used heavily to decode numeric enums into labels |
| `join()` | Correlate two event streams on a shared key (e.g., `TreeId`, `TargetProcessId`) |
| `match()` | Look up a field's value against an uploaded CSV reference file |
| `cidr()` | Test whether an IP falls within a subnet |
| `bucket()` / `timeChart()` | Time-series aggregation and charting |
| `formatTime()` | Convert epoch timestamps into human-readable strings, with timezone control |
| Query parameters (`?FieldName`) | Turn a static query into a reusable, fill-in-the-blank dashboard search |

---

<details>
<summary>📌 Source & Notes</summary>

- Original source: personal LQL query notes/PDF collection, CrowdStrike Falcon LogScale.
- Section titles and query bodies were reconstructed from a PDF where the title list and query list appeared as separate blocks; mapping is best-effort based on query content and logic. If you spot a mismatch against your original notes, flag it and I'll fix the pairing.
- One regex (§14) had a likely OCR artifact (stray trailing `F`) removed — verify against your original before production use.
</details>
