# System Capacity & User Activity Query

This query aggregates system capacity, user logon activity, and resource utilization data, enriched with sensor metadata.

## Query

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
