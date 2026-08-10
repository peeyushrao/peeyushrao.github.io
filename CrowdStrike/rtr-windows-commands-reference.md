# RTR (Real Time Response) — Windows Command Reference

RTR gives you a live, remote shell-like session on any Falcon-covered endpoint, without needing RDP, VPN, or local access. It's built for **triage, live investigation, evidence collection, and remediation** — everything you'd normally need physical or remote-desktop access for, but audited, session-recorded, and scoped by RBAC role.

RTR commands fall into two buckets:
- **Native RTR commands** — built into the RTR shell itself, work the same regardless of OS specifics, sandboxed.
- **`runscript`** — drops you into real PowerShell (or cmd) execution on the host, for anything native commands can't do.

---

## 1. Session & Help

| Command | Purpose |
|---|---|
| `help` | Lists all available commands for your RBAC role |
| `help <command>` | Detailed usage/syntax for a specific command |
| `history` | Shows commands run in the current session |
| `exit` | Ends the RTR session |

---

## 2. Process & System Visibility

| Command | Purpose |
|---|---|
| `ps` | Lists running processes (PID, name, path, user context) |
| `env` | Dumps environment variables |
| `runscript -Raw=\`\`\`Get-CimInstance Win32_PerfFormattedData_PerfProc_Process\`\`\`` | Task-Manager-style live CPU % per process, normalized per core (fastest, most accurate live read) |
| `runscript -Raw=\`\`\`Get-Process \| Sort CPU -Descending\`\`\`` | Cumulative CPU-seconds per process since launch (good for "who's been busy over time," not "who's busy now") |
| `runscript -Raw=\`\`\`Get-MpComputerStatus\`\`\`` | Defender AV engine/real-time-protection state (active/passive/disabled) — useful for AV-conflict triage |
| `runscript -Raw=\`\`\`Get-Service -Name WinDefend\`\`\`` | Confirms whether the Defender service exists/is running at all |

**Why this matters:** `ps` is your first move on any "what's happening on this box right now" question — malware triage, resource investigation, or confirming a process actually launched.

---

## 3. Network

| Command | Purpose |
|---|---|
| `netstat` | Active connections, listening ports — first stop for C2/beaconing or unexpected outbound connections |
| `ipconfig` | IP config, adapters, DNS servers |
| `runscript -Raw=\`\`\`Get-NetTCPConnection \| Where State -eq Established\`\`\`` | Structured, filterable version of netstat — pipe/sort/filter by remote IP, port, PID |
| `runscript -Raw=\`\`\`Resolve-DnsName <host>\`\`\`` | Live DNS resolution check from the endpoint's own vantage point |

**Why this matters:** confirms lateral movement, C2 beaconing, or unexpected listener ports directly from the host, rather than inferring from firewall/proxy logs alone.

---

## 4. File System & Evidence Collection

| Command | Purpose |
|---|---|
| `ls` / `cd` | Browse the filesystem interactively |
| `cat` | Read a file's contents inline |
| `get <file>` | **Pulls a file off the endpoint** to the Falcon console for download/offline analysis — core forensic collection command |
| `put <file>` | Pushes a file (e.g. a diagnostic tool or remediation script) onto the endpoint |
| `filehash <file>` | SHA256 of a file — quick IOC match against threat intel without needing to exfil the whole file |
| `zip` / `unzip` | Package/unpack files for bulk `get`/`put` |
| `mkdir` / `rm` | Basic filesystem manipulation for staging or cleanup |

**Why this matters:** this is how you collect evidence (a suspicious binary, a config file, a log) for offline analysis without ever touching the box yourself, or push a fix/tool down at scale.

---

## 5. Registry

| Command | Purpose |
|---|---|
| `reg query <key>` | Read a registry key/value — persistence checks, config verification, malware artifact hunting |
| `reg set` | Write a registry value (remediation, config push) |
| `reg delete` | Remove a key/value (remediation) |

**Why this matters:** most persistence mechanisms (Run keys, services, scheduled task registration) live in the registry — this is a standard first stop in an intrusion investigation.

---

## 6. Event Logs

| Command | Purpose |
|---|---|
| `eventlog list` | Lists available Windows event log channels |
| `eventlog view <log>` | Views entries from a specific log (Security, System, Application, etc.) |
| `runscript -Raw=\`\`\`Get-WinEvent -LogName Security -MaxEvents 50\`\`\`` | More flexible/filterable pull (by ID, time range, keyword) than the native `eventlog view` |

**Why this matters:** correlate local Windows event log evidence (logon events, service changes, scheduled task creation) against what Falcon's own telemetry shows for the same window.

---

## 7. Diagnostics & Sensor Health

| Command | Purpose |
|---|---|
| `cswindiag` | Runs CrowdStrike's built-in Windows diagnostic bundle — sensor health, config, channel files, connectivity — packages it for `get` |
| `runscript -Raw=\`\`\`Get-ScheduledTask \| Where State -eq Ready\`\`\`` | Lists active scheduled tasks — useful for tracking down cron-style process-churn sources |
| `runscript -Raw=\`\`\`Get-CimInstance Win32_Service \| Where State -eq Running\`\`\`` | Full running-service inventory beyond just `ps` |

**Why this matters:** `cswindiag` is your go-to when CrowdStrike Support asks for sensor diagnostics, or when you need to rule the sensor itself in/out of an issue (like the Falcon-vs-workload CPU question from earlier).

---

## 8. Process/Script Control (Containment & Remediation)

| Command | Purpose |
|---|---|
| `kill <pid>` | Terminate a running process |
| `runscript -CloudFile="<name>"` | Runs a pre-approved script from your org's Script Manager (works even if raw scripting is disabled by policy) |
| `runscript -Raw=\`\`\`...\`\`\`` | Ad-hoc PowerShell — most flexible option, requires elevated RTR role and raw-scripting enabled at the CID/policy level |
| `update history` / `restart` / `shutdown` | Host-level control actions (used carefully — session-recorded and auditable) |

**Why this matters:** RTR isn't just read-only investigation — it's also how you kill a malicious process, remediate a registry persistence key, or push a fix, all without needing hands-on-keyboard access or the endpoint user's cooperation.

---

## Practical notes from what we've hit so far in this conversation

- **`-Raw` requires the elevated RTR role** (Real Time Responder – Administrator or similar) and requires raw scripting to be enabled in Response Policies for that CID — if it's disabled org-wide, use `-CloudFile` with pre-approved Script Manager scripts instead.
- **Object output needs explicit formatting.** Piping PowerShell objects straight out (`Get-Process | Sort CPU`) without `Format-Table -AutoSize | Out-String -Width 200` at the end will print .NET type names instead of readable data in the RTR console.
- **`Win32_PerfFormattedData_PerfProc_Process` > raw `Get-Counter`** for live CPU reads — it's pre-normalized per logical core (matches Task Manager's math) and doesn't need the two-sample `-SampleInterval` workaround that raw `% Processor Time` counters require for accuracy.
- **Cumulative vs instantaneous matters.** `Get-Process`'s `CPU` column is total CPU-seconds since launch — great for "who's used the most CPU historically," useless for "what's spiking right now." Use the CIM/Counter-based commands for live snapshots.
