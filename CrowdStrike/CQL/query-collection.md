# Collection of useful CQL queries

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
### 3 - Hosts received (and confirmed) a particular generation of channel file
```
hostname1 OR hostname2
| "#event_simpleName" = LFODownloadConfirmation
| FileName = "C-*60-*.sys"
| groupBy([ComputerName,FileName,@timestamp])
```
If you take Windows Diagnostic Logs, you will find a file Hostname_BASIC-INFO.txt, in this file we will be able to see the .sys file downloaded by agent on the system. For e.g. - 

CrowdStrike Driver Files
Filename                            Size (Bytes)    Created                   Version Info   
20505-CsInstallerService.exe        219960          01-04-2026 11:06:11       7.33.20505.0   
20709-CsInstallerService.exe        219960          22-05-2026 20:26:01       7.35.20709.0   
C-00000001-00000000-00000529.sys    3975284         16-06-2026 17:19:48                      
C-00000003-00000000-00000006.sys    52032           16-06-2026 17:19:48                      
C-00000005-00000000-00000001.sys    188             19-08-2024 22:25:02                      
C-00000007-00000000-00000195.sys    18924           16-06-2026 17:19:47                      
C-00000009-00000000-00000021.sys    1000            16-06-2026 17:19:46                      
C-00000011-00000000-00000133.sys    683             12-06-2026 11:23:35                      
C-00000012-00000000-00000006.sys    123             19-08-2024 22:25:02                      
C-00000013-00000000-00000101.sys    592884          10-06-2026 20:28:30                      

-----------------------------
