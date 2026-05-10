# CrowdStrike Falcon Admin Interview Questions — The Complete Guide

> **Who this is for:** Security engineers and SOC analysts preparing for Falcon Administrator, Detection Engineer, or senior EDR roles. These questions are grouped by depth — from foundational architecture to senior-level judgment calls that separate operators from practitioners.

---

## How Interviewers Actually Think

Most Falcon interviews are testing five things — not your memorization of the UI:

| Area | What They Actually Want |
|---|---|
| Platform Knowledge | Do you understand Falcon modules and architecture? |
| Troubleshooting | Can you solve operational problems calmly and methodically? |
| Detection Understanding | Do you understand attacker behavior — not just tool behavior? |
| Security Judgment | Do you tune safely instead of blindly excluding? |
| Incident Handling | Can you investigate endpoint activity logically under pressure? |

The red flags are consistent: candidates who talk about Falcon like it's antivirus, candidates who say "I'd whitelist it" when handling false positives, and candidates who can't explain *why* they'd take an action — only *what* the action is.

---

## Section 1: Architecture & Fundamentals

### Q1. Explain CrowdStrike Falcon's architecture end-to-end

**What strong answers include:**

- Kernel-level sensor → cloud telemetry pipeline
- Lightweight agent concept (processing happens in cloud, not on host)
- Behavioral detections via IOAs — not signature matching
- Threat Graph as the global graph-native intelligence layer
- Real Time Response (RTR) channel over the same persistent connection
- Cloud-native advantages: retroactive detection, global intelligence, no signature updates needed

**Red flags:**
- Only talks about "antivirus"
- Cannot explain why Falcon differs architecturally from legacy AV
- Doesn't mention the distinction between prevention and detection

---

### Q2. What is the difference between IOC and IOA in CrowdStrike?

*This question filters surface-level admins from deeper defenders.*

**Good answer:**

- **IOC** = known bad artifact: file hash, IP address, domain name
- **IOA** = behavioral detection: process injection pattern, credential dumping chain, lateral movement sequence

**Great answer adds:**

IOAs are architecturally stronger because attackers can trivially change hashes, domains, and IPs — but they cannot fundamentally change *what they need to do*. An attacker still needs to execute code, access credentials, establish C2. The behavioral pattern is constant even when the tools change entirely.

IOAs catch zero-days, fileless malware, and LOLBin abuse that no IOC-based system can detect.

---

### Q3. Explain Falcon Complete, Falcon Insight, Falcon Discover, and Falcon OverWatch

*This checks platform breadth — not just depth in one area.*

| Module | What It Does | Who Operates It |
|---|---|---|
| **Falcon Insight** | Core EDR — detection, investigation, response | Customer |
| **Falcon Discover** | Asset visibility, IT hygiene, unsanctioned software | Customer |
| **Falcon OverWatch** | Managed threat hunting — CS hunters proactively hunt your environment | CrowdStrike |
| **Falcon Complete** | Full managed detection and response (MDR) | CrowdStrike |

**Bonus signal:** Candidates who explain *where responsibilities shift* between the customer and CrowdStrike — especially for OverWatch vs Complete — demonstrate real platform fluency.

---

### Q4. How does Falcon handle environments with strict egress filtering or an explicit proxy? What breaks if the proxy is misconfigured?

**Strong answer:**

Falcon sensors communicate outbound via HTTPS (port 443) to CrowdStrike's cloud endpoints. In proxy environments:

- The proxy must be configured in the sensor policy or via `falconctl` / registry settings
- SSL/TLS inspection must **exclude** CrowdStrike cloud destinations — Falcon uses certificate pinning; MITM inspection breaks the connection entirely
- If the proxy is misconfigured: sensor appears installed but never checks in, telemetry stops flowing, prevention capability degrades silently

**What breaks specifically:**
- No telemetry → no cloud detections (only local ML fires)
- RTR sessions fail
- Policy updates stop reaching the sensor
- Host goes dark in console but appears healthy on the endpoint

**Probe follow-up:** *Your security team wants Zscaler to inspect all Falcon cloud traffic for DLP purposes. What's your recommendation?*

**Answer:** Recommend creating a Zscaler bypass (SSL inspection exclusion) for CrowdStrike's cloud endpoints. Zscaler cannot inspect Falcon's encrypted channel without breaking it. The correct DLP approach is to trust Falcon's own data protection capabilities and CrowdStrike's SOC 2 compliance, not attempt to MITM the sensor-cloud channel.

---

## Section 2: Sensor Deployment & Operations

### Q5. A host is not appearing in the Falcon console. How would you troubleshoot it?

*Practical admin experience test.*

**Structured troubleshooting flow:**

```
Step 1 → Is the sensor installed?
         Windows: Services.msc → CrowdStrike Falcon Sensor
         Linux:   systemctl status falcon-sensor
         macOS:   sudo /Applications/Falcon.app/... --version

Step 2 → Is the sensor service running?
         Windows: sc query csagent
         Linux:   systemctl is-active falcon-sensor

Step 3 → Is the CID correct?
         Wrong CID = sensor installs but registers to wrong tenant

Step 4 → Network/proxy/firewall issue?
         Test connectivity: curl https://ts01-b.cloudsink.net
         Check proxy configuration in policy

Step 5 → Sensor version supported?
         Very old sensors may be EOL and rejected by cloud

Step 6 → Host grouping/policy assignment?
         Host may be in wrong group or ungrouped

Step 7 → Check sensor logs
         Windows: C:\Windows\System32\drivers\CrowdStrike\
         Linux:   /var/log/falcond.log

Step 8 → Verify RTR connectivity if sensor appears but is unresponsive
```

**Bonus signals:** Mentioning `falconctl`, sensor diagnostics commands, proxy configuration flags, or checking the Customer ID (CID) hash match.

---

### Q6. Walk me through deploying Falcon sensors to 5,000 endpoints across Windows, macOS, and Linux. What's your rollout strategy?

**Phase 1 — Audit mode pilot (100–200 hosts)**
- Deploy with prevention policies in Detect-only
- Validate telemetry is flowing, no connectivity issues
- Identify proxy/network edge cases before scaling

**Phase 2 — Prevention enable (controlled rollout)**
- Enable ML prevention first (lowest false positive risk)
- Watch for business-impacting blocks
- Create exclusions only where justified with documented tickets

**Phase 3 — Full prevention + IOAs**
- Enable behavioral detections
- Custom IOAs for org-specific threats
- Monitor detection volume for noise/gap analysis

**Cross-platform specifics:**
- Windows: MSI/EXE via SCCM/Intune/GPO + Installation Token
- Linux: RPM/DEB packages; handle kernel module compatibility for RFM risk
- macOS: PKG deployment; requires Privacy Preferences Policy Control (PPPC) profiles for full disk access + system extension approval

**Probe follow-up:** *During rollout, 3% of sensors deployed but never checked into the console. You can't RDP to those machines. How do you diagnose at scale?*

**Answer:** Query the console for hosts with "never seen" status matching your deployment window. Cross-reference against CMDB/deployment tool logs to confirm the package was pushed. Use a secondary channel (SCCM remote command, cloud agent, or jump host) to run `falconctl getstatus` or check the service state remotely. Look for CID mismatch, proxy misconfiguration, or OS-level block of the kernel module.

---

### Q7. A sensor hasn't checked in for 48 hours on a high-value finance server. While it was dark, a detection came in on a neighbouring host for lateral movement toward it. What do you do?

**This is an incident response judgment call, not just a sensor health ticket.**

1. **Escalate immediately** — dark sensor + lateral movement toward it = potentially compromised host
2. **Attempt network containment** via console despite sensor dark status — if sensor has any connectivity, containment may still work
3. **Pivot on the neighbouring host's detection** — what process initiated the lateral movement? What credential was used? What was the destination?
4. **Review directory service authentication logs** for the finance server during the dark period
5. **Coordinate with network team** for VLAN isolation if Falcon containment can't reach the host
6. **Treat the 48-hour dark period as dwell time** — scope accordingly, assume the worst until proven otherwise

---

### Q8. What is Reduced Functionality Mode (RFM) and how do you handle it?

**RFM = sensor installed but operating with degraded protection.**

| Platform | Common RFM Causes | Remediation |
|---|---|---|
| **Linux** | Kernel version not supported; missing kernel headers; unsupported distro | Update sensor or kernel to compatible version |
| **Windows** | Driver signing issues; OS at EOL; conflict with another security product | Check driver conflicts; verify OS support |
| **macOS** | System extension not approved; PPPC profile not deployed; SIP interference | Push PPPC profile via MDM; verify extension approval |

**Monitoring:** Falcon console → Sensor Management → filter by RFM status. Alert on RFM hosts in critical host groups — a host in RFM is a coverage gap.

---

## Section 3: Prevention Policy Management

### Q9. How do Falcon prevention policies work, and how would you tune them?

**Policy hierarchy:**

```
Tenant (CID)
  └── Host Groups (dynamic or static membership rules)
        └── Prevention Policy assigned to group
              ├── ML Prevention (on-sensor AI scoring)
              ├── Behavioral IOA rules
              ├── Sensor Visibility settings
              └── Device Control settings
```

**Policy precedence:** When a host belongs to multiple groups with different policies, Falcon applies the policy from the *highest-priority* group (numerically lowest priority number = highest precedence).

**Tuning approach:**
1. Start in **Detect-only** — never go straight to Prevent in production
2. Monitor and triage false positives for 2–4 weeks
3. Create **scoped exclusions** — never tenant-wide unless absolutely necessary
4. Document every exclusion: business justification, ticket number, scope, review date
5. Audit exclusions periodically — orphaned exclusions silently erode your security posture

**What scares interviewers:** "I'd just whitelist it." Exclusions without scope or review cycles are security debt that accumulates invisibly.

---

### Q10. Your CISO wants everything in "Prevent" mode but infrastructure is screaming it's breaking production. How do you manage that conflict?

*This tests security judgment and stakeholder management.*

1. **Get specifics** — require ticket numbers and affected process details. Vague complaints aren't actionable.
2. **Validate each block** — is this actually Falcon? Many "Falcon is blocking it" complaints turn out to be GPO, WDAC, or AppLocker.
3. **Create scoped exclusions** for legitimate tools — specific hash + specific host group, not tenant-wide
4. **Document the risk** — if leadership wants to exclude something genuinely risky, document that decision and get sign-off in writing
5. **Phase the rollout** — move business-critical systems to Prevent last, after a Detect-only validation period

The CISO's goal (full prevention) is correct. The path is a structured phased rollout — not a binary choice.

---

### Q11. A developer says Falcon is blocking a legitimate internal tool. How do you handle it without lowering your overall prevention posture?

1. **Validate the block** — pull the detection, examine the process tree and the specific IOA or ML score that triggered
2. **Assess the tool** — is it internally developed? Signed? What does it actually do?
3. **Determine the right exclusion type:**
   - Hash-based (ML exclusion) for specific known-good executables
   - IOA exclusion for behavioral patterns that are legitimate for this specific tool
4. **Scope tightly** — apply to the developer host group only, not tenant-wide
5. **Document** — ticket, scope, justification, reviewer, 90-day review date
6. **Monitor** — confirm the tool runs cleanly and no new related detections appear

**What not to do:** Exclude the entire parent directory. Disable ML prevention for the whole tenant. Create a wildcard exclusion on the process name.

---

### Q12. Six months later you're reviewing exclusions and find 47 with no ticket, no scope, and some are tenant-wide. What's your remediation plan?

1. **Export the full exclusion list** — document current state before touching anything
2. **Categorize by risk:** tenant-wide exclusions first (highest risk), then broad path exclusions
3. **Identify ownership** — who created each? Cross-reference ITSM if possible
4. **For each exclusion:**
   - Can it be scoped to a specific host group? → Scope it
   - Is the excluded process/path still in use? → Verify with asset owners
   - No owner, no justification, no business need → Schedule for removal
5. **Test removals in Detect-only first** — enable as a detection before fully removing to see if it fires
6. **Implement governance going forward:** mandatory ticket numbers in exclusion notes, 90-day review cycle, peer approval for any tenant-wide exclusion

**The finding itself should be reported to leadership** as a documented security gap.

---

### Q13. What is the "three-phase" approach to deploying prevention policies?

**Phase 1 — Visibility only (Detect)**
- All detections active, zero prevention
- Goal: understand your environment's noise baseline
- Duration: 2–4 weeks minimum

**Phase 2 — Cautious Prevention**
- Enable ML prevention at medium sensitivity
- Leave behavioral IOAs in Detect
- Address false positives with scoped exclusions

**Phase 3 — Full Prevention**
- Enable all prevention including custom IOAs
- Enable Sensor Tampering Protection
- Ongoing exclusion governance and review cadence

This approach prevents the "Falcon broke production" scenario — every impactful block has already been seen and addressed as a detection first.

---

## Section 4: Detection Investigation

### Q14. Walk me through how you would investigate a Falcon detection end-to-end

**Structured investigation flow:**

```
1. Detection metadata
   → Severity, tactic, technique (MITRE ATT&CK mapping)
   → Timestamp, host name, user context

2. Process Tree
   → Parent process — was this a legitimate spawner?
   → Child processes — what did it create?
   → Command line arguments — encoded? Suspicious flags?

3. User context
   → Standard user or privileged account?
   → Is this account expected on this host?
   → Recent password changes or MFA anomalies?

4. Network activity
   → Outbound connections from the process?
   → Known-bad IPs or newly registered domains?
   → DNS queries from the host around detection time?

5. Persistence mechanisms
   → New scheduled tasks?
   → Registry run keys modified?
   → New services created?

6. Scope
   → Same hash/command seen on other hosts?
   → Same user account active elsewhere?
   → Lateral movement indicators on adjacent hosts?

7. Decision
   → True positive → contain, eradicate, recover
   → False positive → tune with scoped exclusion + document
```

**Bonus:** Mapping each finding to MITRE ATT&CK technique IDs builds the case narrative and guides hunting for related techniques in the same tactic cluster.

---

### Q15. The suspicious PowerShell ran under a service account used by 200 other hosts. How do you determine if this is isolated or a campaign?

1. **Pivot on the service account** — search LogScale/Event Search for this account's authentication activity across all hosts in the past 24–72 hours
2. **Search for the same command** — hash or substring search the PowerShell command across fleet telemetry
3. **Look for timing correlation** — did similar detections fire on other hosts within the same window?
4. **Check the account's behavior baseline** — what hosts does it normally authenticate to? What processes normally run under it?
5. **Pivot on network indicators** — if there's an outbound connection, search for other hosts connecting to the same destination IP

**If results show activity on multiple hosts → campaign.** Escalate, scope all affected hosts, coordinate simultaneous containment.

**If truly isolated → investigate why** this one host had anomalous behavior from that service account (cached credential? token theft? misconfigured service?).

---

### Q16. How would you use Falcon's Event Search / LogScale to hunt for credential dumping across your fleet?

**Sample hunting logic:**

```
# LSASS access by non-system processes
event_simpleName=ProcessRollup2
| TargetImageFileName=/lsass\.exe/i
| ImageFileName!=/System32/
| groupBy([ComputerName, ImageFileName, UserName])

# SAM database access (local credential store)
event_simpleName=RawReadNotification
| TargetFileName=/SAM$/i
| groupBy([ComputerName, ImageFileName])

# Known credential dump tool patterns
event_simpleName=ProcessRollup2
| CommandLine=/(sekurlsa|logonpasswords|mimikatz|procdump.*lsass)/i

# NTDS.dit access (Domain Controller credential database)
event_simpleName=RawReadNotification
| TargetFileName=/ntds\.dit/i
```

**Probe follow-up:** *Hunt returns zero results but threat intel says the adversary uses a custom reflective DLL loader that never touches disk. How do you adjust?*

**Answer:** Shift from artifact-based to behavior-based hunting:
- Hunt for anomalous memory allocation: private executable memory regions in unexpected processes
- Look for processes with network connections that have no corresponding file on disk
- Hunt for remote thread injection: threads created in legitimate processes by a different parent
- Look for processes with unusual parent-child relationships with blank command lines (reflective loaders often self-blank)

---

## Section 5: Real Time Response (RTR) & Incident Response

### Q17. How does RTR work, and what are its operational risks?

**How it works:** RTR provides a remote shell to endpoints over the *same* persistent Falcon cloud channel — not a separate network connection. Works on **network-contained hosts** (cloud channel remains open during isolation).

**RTR Role Risk Matrix:**

| RTR Role | Capabilities | Risk Level | Who Should Have It |
|---|---|---|---|
| **RTR Analyst** | Read-only: get file, list processes, registry query | Low | All analysts |
| **RTR Active Responder** | Read + write: put/run file, kill process | Medium | Experienced IR analysts |
| **RTR Administrator** | Full: run any script, unrestricted | High | Senior IR only, with approval workflow |

**The critical risk of RTR Administrator:** It is effectively unrestricted remote code execution with SYSTEM privileges on every enrolled endpoint. A compromised account with RTR Admin is a full domain-equivalent compromise through a different path. RBAC must be tightly controlled and sessions audit-logged.

---

### Q18. Describe how you'd use RTR to collect forensic artifacts from a compromised host

```bash
# 1. Establish RTR session via Falcon console → host → RTR

# 2. Active processes
ps

# 3. Network state — active connections, listening ports
netstat -ano

# 4. Persistence locations
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
schtasks /query /fo LIST /v

# 5. Suspicious staging locations
ls C:\Windows\Temp\
ls C:\Users\*\AppData\Roaming\
ls C:\PerfLogs\

# 6. Pull suspicious files to Falcon cloud
get C:\Windows\Temp\suspicious.exe

# 7. Event logs
get C:\Windows\System32\winevt\Logs\Security.evtx
```

**Probe follow-up:** *RTR session keeps dropping every 2–3 minutes. Host is critically compromised. What's your fallback?*

**Answer:**
1. Write a single RTR script that does all collection in one execution — don't rely on interactive session stability
2. Use bulk script execution to push a collection script that writes artifacts locally
3. Coordinate with on-site IT for physical/out-of-band access
4. If it's a VM, take a hypervisor-level snapshot — captures full memory independent of Falcon connectivity
5. Document the drops as potential indicators of active attacker interference

---

### Q19. You contain a host. Ten minutes later the business calls — it's a payment processing server doing $2M/hour. Leadership wants it uncontained immediately. What do you do?

**This is a governance decision, not a technical one.**

1. **Do not uncontain without authorization** — document the request in writing immediately
2. **Brief leadership clearly** — what specifically was detected, what the attacker can do if uncontained, what the risk is
3. **Offer alternatives** — can payment processing failover to a backup system while this host is investigated?
4. **If leadership formally accepts the risk and directs you to uncontain:** document the decision in writing, increase monitoring on the host, have RTR ready, set a strict re-containment tripwire on any new detection
5. **Your job:** make the risk clear, not override the business decision — but also never silently comply without documentation

---

## Section 6: Advanced Administration

### Q20. What are Custom IOAs, and when would you create one?

*This separates admins from advanced defenders.*

**Custom IOAs** are behavioral detection rules written by the defender for org-specific threats, using regex-based pattern matching against process, network, registry, and file events.

**When to create them:**
- A specific LOLBin being abused in your environment (e.g., `certutil.exe` downloading from internal infrastructure)
- RMM tool (AnyDesk, TeamViewer) running outside of approved maintenance windows
- PowerShell execution from user directories that should never run scripts
- Custom attacker TTP identified in a purple team exercise

**Rule construction principles:**
- Be specific — overly broad rules create noise and analyst fatigue
- Test in Detect-only before enabling Prevention
- Use process path + command line regex combinations for precision
- Scope to the relevant host group, not tenant-wide
- Document the threat scenario the rule was written to address

---

### Q21. RBAC vs. Fine-Grained Access (FGA) — explain the difference and when you'd use FGA

**RBAC:** Assigns a role that defines *what actions* a user can perform across the **entire tenant**.

**FGA:** A layer *on top of* RBAC that restricts *which hosts* a user can see and act on, even within their role's permissions.

**Example use case — MSSP:** A managed service provider supports 5 customers in the same Falcon tenant. Each customer's SOC analyst has the same Falcon Analyst role — but FGA restricts each analyst's host scope to their own customer's endpoints only.

**Example use case — Regional SOC:** EU analysts should only query and respond to EU hosts. FGA enforces this without requiring separate tenants.

---

### Q22. An analyst cannot see the "Network Containment" button on a critical detection. What's happening and how do you fix it?

**Admin diagnosis:**
- The analyst likely has **Falcon Analyst** or **Help Desk Analyst** role, which lacks containment permissions
- Check: User Management → the analyst's role assignments
- Fix: Assign **Falcon Administrator**, **Falcon Analyst - Remediation**, or a custom role that includes the Network Contain permission

**Analyst decision question:** *Under what conditions would you contain vs. just monitor the process tree?*

- **Contain when:** Active lateral movement, ransomware indicators, confirmed C2 with active attacker control, privileged account compromise
- **Monitor when:** Detection is suspicious but not confirmed, scope is not yet established, host is mission-critical and business impact of isolation is high

---

### Q23. Managing Fusion SOAR — design a workflow to auto-contain on a critical detection

**Workflow design:**

```
Trigger: Detection severity = Critical
    ↓
Condition: Detection confidence = High
    ↓
Action 1: Slack notification → #soc-critical
          (Host, severity, detection summary, console deep link)
    ↓
Action 2: Create ServiceNow incident ticket
    ↓
Action 3: Network Containment → affected host
          (Requires RTR Active Responder or Admin role on workflow)
    ↓
Action 4: PagerDuty alert → on-call analyst
    ↓
Logging: All actions recorded to Fusion Execution History
```

**Analyst task — evaluating execution history:**
Review Execution History to confirm the workflow fired correctly, the containment succeeded, and it didn't trigger on a false positive. If it fired on a false positive: tune the detection policy at source, add a condition to the workflow (e.g., require specific MITRE tactic), and review the business impact of the false containment.

**Governance note:** For Tier 0 / critical servers, add a manual approval gate before the containment action fires.

---

### Q24. Sensor Update Policies — why avoid "Auto" for production, and what is the N-2 rule?

**Why avoid "Auto":** The Auto version installs the latest sensor immediately on release. In production, new sensor versions may:
- Change kernel module behavior (RFM risk on Linux)
- Interact differently with other security products
- Require system extension re-approval on macOS

**The N-2 rule:** Pin production systems to the sensor version 2 releases behind the latest (N-2). This version has had real-world validation through 2 additional release cycles.

**Recommended policy structure:**

```
Pilot group       → N (latest)     Canary — catch issues first
Staging group     → N-1            Validated once
Production group  → N-2 (pinned)   Manually promoted quarterly
```

---

### Q25. Installation Tokens — when and how to implement them

**Purpose:** Prevent unauthorized sensor installation or removal. A valid token is required at install time.

**When to enable:**
- Insider threat environments
- Regulated industries requiring tamper evidence
- Environments where you need an audit trail of who authorized each deployment

**Impact on deployment scripts:**
- Windows: Add `/INSTALLTOKEN=<token>` to the MSI install command
- macOS: Pass token in the configuration profile
- Linux: Include `--aph=<token>` in the install command

**Token management:** Use time-limited tokens for bulk deployments. Rotate after each deployment phase. Never embed long-lived tokens in shared scripts without access controls on the script repository.

---

### Q26. What is the impact if Uninstall and Maintenance Protection is enabled and the sensor needs to be removed from an offline Windows host?

**The problem:** Uninstall protection requires a maintenance token to uninstall. If the host is offline, you cannot retrieve the per-host token from the console remotely.

**Resolution options:**
1. Bring the host online temporarily to pull the maintenance token from the Falcon console (Host Management → host → Maintenance Token)
2. If the host cannot come online: use the bulk maintenance token (if configured) — a static token that works across the tenant
3. Physical access + boot into safe mode — sensor runs in limited mode and may allow uninstall
4. Image replacement (nuclear option) — wipe and redeploy if the host cannot be recovered via any of the above

**Prevention:** Always configure a bulk maintenance token as a break-glass credential and store it in your PAM vault.

---

## Section 7: Architecture & Integration

### Q27. How would you integrate Falcon with Splunk or Microsoft Sentinel? What data streams would you prioritize?

**Integration methods:**
- **Falcon Data Replicator (FDR):** S3-based bulk telemetry export — all raw events streamed to S3, ingested by Splunk/Sentinel
- **Streaming API (Event Streams):** Real-time detection and event stream via OAuth2 API
- **Pre-built connectors:** Splunk TA for CrowdStrike, Sentinel Data Connector

**Data stream priority:**

| Priority | Stream | Reason |
|---|---|---|
| 1 | Detections + alerts | Immediate SOC action |
| 2 | Authentication events | Account compromise detection |
| 3 | Process execution (Tier 0 hosts) | High-fidelity threat hunting |
| 4 | Network events (Tier 0 hosts) | Lateral movement correlation |
| 5 | Full telemetry (all hosts) | Historical hunting — high volume, ingest carefully |

**Probe follow-up:** *Three months after integration, SOC says Falcon alerts are noisy and they're ignoring them. What went wrong?*

Common causes and fixes:

| Root Cause | Fix |
|---|---|
| All severities forwarded to one queue | Filter to Critical/High only for primary queue |
| No correlation rules written | Build SIEM rules that enrich Falcon detections with identity + network context |
| Detection policies not tuned at source | Reduce false positives in Falcon before they reach SIEM |
| No response playbooks | Build runbooks — analysts ignoring alerts often means they don't know what to do with them |
| No alert routing by severity | Implement severity-based routing and escalation paths |

---

### Q28. Explain Falcon Flight Control — can a Child CID admin override a global exclusion?

**Flight Control** is CrowdStrike's multi-tenant management layer for MSSPs and large enterprises.

- Parent CID can push policies, exclusions, and configurations to Child CIDs
- Child CID admins can view inherited configurations but **cannot modify or override them**
- Child CID admins **cannot** override global exclusions set at the Parent level
- Child CIDs can create their own local policies that apply on top of (or instead of) inherited ones, depending on how the Parent configures inheritance

**Use cases:** MSSP multi-tenant management, business unit isolation, geographic data residency separation.

---

## Section 8: Senior / Advanced Probe Questions

*Asked for Detection Engineering, Threat Hunting, and Lead SOC roles.*

---

### How would you hunt for PowerShell abuse across the fleet?

**Hunting angles:**

```
1. Encoded commands
   CommandLine contains "-EncodedCommand" or "-enc"

2. Download cradles
   CommandLine contains "DownloadString", "WebClient", "IEX"

3. AMSI bypass attempts
   Known bypass strings in command line

4. Non-standard parent processes
   PowerShell spawned by mshta.exe, wscript.exe, winword.exe, outlook.exe

5. Script block logging anomalies
   Suspicious content in PowerShell script block events

6. Outbound network from powershell.exe
   Any external connections from a process that shouldn't be initiating them
```

---

### How would attackers try to evade Falcon, and why does it still catch them?

| Evasion Technique | How It Works | Why Falcon Still Detects It |
|---|---|---|
| Hash modification | Change one byte to change the hash | IOAs are behavior-based, not hash-based |
| Signed malware | Use legitimate code-signing certificate | Post-execution behavior still triggers IOAs |
| LOLBin abuse | Use built-in Windows tools | Anomalous parent-child relationship IOAs |
| Kernel-level rootkit | Operate below user space | Falcon sensor operates at kernel level too |
| Sensor tampering | Attempt to stop or uninstall Falcon | Sensor Tampering Protection + cloud-side detection |
| Memory-only / fileless | Never write to disk | Behavioral memory allocation IOAs |

**What no evasion technique fully defeats:** The kernel-level telemetry stream itself. Attackers can try to interfere with the sensor — but that interference generates its own telemetry.

---

### How do you measure EDR effectiveness?

| Metric | What It Measures |
|---|---|
| Mean Time to Detect (MTTD) | How quickly is attacker activity flagged? |
| Mean Time to Respond (MTTR) | How quickly does the team act on detections? |
| ATT&CK coverage heatmap | Which MITRE techniques have detection coverage? |
| False positive rate | What % of detections require no action? |
| Sensor deployment coverage | % of endpoints with healthy, active sensors |
| RFM host count | How many hosts are running in degraded mode? |
| Exclusion growth rate | Is the exclusion list growing without governance? |

**The 1-10-60 benchmark** — CrowdStrike's own operational standard:
- **1 minute:** Detect the intrusion
- **10 minutes:** Understand the full scope
- **60 minutes:** Contain and remediate

Measuring your team against this gives a concrete, externally validated operational baseline.

---

### Identity-based threat response — credential access detection

**Analyst task:** You see a "Credential Access" detection. How do you use Identity Protection insights to determine if the account was compromised via an unmanaged service provider?

1. In Falcon Identity Protection, pull the full authentication history for the flagged account
2. Look for authentications from IP ranges associated with the service provider — compare against known provider IP space
3. Check for impossible travel: the account authenticating from both internal corporate IPs and external IPs within a short window
4. Look for token reuse: the same session token appearing from different source IPs
5. Review service provider's access logs if available — correlate their records with the flagged authentication timestamps

**Admin task:** How do you configure a Policy Rule to force MFA for that specific user group until the incident is resolved?

- In Falcon Identity Protection → Policy Rules → create a new rule scoped to the affected user group
- Set condition: any authentication attempt
- Action: require MFA step-up
- Apply to the specific user group only — do not apply tenant-wide
- Set an expiry or review date on the rule and remove it once the incident is resolved and credentials have been reset

---

## Quick Reference: What to Prepare

```
Deployment stories:
  → A sensor rollout that hit a problem — how you diagnosed it
  → A proxy/connectivity issue and how you resolved it

Policy stories:
  → A false positive you handled without over-excluding
  → A prevention policy tuning decision that had business impact

Detection stories:
  → A detection you investigated end-to-end (process tree → root cause)
  → A hunt you ran and what you found

Incident stories:
  → A containment decision — when you isolated and why
  → A time you had to push back on premature eradication

Integration stories:
  → Falcon + Splunk data pipeline work
  → A custom IOA or Fusion SOAR workflow you built
```

**The difference between "tool-trained" and "experienced":**
You can explain the *why* behind every action — not just the *what*.

---

*Tags: `crowdstrike` `falcon` `interview` `EDR` `SOC` `blue-team` `detection-engineering` `RBAC` `RTR` `IOA` `threat-hunting` `Fusion` `SOAR`*
