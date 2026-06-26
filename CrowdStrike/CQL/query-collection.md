### 1 - Host Count per OS
```
#event_simpleName=/(SensorHeartbeat|OsVersionInfo|ConfigStateUpdate)/
| groupBy([event_platform], function=count(aid, distinct=true, as=Host_Count_per_OS))
| sort(Host_Count_per_OS, order=desc)
```
