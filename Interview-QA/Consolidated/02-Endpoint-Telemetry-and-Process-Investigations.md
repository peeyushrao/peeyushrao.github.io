# Endpoint Telemetry and Process Investigations

Interview questions and answers, grouped by topic. Each source section retains its original content.

---

**Source: 10.md**

## What is the difference between endpoint and network telemetry?

The primary difference between **endpoint telemetry** and **network telemetry** lies in the **source of data** and the **type of visibility** they provide:

- **Endpoint telemetry** captures what is happening *inside* a specific device.
- **Network telemetry** captures how devices *communicate with each other*.

---

## Endpoint Telemetry

Endpoint telemetry is sourced directly from individual devices such as workstations, servers, and mobile devices. It focuses on the internal state and activities of the host operating system.

### Key Data Points
- Process executions
- File creation, modification, and deletion
- Registry changes
- Local user and privilege activity

### Collection Methods
- Operating system logs (e.g., Windows Event Logs)
- Native system utilities (e.g., `tasklist`, `netstat`)
- Lightweight endpoint agents

### Forensic Value
Endpoint telemetry provides deep, high‑fidelity visibility into the **"who"** and **"how"** of a compromise. For example, it can reveal a malicious macro running inside a Word process or a PowerShell script launched by a specific user.

---

## Network Telemetry

Network telemetry is sourced from the infrastructure that connects systems, such as routers, switches, firewalls, and network sensors. It focuses on the **conversations occurring on the wire**.

### Key Data Points
- Network flow data (source/destination IPs and ports)
- Packet metadata
- Protocol‑specific details (e.g., HTTP headers, DNS queries, SMB activity)

### Collection Methods
- Network devices using NetFlow or IPFIX
- Network Security Monitoring (NSM) tools
- Traffic capture via TAPs or SPAN ports

### Forensic Value
Network telemetry is critical for:
- Detecting lateral movement
- Identifying command‑and‑control (C2) communications
- Spotting data exfiltration attempts

---

## Interview Question

**Question:**
> What is the difference between endpoint and network telemetry, and why do we need both?

**Answer:**
> Endpoint telemetry provides an internal view of a system’s behavior, while network telemetry provides an external view of its communications. Endpoint telemetry shows the ground truth of execution—exactly which process ran, under which user context, and what actions occurred before and after. However, it can be obscured by advanced malware such as rootkits. Network telemetry compensates for this by observing traffic on the wire, which is much harder for attackers to hide. It allows detection of lateral movement, C2 activity, and data exfiltration. Using both provides defense in depth: network telemetry may reveal suspicious connections, while endpoint telemetry proves which process initiated them.

---

## Simple Summary

- **Endpoint telemetry** shows *what happened on the host* (processes, users, files, memory).
- **Network telemetry** shows *how systems communicate* (connections, protocols, destinations).

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, endpoint telemetry is treated as the **authoritative source of truth**, with network telemetry used to enrich and validate findings.

### Endpoint Telemetry (Falcon Sensor)

Collected directly on the host:
- Process creation and termination
- Command‑line arguments
- Parent/child process relationships
- DLL loads
- Memory access (e.g., LSASS access)
- File writes and registry modifications
- User context and privilege level

**Best answers:**
- What executed?
- Who executed it?
- How did it start?
- What happened before and after?

This is where **malicious intent is proven**.

---

### Network Telemetry (Falcon XDR / Integrations)

Observed in transit:
- Inbound and outbound connections
- IPs, domains, ports, and protocols
- Beaconing patterns
- Lateral movement paths

**Best answers:**
- Where did it connect?
- Is data leaving the environment?
- Is there C2 or lateral movement?

Network telemetry confirms **reach and impact**, but not intent on its own.

---

## Why CrowdStrike Prioritizes Endpoint Telemetry

- Attackers can:
  - Encrypt network traffic
  - Use trusted cloud services
  - Blend into allowed network flows
- Attackers **cannot hide execution on the endpoint**

In Falcon investigations:
> **Network telemetry adds context — endpoint telemetry proves compromise.**



---

**Source: 11.md**

## Why is baselining normal behavior important?

Baselining normal behavior means documenting the **standard operating state** of an environment so it can be used as a reliable point of comparison to detect **malicious or anomalous activity**. Without a baseline, analysts have no objective way to determine whether an observed behavior is expected or suspicious.

A strong baseline turns detection from guesswork into evidence‑based analysis.

---

## What Does a Baseline Represent?

A baseline captures how systems, users, and networks behave **when nothing is wrong**, including:
- Which processes normally run
- Which ports and protocols are typically used
- How much network traffic is expected
- How users usually authenticate and access resources

Any meaningful deviation from this established norm becomes a candidate for investigation.

---

## 1. Essential Data Categories for Baselining

To build a comprehensive baseline, analysts must collect data across multiple dimensions.

### Process and Service Activity
- Programs and services that normally run on each system
- Expected disk locations of binaries
- Typical parent–child process relationships

This helps identify suspicious executions such as renamed binaries, LOLBins used out of context, or abnormal process trees.

### Network Metadata
- Standard open and listening ports
- Normal traffic volumes and patterns
- Commonly used protocols
- Typical user‑agent strings

This enables detection of unusual connections, beaconing behavior, or unexpected protocol usage.

### User and Entity Behavior
- Normal login times and frequency
- Typical geographic access locations
- Resources and systems a user commonly accesses

This is critical for identifying account compromise, insider threats, or abnormal privilege use.

### System Configuration
- "Gold builds" for servers and endpoints
- Default configurations before third‑party software or user interaction

These baselines allow detection of configuration drift, persistence mechanisms, or unauthorized changes.

---

## 2. Methodologies for Building Baselines

Baselines are established using a combination of **documentation, automation, and analytics**.

### Automated Collection
- Periodic capture of system state (e.g., processes, services, network connections)
- Use of scripts or built‑in OS utilities
- Storage of snapshots as text‑based or structured records for comparison

This provides a historical "known‑good" reference.

### Behavioral Analytics (UEBA)
- Ingestion of endpoint and network logs
- Automatic learning of normal patterns over time
- Detection of deviations using statistical or machine‑learning models

UEBA is especially effective for large environments where manual baselining is impractical.

### Asset Inventory and Categorization
- Identification of all IT assets
- Assignment of business criticality ratings

More critical systems require tighter baselines and lower tolerance for deviation.

### Vulnerability and Hardening Scans
- Regular scans to ensure systems align with security standards
- Documentation of approved exceptions

Approved deviations become part of the baseline rather than false positives.

---

## Interview Question

**How do you build a baseline for a network you’ve never seen before?**

**Answer:**
> I start with visibility and IT hygiene. First, I perform asset discovery to identify all hosts and understand their roles. Then I collect data on running processes, listening ports, and network flows over a defined observation period to understand what "normal" looks like.
>
> I use a tiered approach—beginning with technical baselines such as gold builds for servers, followed by behavioral baselines for users using centralized logging and analytics. By capturing automated, periodic snapshots, I can detect configuration drift or suspicious activity when a system deviates from its historical known‑good state.

---

## Key Takeaway

Baselining is foundational to effective detection.

- **No baseline → no anomaly**
- **No anomaly → no reliable detection**

A well‑maintained baseline allows analysts to distinguish between **expected behavior, misconfiguration, and true malicious activity** with confidence.



---

**Source: 12.md**

## What is a process and how is it different from a service?

A **process** is an active instance of a computer program executing in memory. It acts as a container for the program’s code and the system resources it requires. A **service** is a specialized type of process designed to run in the background, typically managed by the operating system rather than by direct user interaction.

---

## What Is a Process?

Every program running on an operating system executes within the context of a process. A process provides the runtime environment necessary for an application to function.

### Key Characteristics of a Process

- **Process ID (PID):** A unique, dynamic identifier assigned for the lifetime of the process
- **Memory and Resources:** A dedicated memory space and handles to resources such as files, registry keys, and network sockets
- **Execution Threads:** At least one thread, which is the basic unit scheduled by the CPU
- **Security Context:** Runs under a specific user or system account that defines its permissions
- **Lineage:** Most processes are spawned by a parent process, forming a process tree

A process is typically tied to a **user action** or a **specific system task** and may be short‑lived.

---

## What Is a Service?

A service is a background program designed to perform automated or continuous system functions. While technically still a process, it is distinct in how it is managed and how it behaves.

### Key Characteristics of a Service

- **User Independence:** Can run without an interactive user session and often starts automatically at system boot
- **Centralized Management:** Managed by the operating system’s **Service Control Manager (SCM)**, which handles starting, stopping, and configuration
- **Persistence:** Configured with startup types such as *Automatic*, *Manual*, or *Disabled*
- **Error Recovery:** Often includes built‑in restart or recovery mechanisms if the service fails

Services are designed for **availability and persistence**, not one‑time execution.

---

## Simple Comparison

- A **process** is a running instance of a program executing in memory, usually initiated by a user or a transient system task.
- A **service** is a specialized process intended to run continuously in the background, often without user interaction, and typically starts automatically with the system.

**In short:**
- Processes are about **execution**
- Services are about **persistence and availability**

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, the distinction between processes and services is critical because attackers abuse them for different objectives.

---

## Process (Falcon View)

### Characteristics
- Created when an executable runs
- Has a:
  - Parent process
  - Command line
  - User context
- Often short‑lived

### Common Attacker Abuse
- `powershell.exe`
- `cmd.exe`
- `rundll32.exe`

### Falcon Focus Areas
- Process tree analysis
- Command‑line inspection
- Parent–child relationship anomalies
- Memory access behavior

**Processes usually represent execution and attacker intent.**

---

## Service (Falcon View)

### Characteristics
- A process registered with the **Service Control Manager (SCM)**
- Can run:
  - At system boot
  - As `SYSTEM`
  - Without a logged‑in user
- Often long‑lived

### Common Attacker Abuse
- Malicious service creation
- Service hijacking
- Service binary replacement

### Falcon Focus Areas
- Service creation and modification events
- Service binary path validation
- Privilege context (running as `SYSTEM` is a high‑confidence signal)
- Persistence validation

**Services often represent persistence and elevated privilege.**

---

## Key Takeaway

In investigations:
- **Processes tell you what executed and why**
- **Services tell you how an attacker stays and with what level of control**

Understanding the difference is fundamental for endpoint detection, threat hunting, and incident response.



---

**Source: 13.md**

## What role does explorer.exe play in user activity?

`explorer.exe` is the default **graphical shell** for Windows user sessions. It provides the primary interface through which users interact with the operating system, the filesystem, and applications. As such, it is one of the strongest indicators of **interactive, human‑initiated behavior** on a Windows system.

---

## User Interface Management

The primary function of `explorer.exe` is to render and manage the visible components of the Windows environment.

### Component Hosting
- Desktop
- Taskbar
- Start Menu
- File Explorer

### Operational Impact
- If `explorer.exe` is terminated, the desktop, wallpaper, taskbar, and shortcuts disappear
- Restarting the process restores the user interface

### Navigation Role
- Acts as the main portal for browsing folders and accessing local or network files

---

## Process and Session Relationship

`explorer.exe` is tightly integrated into the Windows logon and execution flow.

### Logon Sequence
- After successful interactive logon:
  - `winlogon.exe` spawns `userinit.exe`
  - `userinit.exe` loads the user profile
  - `explorer.exe` is launched as the user shell

### Process Lineage
- Commonly acts as the **parent process** for applications launched by the user, such as:
  - Double‑clicking executables
  - Opening documents
  - Launching applications from the Start Menu or desktop

### Instance Count
- Typically one instance of `explorer.exe` exists per interactive user session

---

## Security and Forensic Context

Understanding the normal behavior of `explorer.exe` is critical for identifying anomalies during investigations.

### User Permissions
- Runs under the **logged‑in user’s security context**, not as SYSTEM
- Reflects the user’s privilege level and access rights

### Network Access
- Facilitates network connections when users browse UNC paths (e.g., `\\server\\share`) via File Explorer

### Adversarial Abuse
- Trusted, long‑lived process frequently targeted for:
  - Process injection
  - Process hollowing
- Malicious threads can be hidden inside `explorer.exe` to evade detection by blending into normal user activity

---

## SOC Interpretation

`explorer.exe` represents **interactive user behavior**.

- When it appears as a **parent process**, it usually indicates:
  - A human clicked or opened something
  - Execution was user‑assisted rather than automated

For SOC analysis, `explorer.exe` is a strong signal of **user‑initiated execution**, commonly associated with:
- Phishing payload execution
- Malicious document opening
- Downloaded file execution

---

## CrowdStrike‑First Perspective

In **CrowdStrike Falcon**, `explorer.exe` is a critical pivot point during investigations.

### Typical Pattern

```
explorer.exe → child_process.exe
```

This often implies:
- The user clicked or opened content
- Initial access may involve phishing or social engineering

### Analyst Review Focus
- Child process type (LOLBins such as `powershell.exe`, `rundll32.exe`, `mshta.exe`)
- Full command line
- Execution location (e.g., `Downloads`, `AppData`)
- Follow‑on activity:
  - Network connections
  - Credential access
  - Persistence mechanisms

Attackers frequently rely on `explorer.exe` to make malicious execution appear legitimate and user‑driven.

---

## Key Takeaway

- `explorer.exe` is the **Windows user shell**
- It strongly correlates to **human interaction**
- As a parent process, it often marks the **initial execution point** in phishing‑based attacks

For defenders, understanding `explorer.exe` behavior is essential for separating **user‑driven compromise** from automated or system‑level activity.



---

**Source: 14.md**

## Why is svchost.exe commonly abused by attackers?

`svchost.exe` (Service Host) is a legitimate Windows system process designed to act as a **container for multiple background services implemented as Dynamic Link Libraries (DLLs)**. Its architecture, privilege level, and ubiquity make it a frequent target for abuse by threat actors.

---

## Interview-Grade Model Answer

**Question:** Why is `svchost.exe` so frequently targeted and abused by attackers?

**Answer:**
`svchost.exe` is abused primarily because of its **ubiquity and complexity**. Modern Windows systems run many instances of `svchost.exe` simultaneously to host DLL-based services, making it easy for malicious activity to blend into normal system behavior. Attackers typically abuse it in two main ways:

1. **Masquerading**  
   Attackers name malicious executables `svchost.exe` (or close variants such as `scvhost.exe`) and place them in **non-standard directories** like `C:\Windows\Temp` or user-writable paths. Because the process name appears legitimate, it can evade casual inspection.

2. **Process Injection**  
   Malicious code is injected into a **legitimate `svchost.exe` process**, allowing execution under the context of a trusted, high-privilege system process and making detection harder for signature-based tools.

---

## What Interviewers Listen For

Strong answers usually demonstrate the following understanding:

- **Architectural knowledge**: `svchost.exe` hosts services as **DLLs**, not standalone executables
- **Parent–child lineage**: Legitimate instances are spawned by `services.exe`
- **Path validation**: The only legitimate path is `%SystemRoot%\System32\svchost.exe`
- **Modern isolation model**: On Windows 10/11 systems with sufficient RAM, services often run in **separate svchost instances** for better isolation

---

## MITRE ATT&CK Mapping

Common techniques associated with `svchost.exe` abuse include:

- **T1036.003 – Masquerading: Rename System Utilities**  
  Naming a malicious binary `svchost.exe` to blend in

- **T1055 – Process Injection**  
  Injecting code into a legitimate `svchost.exe` instance

- **T1543.003 – Create or Modify System Process: Windows Service**  
  Creating or modifying a service that uses `svchost.exe` to achieve persistence

---

## Mock Incident Scenario

**Scenario:** An automated alert flags an *unusual process parent* on a critical file server.

### Evidence
- A process named `svchost.exe` is running from `C:\Windows\Temp`
- Parent process is `cmd.exe`

### Triage Logic

1. **Path Check**  
   Legitimate `svchost.exe` runs only from `System32`. Execution from `Temp` confirms masquerading.

2. **Lineage Check**  
   Legitimate `svchost.exe` is spawned by `services.exe`. Being spawned by `cmd.exe` indicates manual execution.

3. **Argument Analysis**  
   Legitimate instances typically include the `-k` service group flag (e.g., `-k netsvcs`). Missing or abnormal arguments warrant immediate containment.

---

## Why svchost.exe Is Attractive to Attackers

`svchost.exe` is abused because it is a **trusted, high-privilege Windows process** that blends naturally into normal system behavior.

### Key Factors

1. **Runs as SYSTEM**  
   Many instances execute as `NT AUTHORITY\SYSTEM`, granting attackers immediate high privilege.

2. **Expected to Run Continuously**  
   Long-lived background process where network activity often appears normal, aiding C2 concealment.

3. **Hosts Multiple Services**  
   One binary hosting many services allows malicious behavior to hide within legitimate noise.

4. **Flexible Execution Model**  
   Attackers can:
   - Register malicious services
   - Hijack service DLLs
   - Abuse service parameters to load malicious code

5. **Common in Legitimate Operations**  
   Analysts expect to see `svchost.exe`, making abuse less suspicious at first glance.

---

## CrowdStrike Falcon Perspective

In **CrowdStrike Falcon**, `svchost.exe` is treated as a **high-value process and high-risk abuse target**. Investigations focus on:

- Path and signature validation
- Parent process verification (`services.exe` vs user-initiated processes)
- Command-line and service group analysis
- Behavioral deviations within otherwise trusted service activity

---

## Key Takeaway

`svchost.exe` is commonly abused because it is **trusted, privileged, long-lived, and ubiquitous**. Attackers leverage it to hide execution, gain SYSTEM-level access, establish persistence, and evade detection.

A mature SOC treats `svchost.exe` as **normal—but never blindly trusted**.


---

**Source: 15.md**

## Why is execution from the AppData directory considered highly suspicious?

Execution from the **AppData directory** (and the broader user profile path) is considered highly suspicious because it is a **user‑writable location** where standard, non‑privileged users can place and execute files. Unlike protected system directories such as `C:\Windows\System32`, AppData does **not** require administrative privileges to modify, allowing adversaries to stage and run malware **without bypassing UAC or gaining elevation**.

As a result, AppData is a common staging ground for **initial access, persistence, and masquerading**.

---

## Interview‑Grade Model Answer

**Question:** Why is process execution from the AppData directory often flagged as a high‑risk event?

**Answer:**
Execution from AppData is suspicious primarily because of the **permissions context**. It is one of the few locations on Windows where a non‑administrative user can write and execute binaries. Attackers abuse this to drop malware and establish persistence without requiring local administrator rights.

Additionally, some legitimate applications install in the user context, making AppData a frequent choice for **masquerading**. An executable with a system‑like name—such as `svchost.exe`—running from a user’s AppData path is a strong indicator of a human adversary attempting to hide in plain sight.

---

## What Interviewers Listen For

Strong answers usually include:

- **User permissions**: AppData allows file placement and execution without administrative approval
- **Persistence mechanisms**: Use of Startup folders or Registry Run keys pointing to AppData paths
- **Whitelisting context**: Application control policies (e.g., AppLocker) typically block execution from user‑writable directories
- **Evasion tactics**: Use of hidden subfolders to store scripts or Living‑off‑the‑Land (LOLBin) artifacts

---

## MITRE ATT&CK Mapping

Common techniques associated with AppData abuse include:

- **T1547.001 – Boot or Logon Autostart Execution**  
  Using AppData subfolders for Registry Run keys or Startup folder persistence

- **T1036.005 – Masquerading: Match Legitimate Name or Location**  
  Placing binaries with system‑like names in AppData

- **T1204.002 – User Execution: Malicious File**  
  Tricking users into executing payloads stored in their profile directories

---

## Mock Incident Scenario

**Scenario:** An EDR alert triggers for *Unsigned Binary Execution* from `C:\Users\Public\AppData\Local\Temp`.

### Observation
- Binary name: `security_patch.exe`

### Triage Steps

1. **Parent Process**  
   Spawned by `outlook.exe`, indicating likely phishing attachment execution

2. **Signature Check**  
   File is unsigned—common for malware, rare for legitimate security patches

3. **Persistence Check**  
   New Registry Run key points to the binary in the Temp directory

### Assessment
**High‑confidence true positive.** The attacker abused a user‑writable directory to bypass protections and establish a foothold.

---

## Why Attackers Prefer AppData

From a defensive standpoint, AppData offers attackers multiple advantages:

### User‑Writable (No Admin Required)
- Standard users can write and execute files
- Ideal for phishing‑based initial access

### Trusted by Users
- Browsers and applications routinely write to AppData
- Files in this location attract little user suspicion

### Persistence‑Friendly
- Commonly paired with:
  - Registry Run keys
  - Scheduled tasks
  - Startup folder abuse

### Low Operational Visibility
- Thousands of legitimate files already exist
- Malicious binaries blend into background noise

### Pairs Well with LOLBins
- `AppData\\*.exe` → `powershell.exe`
- `AppData\\*.dll` → `rundll32.exe`

---

## CrowdStrike Falcon Perspective

In **CrowdStrike Falcon**, execution from AppData is treated as a **high‑signal context indicator**, especially when combined with:

- User‑initiated parent processes (e.g., `outlook.exe`, `winword.exe`)
- Unsigned binaries
- Persistence attempts
- LOLBin usage

---

## Key Takeaway

Execution from AppData is suspicious because it represents **user‑level execution in a location not intended for running binaries**.

Legitimate software rarely needs to execute from AppData—**attackers rely on this gap** to bypass controls, persist quietly, and blend into normal user activity.



---

**Source: 16.md**

## What are LOLBins and why are they dangerous?

**LOLBins (Living‑Off‑the‑Land Binaries)** are legitimate, trusted operating system binaries that attackers abuse to perform malicious actions such as **execution, persistence, defense evasion, lateral movement, and data exfiltration**.

They are dangerous because they leverage tools that already exist on the system, allowing attackers to blend into normal activity and reduce their reliance on custom malware.

---

## Why LOLBins Are Dangerous

Attackers prefer LOLBins because they provide a strong tactical advantage over traditional malware.

### Built‑In and Trusted
- Already present on the operating system
- Digitally signed (often by Microsoft)
- Rarely blocked by default security controls

### Detection Evasion
- No dropped malware binaries
- No unique or known hashes to block
- Frequently bypass signature‑based detection

### Hiding in Plain Sight
- Commonly used by administrators for legitimate tasks
- Malicious usage blends into normal system noise
- Difficult to distinguish without behavioral context

### Fileless Capabilities
- Many LOLBins support in‑memory execution
- Malicious code can run without being written to disk
- Leaves a minimal forensic footprint

### Powerful, Flexible Functionality
- Tools such as `certutil.exe` and `bitsadmin.exe` enable stealthy file downloads
- `powershell.exe` and `wmic.exe` provide extensive local and remote execution control

---

## LOLBins in Real SOC Operations

LOLBins are especially dangerous in live SOC environments because they:

- Are **trusted by default**
- Evade traditional signature‑based controls
- Chain easily into multi‑stage attacks
- Support multiple MITRE ATT&CK tactics with a single tool

### Common LOLBin Execution Chains

- `winword.exe` → `powershell.exe` → `rundll32.exe`

Without correlation and context, this behavior can appear legitimate.

---

## CrowdStrike Falcon Perspective

In **CrowdStrike Falcon**, LOLBins are considered a **primary adversary technique**, not an edge case.

### Commonly Abused LOLBins Observed in Falcon

- `powershell.exe`
- `cmd.exe`
- `rundll32.exe`
- `mshta.exe`
- `certutil.exe`
- `wmic.exe`
- `bitsadmin.exe`
- `regsvr32.exe`

Falcon detections focus on **behavior, execution context, and chaining**, rather than simply the presence of these binaries.

---

## Why Signature‑Based Detection Fails Against LOLBins

- The binary itself is legitimate
- The hash is trusted
- The activity may be indistinguishable from admin behavior without context

This forces defenders to rely on:
- Process lineage
- Command‑line analysis
- Parent–child relationships
- Behavioral sequencing

---

## Key Takeaway

LOLBins are dangerous because they allow attackers to **live off the land**—using trusted, pre‑installed tools to perform malicious actions while avoiding traditional malware detection.

A mature SOC does not hunt LOLBins by name—it hunts **abusive behavior, context, and intent**.



---

**Source: 17.md**

## What is a parent–child process relationship?

A **parent–child process relationship** occurs when one process (the **parent**) creates or *spawns* another process (the **child**). Modern operating systems operate through process genealogies rather than isolated executions—the parent typically provides the execution environment and often the **security context** under which the child runs.

Understanding these relationships is fundamental to security monitoring because the **parent often explains *why* the child executed**.

---

## Core Mechanics

### Spawning
- The parent process initiates creation of the child
- **Windows:** `CreateProcess` API
- **Linux/Unix:** `fork()` followed by `execve()`

### Identifiers
- Each child process records a **Parent Process ID (PPID)**
- PPID allows analysts to trace execution back to its origin

### Termination Behavior
- Some parents are designed to spawn a child and exit immediately
  - Examples: `userinit.exe`, certain `smss.exe` instances

---

## Standard Lineage Examples ("Normal" Behavior)

Knowing expected process genealogy is critical for spotting anomalies.

### System Boot
- `wininit.exe` → `services.exe`
- `wininit.exe` → `lsass.exe`

### Services
- `services.exe` → `svchost.exe`

### User Activity
- `explorer.exe` → user-launched applications

Deviations from these patterns are often high-signal indicators of compromise.

---

## Interview-Grade Explanation

**Question:** Can you explain the significance of parent–child process relationships in security monitoring?

**Answer:**  
A parent–child relationship is created when a running process spawns another process. The child usually inherits the parent’s security context unless explicitly changed. For SOC analysts, this relationship is one of the primary ways to assess execution legitimacy.

We look for deviations from expected operating system genealogy. For example, `svchost.exe` should be spawned by `services.exe`. If `svchost.exe` is spawned by `cmd.exe` or `outlook.exe`, it strongly indicates masquerading or malicious execution. By tracing the PPID back to the root, analysts can perform root-cause analysis to determine whether an attack originated from a document macro, browser download, phishing email, or service abuse.

---

## Why Parent–Child Relationships Matter in SOC Investigations

- The parent provides **context and intent**
- The execution chain explains *how* and *why* a process started
- Root-cause analysis depends on reliable process ancestry

---

## CrowdStrike Falcon Perspective

In **CrowdStrike Falcon**, parent–child analysis is one of the **highest-signal investigation techniques**.

Falcon exposes process ancestry through:
- Process Tree
- `ProcessRollup` events
- Incident Graph view

---

## What SOC Analysts Check Immediately

- Is the **parent process expected**?
- Is the **child appropriate** for that parent?
- Does the **full chain** match normal behavior?

---

## Common High-Risk Parent → Child Chains

- `winword.exe` → `powershell.exe`
- `excel.exe` → `cmd.exe`
- `explorer.exe` → `rundll32.exe`
- `svchost.exe` → `unknown.exe`
- `services.exe` → binary executing from `AppData`

These patterns commonly indicate:
- Phishing-based initial access
- LOLBin abuse
- Malware staging
- Privilege escalation attempts

---

## Key Takeaway

Parent–child process relationships provide **execution intent, context, and origin**.

A mature SOC treats process ancestry as a **primary signal**, not a supporting detail—because most real attacks reveal themselves through *how execution began*, not just *what executed*.



---

**Source: 18.md**

## What makes a process tree suspicious?

A **process tree** becomes suspicious when the sequence of parent–child executions **deviates from normal behavior**, especially when trusted or user‑facing processes launch administrative tools, scripts, or binaries in unexpected ways.

In other words:
> **It’s not one process that’s suspicious — it’s the story the process chain tells.**

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, analysts rarely judge a process in isolation. Instead, they assess the **entire execution chain** using:
- Process Tree
- Incident Graph
- Host Timeline

A process tree is considered suspicious when one or more high‑risk patterns emerge.

---

## 1. Unusual Parent → Child Relationships

Certain parent–child combinations are strong indicators of malicious activity.

### High‑Risk Examples
- `winword.exe` → `powershell.exe`
- `excel.exe` → `cmd.exe`
- `explorer.exe` → `rundll32.exe`
- `services.exe` → binary executing from `AppData`

### What These Indicate
- Phishing‑based initial access
- LOLBin abuse
- User‑assisted execution

---

## 2. Abuse of Trusted Binaries (LOLBins)

Process trees become suspicious when **legitimate tools are chained unnaturally**.

### Example Chain
```
explorer.exe → powershell.exe → rundll32.exe → network activity
```

### Why This Is High Risk
- All binaries are signed and trusted
- No malware drop is required
- Detection depends on **behavioral correlation**, not file hashes

---

## 3. Execution from Suspicious Locations

Child processes executing from **user‑writable paths** significantly increase risk.

### Common Suspicious Locations
- `AppData`
- `Temp`
- `Downloads`
- `ProgramData`

### Especially Concerning When Launched By
- Office applications
- Web browsers
- Windows services

---

## 4. Privilege or Context Mismatch

A mismatch between execution context and expected behavior is a strong signal.

### Examples
- User‑level process spawning SYSTEM‑level behavior
- `svchost.exe` launching non‑service binaries
- Service accounts running interactive tools

### Common Implications
- Privilege escalation
- Service abuse
- Persistence setup

---

## 5. Post‑Execution Behavior

A process tree becomes far more suspicious when **follow‑on activity** is observed.

### High‑Risk Follow‑On Signals
- Outbound network connections
- Credential access (e.g., LSASS handle access)
- Registry modifications
- Scheduled task or service creation

Attackers often reveal intent **after initial execution**.

---

## Understanding Parent–Child Process Relationships

A **parent–child process relationship** exists when one process spawns another. Modern operating systems rely on process genealogy rather than isolated execution.

### Core Mechanics

- **Spawning**  
  - Windows: `CreateProcess`
  - Linux/Unix: `fork()` and `execve()`

- **Identifiers**  
  - Each process records a Parent Process ID (PPID)

- **Termination Patterns**  
  - Some parents (e.g., `userinit.exe`, certain `smss.exe` instances) spawn a child and exit immediately

---

## Normal Process Lineage Examples

Understanding what is *expected* is essential for spotting anomalies.

### System Boot
- `wininit.exe` → `services.exe`
- `wininit.exe` → `lsass.exe`

### Services
- `services.exe` → `svchost.exe`

### User Activity
- `explorer.exe` → user‑launched applications

Deviations from these patterns are often high‑confidence indicators of compromise.

---

## Interview‑Grade Explanation

**Question:** Can you explain the significance of parent–child process relationships in security monitoring?

**Answer:**  
A parent–child relationship forms when a running process creates another process. The child usually inherits the security context of the parent unless explicitly changed. For SOC analysts, this relationship is one of the most reliable ways to determine execution legitimacy.

We look for deviations from standard OS genealogy. For example, `svchost.exe` should be spawned only by `services.exe`. If it is spawned by `cmd.exe` or `outlook.exe`, it strongly indicates masquerading or malicious execution. By tracing the PPID back to the root, analysts can perform root‑cause analysis to identify whether a chain began with a document macro, browser download, or service exploit.

---

## Key Takeaway

A suspicious process tree is defined by **context, sequence, and intent**.

- Individual processes may look benign
- Execution chains reveal attacker behavior

A mature SOC treats process trees as **primary investigative evidence**, because most real‑world attacks expose themselves through *how execution unfolds*, not just *what executable ran*.



---

**Source: 19.md**

## Why is command-line visibility vital for SOC analysts?

Command-line visibility removes the **blinders** from incident response. It provides a precise technical trail that shows **what actions were taken**, **how tools were used**, and **why execution occurred**. While traditional antivirus may flag a malicious binary, modern adversaries frequently **live off the land**, abusing built-in tools where **the command-line arguments—not the binary—reveal intent**.

> The process name tells you *what* ran. The command line tells you *how* and *why*.

---

## 1. Context and Intent

Command-line arguments are often the **only reliable way** to distinguish legitimate administration from malicious activity.

### Beyond the Binary
- Seeing `rundll32.exe` or `certutil.exe` execute is insufficient
- Arguments determine whether the tool is:
  - Performing a routine task
  - Downloading payloads
  - Executing injected or sideloaded code

### Identifying Malicious Intent
- Example: `wmiprvse.exe` spawning `cmd.exe`
- This is a high-fidelity indicator of **WMI-based attack activity**—but only visible with command-line auditing enabled

---

## 2. Detecting Living-off-the-Land (LOLBins)

Attackers increasingly rely on legitimate, pre-installed tools to evade detection and bypass application controls.

### Trusted Tools, Abused
- Commonly abused tools include:
  - PowerShell
  - WMI
  - `net.exe`

### Automation Visibility
- Attackers script reconnaissance, lateral movement, and credential access
- Command-line data reveals:
  - Account enumeration
  - Network share mapping
  - Remote execution attempts

---

## 3. Uncovering Obfuscation and Evasion

Adversaries hide intent using flags and encodings that are **only visible in arguments**.

### Encoding
- Base64 encoding (e.g., PowerShell `-enc` / `-EncodedCommand`)
- Capturing the string enables decoding and analysis

### Stealth Execution
- Flags such as `-w hidden` or `-nop` run commands without a visible window
- These tactics evade user notice and basic monitoring

---

## 4. Analyzing Process Lineage

Command-line data is essential for understanding **parent–child relationships**.

### Anomalous Spawning
- Suspicious examples:
  - `winword.exe` → `cmd.exe`
  - `w3wp.exe` → `powershell.exe`

### Root Cause Analysis
- Reviewing the **Creator Process Name** and its arguments reveals origin:
  - Phishing attachment
  - Browser exploit
  - Compromised service

---

## 5. Implementation Requirements (Windows)

Full command-line visibility is **not enabled by default**.

### Group Policy Configuration
- Enable **Audit Process Tracking**
- Enable **Include command line in process creation events**

### Key Logging Sources
- **Security Log:** Event ID **4688** (Process Creation)
- **Sysmon:** Event ID **1** (Process Create)
  - Adds hashes, parent command lines, and richer context

---

## CrowdStrike Falcon Perspective

In **CrowdStrike Falcon**, command-line data is one of the **highest-signal investigation artifacts**.

### Where Falcon Exposes Command-Line Context
- Process Tree
- `ProcessRollup` events
- Detection details
- Reconstructed commands (when available)

### Why This Matters in Practice

- `powershell.exe`  
  → could be benign or malicious

- `powershell.exe -enc <base64>`  
  → **high-confidence malicious**

- `rundll32.exe`  
  → normal Windows component

- `rundll32.exe <temp_path>,Start`  
  → **DLL sideloading / execution abuse**

Attackers almost always reveal themselves **in the arguments, not the binary**.

---

## Key Takeaway

- Command-line visibility reveals **intent**
- Most modern attacks look benign at the process level
- Arguments expose abuse, obfuscation, and attacker objectives

Without command-line visibility, SOC analysts lose the ability to reliably separate **legitimate administration** from **active compromise**.



---

**Source: 20.md**

## What Is DLL Sideloading?

DLL sideloading is a cyber attack technique where an adversary abuses legitimate Windows functionality to trick a trusted, often digitally signed, application into loading a malicious Dynamic Link Library (DLL). By placing a malicious DLL alongside a legitimate executable, the attacker ensures their code executes **inside the context of a trusted process**, significantly reducing the chance of detection.

In simple terms:
> **Attackers hijack trust by abusing how Windows looks for DLLs.**

---

## The Side-by-Side (SxS) Mechanism

The technical foundation of DLL sideloading is the Windows **Side-by-Side (SxS)** loading mechanism.

### Legitimate Purpose

- SxS was designed to allow applications to safely manage **multiple versions of the same DLL**.
- It prevents "DLL hell" by enabling applications to load specific library versions from local or shared locations.

### Adversarial Abuse

- The DLL loading mechanism often relies on **relative paths** and performs **minimal validation**.
- An attacker can place a malicious DLL with the expected name in a directory the application checks **before** system locations.

### DLL Search Order Abuse

- Many applications search for required DLLs in the **same directory as the executable** first.
- If a malicious DLL exists there, it is loaded instead of the legitimate system DLL.

---

## Why Attackers Use DLL Sideloading

DLL sideloading is favored by sophisticated adversaries because it offers multiple advantages:

### Bypassing Defenses

- The primary executable is legitimate and digitally signed.
- Antivirus and application control solutions often trust the signed binary, allowing malicious code to execute unnoticed.

### Persistence

- Each time the legitimate application launches, the malicious DLL is reloaded.
- This provides reliable and low-noise persistence.

### Hiding in Plain Sight

- Malicious code runs as threads inside a known-good process.
- This allows evasion of allowlists, signature-based detection, and superficial process monitoring.

---

## Real-World Examples

DLL sideloading is widely used in real-world attacks:

- **PlugX RAT**  
  Drops a legitimate, signed executable (often present in the NSRL known-good database) and sideloads a malicious DLL at runtime.

- **Other Malware Families**  
  Campaigns involving **NetTraveler**, **Sakula**, and **Poison Ivy** have all used DLL sideloading for execution or persistence.

---

## Detection and Investigation

Identifying DLL sideloading requires **behavioral and contextual analysis**, not signature matching.

### Key Investigation Steps

- **Identify New Files**  
  Look for newly created DLLs or helper files placed alongside legitimate executables.

- **Verify DLL Signatures**  
  Unsigned or rare DLLs loaded by highly trusted binaries are a strong signal.

- **Analyze Process Paths**  
  Investigate system-named processes running from non-standard locations (e.g., Downloads, AppData).

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, DLL sideloading is treated as a **high-confidence execution technique** when supporting context is present.

### Typical Falcon Indicators

- A **signed executable** running from:
  - Downloads
  - ProgramData
  - Application install directories

- Followed by an **unsigned or rare DLL load**

- DLL loaded from:
  - The same directory as the executable
  - A user-writable path (e.g., AppData)

- Immediate post-load behavior such as:
  - Network connections
  - Process injection
  - Persistence creation

### How Falcon Analysts Validate Sideloading

- Review **ImageLoad** events
- Check **DLL signature status**
- Compare **DLL path vs expected path**
- Analyze **Process Tree** and **Host Timeline**

---

## Key Takeaway

DLL sideloading is not about exploiting a vulnerability — it is about **abusing trust and default Windows behavior**.

The executable is legitimate.
The DLL is malicious.
The trust relationship is the weakness.

Understanding this technique is critical for modern endpoint detection, threat hunting, and incident response.



---

**Source: 21.md**

## Why Do Attackers Prefer Signed Binaries?

Attackers prefer signed binaries because they exploit the **implicit trust** that operating systems, security controls, and even human analysts place in digitally signed code. A valid signature does not guarantee safety—it only indicates the publisher’s identity. Adversaries abuse this distinction to bypass defenses, evade detection, and operate with reduced scrutiny.

In short:
> **Signatures confer trust, not safety.**

---

## 1. Bypassing Defensive Controls

Many defensive layers are intentionally designed to trust signed software to avoid disrupting legitimate operations.

### Antivirus (AV) Avoidance

- Digitally signed tools are often not classified as malware by AV engines.
- Legitimate signed utilities (e.g., PsExec) are commonly abused because they blend into normal administrative activity.

### Whitelisting Evasion

- Application control technologies (e.g., AppLocker, WDAC) frequently allow execution of binaries signed by trusted vendors.
- Attackers abuse built-in, signed Windows binaries to perform malicious actions without triggering blocks.

### Stealth and Increased Dwell Time

- Signed binaries blend into background system noise.
- Reduced suspicion allows attackers to remain undetected for longer periods.

---

## 2. Overcoming Operating System Restrictions

Modern Windows security features rely heavily on digital signatures.

### Key Protections That Depend on Signatures

- **Driver Signature Enforcement (DSE)**  
  Only signed drivers can be loaded into the kernel.

- **Code Integrity Guard (CIG)**  
  Restricts applications to loading only Microsoft-signed DLLs when enabled.

- **Smart App Control (SAC)**  
  Requires valid signatures from known publishers if safety cannot be predicted.

- **Protected Process Light (PPL)**  
  Binaries signed with specific certificates can run as protected processes, resisting tampering and termination.

By abusing signed binaries, attackers operate inside these trust boundaries rather than attempting to break them.

---

## 3. Supply Chain and Certificate Exploitation

Adversaries sometimes obtain signed status directly.

### Trust Mimicry

- Attackers compromise legitimate software vendors.
- Malicious code is embedded into otherwise trusted applications.

### Certificate Theft

- Code-signing certificates or private keys are stolen.
- Malware is signed using the organization’s own certificate, appearing fully legitimate.

### Automation at Scale

- Modern campaigns may mutate malware payloads while retaining a stolen or forged signature.
- Static signature-based detection becomes ineffective.

---

## 4. The Catch‑22 of Signed Malware

Despite the advantages, **most malware remains unsigned**.

- Signing increases attacker risk.
- If signed malware is detected, the certificate can be **revoked**.
- Revocation instantly exposes all systems infected with that malware family worldwide.

This makes signing powerful—but dangerous—for adversaries.

---

## 5. Mock Incident Scenario

**Scenario:** A SOC analyst investigates an unusual process tree on a high-value server.

- **Observation:** A legitimate, signed management agent deploys an “automatic update” containing a DLL.
- **Triage:** The signature is valid and belongs to a trusted vendor.
- **Suspicious Behavior:** The process attempts to access LSASS memory.
- **Investigation:** Analysis reveals the vendor’s CI/CD pipeline was compromised.
- **Result:** The malicious module was signed during the build process and bypassed file-reputation controls for weeks before behavioral detection.

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, signed binaries are treated as **frequent abuse targets**, not trusted endpoints.

### Why Attackers Favor Signed Binaries

#### 1. Trust Inheritance & Control Bypass

- Signed binaries:
  - Bypass allowlists and application controls
  - Generate less user suspicion
- Especially effective during:
  - Phishing-based initial access
  - User-assisted execution

Falcon prioritizes **execution context**, not signature trust.

---

### LOLBin Abuse (Most Common)

Attackers frequently abuse Microsoft-signed LOLBins, including:

- `powershell.exe`
- `rundll32.exe`
- `mshta.exe`
- `regsvr32.exe`
- `wmic.exe`

In Falcon investigations, the binary name alone is meaningless without:

- Parent process
- Command line
- Follow-on behavior

---

### DLL Sideloading & Trust Hijacking

- A signed executable loads an unsigned malicious DLL.
- Malicious code executes inside a trusted process context.

Falcon analysts flag:

- Signed parent + unsigned DLL
- DLL loaded from user-writable paths
- Immediate network or persistence behavior

---

### Defense Evasion & Analyst Bias

- Many environments still rely on:
  - File reputation
  - Static trust assumptions
- Signed binaries often receive less scrutiny.

Falcon counters this with:

- Behavior-based Indicators of Attack (IOAs)
- Incident-level correlation
- Cross-host and cross-user context

---

## Key Takeaway

Attackers prefer signed binaries because **trust is exploitable**.

Signed executables are less likely to be blocked, questioned, or prioritized, allowing adversaries to operate under the appearance of legitimacy.

Effective defense requires evaluating **behavior and context**, not signatures alone.


