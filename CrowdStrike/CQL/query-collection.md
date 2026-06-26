### 1 - Host Count per OS
```
#event_simpleName=/(SensorHeartbeat|OsVersionInfo|ConfigStateUpdate)/
| groupBy([event_platform], function=count(aid, distinct=true, as=Host_Count_per_OS))
| sort(Host_Count_per_OS, order=desc)
```
### 2 - Query to trace channel file and configuration update activity
```
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
