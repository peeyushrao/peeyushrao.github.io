# CrowdStrike Multipurpose Queries

## Network Containment Visibility Queries

# Query 1 — Hosts That Were Network Contained

```sql
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

```sql
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

