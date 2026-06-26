### 1 - Host Count per OS
```
#event_simpleName=/(SensorHeartbeat|OsVersionInfo|ConfigStateUpdate)/
| groupBy([event_platform], function=count(aid, distinct=true, as=Host_Count_per_OS))
| sort(Host_Count_per_OS, order=desc)
```
--------------
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
```
### Primary Use Cases

Troubleshooting provisioning failures — verify that a newly deployed sensor received all its channel files

Confirming policy changes propagated — after modifying a prevention policy or host group, validate the sensor received the ConfigStateUpdate

RFM remediation verification — confirm the OSFM certification file arrived via LFODownloadConfirmation

Diagnosing channel file gaps — if ChannelVersionRequired appears without a subsequent ChannelDataDownloadComplete, the sensor may be stuck waiting for a download (possible network/proxy issue)

Post-incident audit — reconstruct the sensor's content update history around the time of an incident

--------------
