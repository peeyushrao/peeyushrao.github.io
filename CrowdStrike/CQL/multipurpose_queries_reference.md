# CrowdStrike Multipurpose Queries

## Network Containment Visibility Queries

# Query 1 — Hosts That Were Network Contained

```cql
#event_simpleName=NetworkContainmentCompleted
| table([@timestamp, ComputerName, UserName, aid])
```

## Purpose

Displays endpoints that successfully entered network containment.

This query is useful for:
- Incident response validation
- Tracking containment activity
- Confirming hosts were isolated
- Building containment reports

---

# Query 2 — Identify Which Falcon Admin Contained or Lifted a Host

```cql
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

---

## Purpose

Displays:
- Falcon admin who initiated containment
- Falcon admin who lifted containment
- Source IP of the Falcon session
- Hostname affected

This query combines:
- Falcon audit logs
- Endpoint containment sensor events

---

## Related Falcon Event Names

| Event | Description |
|---|---|
| `NetworkContainmentCompleted` | Host entered containment |
| `NetworkUncontainmentCompleted` | Host removed from containment |
| `Event_UserActivityAuditEvent` | Falcon admin activity logs |

---

## Summary

| Query | Purpose |
|---|---|
| Query 1 | Identify contained hosts |
| Query 2 | Identify which Falcon admin contained or lifted a host |

---

# Query 3 — Identify Which Falcon Admin Contained or Lifted a Host

```cql
aid=HOST_ID #event_simpleName=/(ProcessRollup2|ProcessRollup2Stats)/
| groupBy(field=["CommandLine"],function=[collect(ImageFileName),collect(ParentBaseFileName),groupBy(field="CommandLine", function=[count("ImageFileName", as="PRcount")]),sum("ProcessCount", as="Bounded")], limit=200000)
| eval(Total=PRcount + Bounded)
| rename(field="PRcount", as="PR count")
| sort(Total, order=desc, limit=20000)
```
## Purpose
If you wish to find out the the most active processes and directories that Falcon reads, you can check Advanced Event Search and run a query around the time the issue is occurring to see the active events and processes.
Based on your own judgement you can then decide what would be the binary path of the most active process(es) that is/are safe to be excluded via Sensor Visibility Exclusions for your hosts.
Please replace HOST_ID with the actual Host ID (also called AID, Agent ID or Asset ID) of the affected host.
The exclusion pattern works best for the binary paths of process(es) that generate the most events. Usually those are monitoring tools or software builds.
They also work well for scripts, but it depends how the script is called. For example, if the script is called:
./script.sh
you can apply an SVE for the binary path of where the script sits.
However, if it is called:
bash script.sh
exclusion for the script would not work since it is called by bash and we would not recommend to SVE for bash as that would create a security gap. In such case you can also:
1) create a wrapper script would have to be created for the .sh file containing the command customer mentioned. So that the wrapper script would call bash and the script. SVE would then be created for the wrapper script.
2) potentially you can make a copy of bash to the example directory:
/opt/script/bin/bash
then adjust the script to use the copy of bash and then apply a Sensor Visibility Exclusion for the above file path.
The above recommendation should be configured and tested with regard to the hosts' workloads and the number of resources available.
Weight current performance with security concerns and decide what configuration is best for their environment.

---
