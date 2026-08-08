# General-Purpose CQL: Fleet Inventory, Upgrades, and Capacity Queries

Not every CQL query is chasing a threat. A large share of day-to-day LogScale work is operational: sensor inventory, upgrade tracking, resource utilization, channel file delivery, host lifecycle. These queries reward being built once and trusted repeatedly — which only works if the field discovery step from the [methodology post](01-how-to-build-cql-queries.md) happened up front.

---

## Host count per OS

The simplest possible fleet-visibility query — how many distinct hosts per platform are actually reporting in, using three event types that all carry OS/platform data:

```lql
#event_simpleName=/(SensorHeartbeat|OsVersionInfo|ConfigStateUpdate)/
| groupBy([event_platform], function=count(aid, distinct=true, as=Host_Count_per_OS))
| sort(Host_Count_per_OS, order=desc)
```

## Sensor upgrade history and version tracking

`AgentOnline` is the primary event for tracking sensor version and upgrade history. The fields worth knowing: `AgentVersion`, `ConfigBuild`, `BuildNumber`, `ComputerName`, `event_platform`, `aid`.

**Single host — full version history:**

```lql
#event_simpleName=AgentOnline
aid=<your_aid_here>
| sort(@timestamp, order=desc)
| table([@timestamp, ComputerName, ConfigBuild, AgentVersion, BuildNumber, event_platform])
```

**Single host — last 30 days**, for recent-change troubleshooting:

```lql
#event_simpleName=AgentOnline
aid=<your_aid_here>
| @timestamp > now() - 30d
| sort(@timestamp, order=desc)
| table([@timestamp, ComputerName, ConfigBuild, AgentVersion, BuildNumber, event_platform])
```

**Single host — upgrade events only**, filtering the full history down to just the moments the version actually changed:

```lql
#event_simpleName=AgentOnline
aid=<your_aid_here>
| sort(@timestamp, order=asc)
| delta(AgentVersion, as=VersionChanged)
| VersionChanged != 0
| sort(@timestamp, order=desc)
| table([@timestamp, ComputerName, ConfigBuild, AgentVersion, BuildNumber, event_platform])
```

**Fleet-wide upgrade history** — every `AgentOnline` event across every host, for broad investigations:

```lql
#event_simpleName=AgentOnline
| sort(@timestamp, order=desc)
| table([@timestamp, aid, ComputerName, ConfigBuild, AgentVersion, BuildNumber, event_platform])
```

**Latest version per host** — current sensor inventory, one row per host:

```lql
#event_simpleName=AgentOnline
| groupBy([aid, ComputerName, event_platform], function=(
    selectFromMax(field="@timestamp", include=[@timestamp, ConfigBuild, AgentVersion, BuildNumber])
))
| sort(AgentVersion, order=desc)
| table([@timestamp, ComputerName, ConfigBuild, AgentVersion, BuildNumber, event_platform])
```

**Fleet-wide version distribution** — the query I use as a baseline before any upgrade push, since it shows the actual starting distribution rather than the assumed one:

```lql
#event_simpleName=AgentOnline
| groupBy([aid, ComputerName], function=(
    selectFromMax(field="@timestamp", include=[AgentVersion, ConfigBuild, event_platform])
))
| groupBy([AgentVersion], function=(count(aid, as=HostCount)))
| sort(HostCount, order=desc)
| table([AgentVersion, HostCount])
```

**Which of these to reach for:**

| Query | Purpose |
|---|---|
| Single host – all version fields | Daily troubleshooting |
| Single host – last 30 days | Recent changes |
| Upgrade events only | Historical upgrade timeline |
| Fleet-wide upgrade history | Broad investigations |
| Latest version per host | Current inventory / compliance |
| Fleet-wide version distribution | Sensor Update Policy rollout tracking |

## Channel file and configuration update tracing

Tracing channel file and config delivery to a specific host — the event types that carry this:

```lql
aid="<aid>"
| in(#event_simpleName, values=[
    "ConfigDownloadComplete",
    "ConfigStateUpdate",
    "ChannelDataDownloadComplete",
    "ChannelVersionRequired",
    "LFODownloadConfirmation"
])
| table([@timestamp,#event_simpleName,Status,TargetFileName,FileName])
| sort(@timestamp)
```

This one query covers a surprising number of operational cases:

- **Provisioning verification** — confirm a newly deployed sensor received all its channel files
- **Policy propagation** — after changing a prevention policy or host group, confirm the sensor's `ConfigStateUpdate` reflects it
- **RFM remediation** — confirm the OSFM certification file arrived via `LFODownloadConfirmation`
- **Channel file gaps** — if `ChannelVersionRequired` appears with no subsequent `ChannelDataDownloadComplete`, the sensor is likely stuck on a network or proxy issue
- **Post-incident audit** — reconstruct a host's content-update history around an incident window

**Confirming a specific channel file generation reached a host**, useful when validating a targeted content rollout:

```lql
hostname1 OR hostname2
| "#event_simpleName" = LFODownloadConfirmation
| FileName = "C-*60-*.sys"
| groupBy([ComputerName,FileName,@timestamp])
```

If corroborating this against local diagnostics, Windows diagnostic logs include a `Hostname_BASIC-INFO.txt` file listing the actual `.sys` channel files present on the host with their creation timestamps — useful for confirming the LogScale result against ground truth on the endpoint itself.

## Resource utilization and system capacity

**Daily-or-longer average utilization**, joining `SystemCapacity`, `UserLogon`, and `ResourceUtilization` events per host via `selfJoinFilter`, converting raw memory/disk figures into human-readable units:

```lql
(#event_simpleName=/^(SystemCapacity|UserLogon|ResourceUtilization)$/) OR (#repo=sensor_metadata #data_source_name=aidmaster) aid=myaid
| case {
    event_platform=Mac | ProductType:=1;
    event_platform=Win | ProductType:=2;
    event_platform=Lin | ProductType:=3;
    *;
}
| $falcon/helper:enrich(field=ProductType)
| selfJoinFilter(field=[aid], where=[{#event_simpleName=SystemCapacity},{#event_simpleName=ResourceUtilization},{#event_simpleName=UserLogon}, {#repo=sensor_metadata #data_source_name=aidmaster}])
| groupBy([aid], function=([selectLast([ComputerName,LocalAddressIP4, UserName,event_platform, ProductType, AgentVersion, Version, CpuProcessorName,MaxUsedRam,MaxCpuUsage,AvailableDiskSpace,UsedDiskSpace, PercentDiskUsed]), avg(AverageCpuUsage, as=AverageCpuUsage), avg(AverageUsedRam, as=AverageUsedRam)]))
| PercentDiskUsed:=AvailableDiskSpace/(UsedDiskSpace+AvailableDiskSpace)*100 
| PercentDiskUsed:=format(format="%.2f %%", field=[PercentDiskUsed])
| MemoryTotal:=(MemoryTotal/1024/1024/1024) 
| MemoryTotal:=round(MemoryTotal) 
| MemoryTotal:=format(format="%s GB", field=[MemoryTotal])
| AverageUsedRam:=(AverageUsedRam/1024) 
| AverageUsedRam:=format(format="%,.2f GB", field=[AverageUsedRam])
| MaxUsedRam:=(MaxUsedRam/1024) 
| MaxUsedRam:=format(format="%,.2f GB", field=[MaxUsedRam])
| AverageCpuUsage:=format(format="%.2f %%", field=[AverageCpuUsage])
| MaxCpuUsage:=format(format="%.2f %%", field=[MaxCpuUsage])
| default(value="-", field=[ComputerName, LocalAddressIP4, UserName,event_platform, AgentVersion, Version, AverageCpuUsage, MaxCpuUsage, MemoryTotal, AverageUsedRam, MaxUsedRam, UsedDiskSpace, AvailableDiskSpace, PercentDiskUsed], replaceEmpty=true) 
| rename(field="aid", as="Agent ID")
| rename(field="ComputerName", as="Endpoint")
| rename(field="event_platform", as="Platform")
| rename(field="AgentVersion", as="Sensor Version")
| rename(field="Version", as="OS")
| rename(field="AverageCpuUsage", as="Avg. CPU")
| rename(field="MaxCpuUsage", as="Max. CPU")
| rename(field="AverageUsedRam", as="Avg. RAM")
| rename(field="MaxUsedRam", as="Max. RAM used")
| rename(field="PercentDiskUsed", as="% of Disk Available")
| rename(field="UserName", as="Last User")
| table(["Agent ID", "Endpoint", "LocalAddressIP4","Last User", "Platform", "Sensor Version", "OS", "Avg. CPU", "Max. CPU","Avg. RAM", "Max. RAM used", "% of Disk Available"], limit=20000)
| sort("Avg. CPU")
```

**15-minute bucketed utilization** for finer-grained trending — closer to what you'd want while actively investigating a resource spike rather than reporting a daily average:

```lql
aid=myaid
| case {
    event_platform=Mac | ProductType:=1;
    event_platform=Win | ProductType:=2;
    event_platform=Lin | ProductType:=3;
    *;
}
| bucket(span=15m, function=([
    avg(AverageCpuUsage, as=AvgCPU),
    max(MaxCpuUsage, as=MaxCPU),
    avg(AverageUsedRam, as=AvgRAM_MB),
    max(MaxUsedRam, as=MaxRAM_MB),
    avg(AvailableDiskSpace, as=AvailableDiskSpace),
    avg(UsedDiskSpace, as=UsedDiskSpace)
  ]))
| AvgCPU=* OR MaxRAM_MB=*
| Timestamp := formatTime(format="%Y-%m-%d %H:%M:%S", field=_bucket)
| PercentDiskAvailable := AvailableDiskSpace/(UsedDiskSpace+AvailableDiskSpace)*100
| AvgRAM_GB := AvgRAM_MB/1024
| MaxRAM_GB := MaxRAM_MB/1024
| AvgCPU := format(format="%.2f %%", field=[AvgCPU])
| MaxCPU := format(format="%.2f %%", field=[MaxCPU])
| AvgRAM_GB := format(format="%.2f GB", field=[AvgRAM_GB])
| MaxRAM_GB := format(format="%.2f GB", field=[MaxRAM_GB])
| PercentDiskAvailable := format(format="%.2f %%", field=[PercentDiskAvailable])
| table([Timestamp, AvgCPU, MaxCPU, AvgRAM_GB, MaxRAM_GB, PercentDiskAvailable], limit=20000)
| sort(_bucket, order=desc)
```

**A gotcha worth knowing before you trust the disk column:** `PercentDiskAvailable` can come back null on rows where CPU/RAM are populated. That's because disk figures (`AvailableDiskSpace`/`UsedDiskSpace`) come from `SystemCapacity` events specifically, while CPU/RAM come from `ResourceUtilization` events — and `SystemCapacity` events are sparse, often only once every several hours. A filter like `AvgCPU=* OR MaxRAM_MB=*` lets buckets through that have CPU/RAM but no disk data in that same 15-minute window. This is expected behavior given event sparsity, not a bug — if consistent disk fill-in matters more than granularity, widen the bucket span (1h or 4h) so more event types land in the same window.

## First seen and last heartbeat

Combining static host metadata (`aidmaster`) with the most recent `SensorHeartbeat` event, to answer "when did we first see this host, and when did it last check in" in one row:

```lql
#repo=sensor_metadata
#data_source_name=aidmaster
| aid="" OR ComputerName=""
| join({
    #repo=base_sensor
    #event_simpleName=SensorHeartbeat
    | groupBy([aid], function=[selectLast([@timestamp])], limit=max)
    | rename(@timestamp, as=LastHeartbeat)
  }, field=[aid], key=aid, mode=left, include=LastHeartbeat)
| LastHeartbeat := formatTime(format="%FT%T%z", field=LastHeartbeat)
| FirstSeenMs := FirstSeen * 1000
| FirstSeen   := formatTime(field="FirstSeenMs", format="%Y-%m-%d")
| table([aid, ComputerName, event_platform, Version, MachineDomain, OU, SiteName, FirstSeen, LastHeartbeat])
```

**Dashboard-ready version** with `?aid`/`?ComputerName` as fill-in-the-blank query parameters:

```lql
#repo=sensor_metadata
#data_source_name=aidmaster
| aid=?aid OR ComputerName=?ComputerName
| join({
    #repo=base_sensor
    #event_simpleName=SensorHeartbeat
    | groupBy([aid], function=[selectLast([@timestamp])], limit=max)
    | rename(@timestamp, as=LastHeartbeat)
  }, field=[aid], key=aid, mode=left, include=LastHeartbeat)
| LastHeartbeat := formatTime(format="%FT%T%z", field=LastHeartbeat)
| FirstSeenMs := FirstSeen * 1000
| FirstSeen   := formatTime(field="FirstSeenMs", format="%Y-%m-%d")
| table([aid, ComputerName, event_platform, Version, MachineDomain, OU, SiteName, FirstSeen, LastHeartbeat])
```

## Installed application inventory

Listing installed applications on a host, with a query-parameter hostname so it doubles as a reusable dashboard search:

```lql
#repo = "base_sensor" ComputerName=?HostName #event_simpleName=InstalledApplication
| Time:=formatTime(format="%Y-%m-%d %H:%M:%S%p", field=@timestamp, timezone="CET")
| table([Time, event_platform, ComputerName, UserName, AppName, AppPath, AppVendor, AppVersion], sortby=Time, order=desc)
```

## Multi-tenant / MSSP: resolving parent CID to a readable name

In an MSSP or multi-CID Flight Control setup, raw CID GUIDs aren't useful in a report — this enriches `ProcessRollup2` events with a friendly customer alias via a CSV lookup:

```lql
#event_simpleName="ProcessRollup2" ComputerName = "aks-ogczlinpool-13679250-vmss000004"
| cid=~match(file="cids.csv", include="cid_alias", strict=false)
| table([@timestamp, cid_alias, ComputerName, FilePath, FileName, CommandLine, TargetProcessId, ParentProcessId])
```

Same pattern generalizes to any host — swap `ComputerName`, or better, convert it to a `ComputerName=?HostName` query-parameter version if it's going to be reused often.

## Scheduling recurring reports without external infrastructure

For any of the above turned into a recurring report (daily upgrade rollout status, weekly EOS exposure, etc.), LogScale's native scheduling covers the common case end-to-end:

1. Build and validate the query under **Investigate → Log Search**, over the intended time window (e.g. **Last 24 Hours**).
2. Save the query with a clear name.
3. Configure a schedule — daily, at a fixed time, with email recipients and CSV/PDF output.
4. Optionally, build dashboard widgets (detection count, timeline, table) on top of the same query — dashboards can be scheduled the same way.

This avoids standing up external infrastructure for what's fundamentally a "run this query daily and email the result" need. If native scheduling isn't available in a given tenant, the FalconPy API (`Detections: Read` scope, or the equivalent read scope for the data in question) is the fallback via cron or Task Scheduler.

## Takeaway

Operational queries are worth the up-front cost of getting field names and event types right, because they get reused for months. A sensor-inventory or utilization query built on guessed fields might return *something* that looks plausible in a report — the real failure mode isn't a crash, it's a quietly wrong number that ends up cited somewhere before anyone catches it. The [discovery-first methodology](01-how-to-build-cql-queries.md) pays for itself fastest on exactly this class of query.
