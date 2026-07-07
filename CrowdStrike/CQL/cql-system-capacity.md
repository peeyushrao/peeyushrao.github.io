# CQL Query  - Resource Utilization

This query aggregates system capacity, user logon activity, and resource utilization data, enriched with sensor metadata.
https://community.crowdstrike.com/falcon-platform-raptor-release-84/cql-query-help-resource-utilization-1111

## Query -1: Average Utlization for 1 day or greater than that

```sql
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

## Notes
- Uses selfJoinFilter to correlate multiple event types per agent (aid)
- Applies enrichment via Falcon helper
- Converts memory and disk metrics into human-readable formats
- Outputs a summarized table sorted by average CPU usage

## Query -2: Average Utlization in 15 minutes chunk
```
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
![AES Diagram](/images/aes1.png)

Notice in your screenshot: PercentDiskAvailable is null across all rows now, even though CPU/RAM populated. That's because AvailableDiskSpace/UsedDiskSpace come only from SystemCapacity events, while AverageCpuUsage/MaxCpuUsage come from ResourceUtilization events — and your filter AvgCPU=* OR MaxRAM_MB=* is letting through buckets that have CPU/RAM data but no disk data in that same 15-minute window. That's expected behavior given how sparse the disk-capacity events are (often just once every several hours), not a bug — but if you want disk % filled in more consistently, you'd want a wider bucket span (e.g. 1h or 4h) so more event types land in the same window.
