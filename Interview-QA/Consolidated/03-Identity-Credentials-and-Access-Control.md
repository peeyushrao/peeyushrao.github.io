# Identity, Credentials, and Access Control

Interview questions and answers, grouped by topic. Each source section retains its original content.

---

**Source: 22.md**

## What Is the Difference Between Authentication and Authorization?

Authentication and authorization are distinct but tightly connected security concepts. **Authentication verifies identity**, while **authorization determines access**. One answers *who you are*; the other answers *what you are allowed to do*.

> You cannot authorize an entity that has not first been authenticated.

---

## Fundamental Differences

### Authentication — *The “Who”*

Authentication is the process of proving identity.

It answers the question:
> **“Are you really who you claim to be?”**

Common authentication methods include:
- Passwords and passphrases
- Biometrics (fingerprint, face recognition)
- Multi-Factor Authentication (MFA)
- Certificates or cryptographic keys

If authentication fails, access stops immediately.

---

### Authorization — *The “What”*

Authorization occurs **after successful authentication** and determines permissions.

It answers the question:
> **“What are you allowed to access or do?”**

Authorization is enforced using:
- Access Control Lists (ACLs)
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- The principle of least privilege

A user may be authenticated successfully but still denied access to specific resources.

---

## In Short

- **Authentication = identity proof**
- **Authorization = permission enforcement**

Both are required for secure access control.

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, the distinction between authentication and authorization is critical for **incident triage, risk assessment, and scoping**.

---

## Authentication: Identity Compromise Focus

Authentication-related analysis answers:
- Did the attacker successfully log in?
- Were credentials stolen, replayed, or bypassed?
- Was MFA present, absent, or bypassed?

Falcon combined with identity telemetry helps detect:
- Successful use of stolen credentials
- Anomalous logins following endpoint compromise
- Credential access attempts (e.g., LSASS memory access)

If authentication is compromised, **account takeover becomes possible**.

---

## Authorization: Impact and Blast Radius Focus

Authorization analysis answers:
- What systems could the attacker access?
- What actions could they perform?
- Did the compromised account have:
  - Administrative privileges?
  - Domain-level rights?
  - Access to sensitive or regulated data?

In Falcon investigations:
- A compromised **low-privilege user** typically represents lower immediate risk
- A compromised **privileged account** is a high-risk incident, even with minimal observed activity

Authorization determines **business impact and blast radius**, not authentication alone.

---

## Key Takeaway

Authentication determines **whether access is possible**.
Authorization determines **how damaging that access can be**.

Effective incident response requires understanding both — a successful login without privilege may be noise, while a single privileged authentication can represent a major breach.



---

**Source: 23.md**

## Why Are Service Accounts Frequently Targeted?

Service accounts are frequently targeted by adversaries because they combine **high privileges**, **persistent access**, and **weak security controls**. Unlike interactive user accounts, service accounts are designed to run continuously in the background, which makes malicious use harder to notice and easier to sustain.

---

## Model Answer (Interview‑Grade)

> *“Service accounts are high‑value targets primarily because they are often over‑privileged and poorly managed. Unlike standard user accounts, service accounts frequently use static passwords that never expire and lack interactive protections, making them susceptible to attacks such as Kerberoasting. Because services start automatically and run continuously, service accounts provide reliable persistence. Many also run under powerful security contexts such as SYSTEM or LocalSystem, granting extensive access. Finally, because service activity is expected and automated, malicious behavior can easily blend into background noise.”*

---

## Technical Reasons Attackers Target Service Accounts

### Static or Long‑Lived Credentials

- Manually created service accounts often have passwords that:
  - Never expire
  - Are rarely rotated
- This contrasts with:
  - **Managed Service Accounts (MSA)**
  - **Group Managed Service Accounts (gMSA)**, which use OS‑managed password rotation
- Static credentials are ideal for:
  - Kerberoasting
  - Credential replay
  - Long‑term persistence

---

### Local Credential Storage (LSA Secrets)

- Credentials for service accounts are stored locally as encoded **LSA Secrets**
- Any account with administrative access can extract these secrets
- Once obtained, attackers can reuse credentials across systems

---

### Built‑In Persistence

- Services:
  - Start automatically at boot
  - Run without user interaction
- Attackers can modify service configuration to maintain access, for example:
  - Changing the **ImagePath** of a legitimate service in:
    ```
    HKLM\SYSTEM\CurrentControlSet\Services
    ```
  - Pointing the service to a malicious binary

---

## High‑Level Summary

Service accounts are frequently targeted because they:
- Have **high privileges**
- Use **long‑lived credentials**
- Run continuously and silently
- Receive **less scrutiny and monitoring** than user accounts

They are ideal for **stealthy, persistent access**.

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, service account abuse is treated as a **high‑risk identity signal**, even when activity appears legitimate.

---

### 1. Elevated Privileges by Design

- Service accounts often have:
  - Local administrator rights
  - Server‑level privileges
  - Sometimes domain‑level permissions
- Compromise often removes the need for additional privilege escalation

> In Falcon investigations, **low activity + high privilege** is more dangerous than noisy malware.

---

### 2. Long‑Lived / Non‑Rotating Credentials

- Common characteristics:
  - Passwords that do not expire
  - Credentials embedded in scripts or configuration files
- Enables:
  - Pass‑the‑hash
  - Credential replay
  - Long‑term persistence

Falcon frequently correlates:
- LSASS access → service account use → lateral movement

---

### 3. Non‑Interactive Nature = Low Visibility

- No human user to notice abnormal behavior
- Activity is often assumed to be:
  - Automation
  - Scheduled jobs
  - Backend processing

This allows attackers to hide inside expected background noise.

---

### 4. Broad Lateral Reach

- Service accounts commonly authenticate:
  - Across multiple servers
  - Across environments (on‑prem, cloud, applications)
- A single compromised service account can enable widespread lateral movement

Falcon XDR highlights this when:
- The same service account appears on multiple hosts unexpectedly

---

### 5. Weak MFA and Monitoring Coverage

- MFA is rarely enforced on service accounts
- Logging is often incomplete or deprioritized

Attackers deliberately choose accounts with **fewer controls and weaker alerting**.

---

## Key Takeaway

Service accounts are targeted not because they are obscure, but because they are **powerful, persistent, and trusted by default**.

Defending them requires:
- Least‑privilege design
- Credential rotation (gMSA where possible)
- Strong monitoring of service account behavior
- Treating service account activity as **identity risk**, not routine automation



---

**Source: 24.md**

## What Is Lateral Movement?

Lateral movement refers to the techniques and strategies an adversary uses to move **from one compromised system to other systems within the same environment** after gaining an initial foothold. This phase allows attackers to expand access, discover high-value assets, and position themselves for maximum impact.

It is one of the most critical—and dangerous—stages of a cyberattack because it turns a **single-host compromise** into an **environment-wide incident**.

---

## Model Answer (Interview-Grade)

> *“Lateral movement is the process by which an attacker, after compromising an initial system, moves to other systems inside the internal network. The goal is to access more sensitive data, traverse network segments, and escalate privileges to obtain ‘keys to the kingdom’ credentials such as Domain Admin. Technically, it often involves harvesting credentials—such as dumping hashes from LSASS—and then using legitimate administrative tools like RDP, PsExec, or PowerShell Remoting to execute on additional hosts. It is difficult to detect because attackers rely on valid credentials and built-in tools, blending into normal administrative activity.”*

---

## In Simple Terms

Lateral movement is the phase of an attack where an adversary:
- Moves from **one host to another**
- Uses **stolen credentials**, **existing trust relationships**, or **legitimate admin tools**
- Expands access to reach **higher-value systems**
- Positions for final objectives such as:
  - Data theft
  - Ransomware deployment
  - Domain or cloud compromise

---

## Why Lateral Movement Is Hard to Detect

- No new malware may be introduced
- Actions often look like legitimate IT administration
- Tools used are:
  - Signed
  - Native to the OS
  - Common in enterprise environments

Detection therefore relies on **context and correlation**, not single events.

---

## CrowdStrike Perspective

In **CrowdStrike Falcon**, lateral movement is rarely identified by a single alert. It is detected through **correlation of endpoint, identity, and behavioral telemetry**.

---

## 1. Credential Reuse Across Hosts

A key Falcon signal is the **same identity appearing on multiple systems**.

Indicators include:
- A user or service account authenticating to:
  - Multiple hosts
  - New or previously unused hosts
  - Systems at unusual times

Especially high-risk when:
- The account is privileged
- The source host has prior compromise indicators

Falcon XDR emphasizes **identity movement patterns**, not just login success.

---

## 2. Legitimate Tools Used Illegitimately

Attackers frequently use built-in administrative tools, including:

- PsExec
- `wmic`
- `sc.exe`
- `net use`
- Remote Desktop Protocol (RDP)
- SMB and Windows administrative shares

These tools are:
- Digitally signed
- Widely used by administrators
- Only suspicious **in context**

Falcon focuses on:
- **Who** used the tool
- **From which host**
- **Following what prior activity**

---

## 3. Movement After Credential Access

A classic Falcon lateral movement pattern:

```
Initial host compromise
→ LSASS credential access
→ Same credentials observed on multiple hosts
```

This sequence strongly indicates **active lateral movement**, even if:
- No malware is dropped
- No exploit is observed

---

## Key Takeaway

Lateral movement is not about exploiting vulnerabilities—it is about **abusing trust and credentials**.

Defenders must watch for:
- Identity reuse
- Contextual tool usage
- Cross-host behavior chains

Stopping lateral movement early is often the difference between a **contained incident** and a **full-domain compromise**.



---

**Source: 25.md**

## What Is Credential Dumping?

Credential dumping is the process of extracting authentication secrets—such as usernames, plaintext passwords, password hashes, and Kerberos tickets—from a compromised system. It typically occurs after an attacker has established a foothold and elevated privileges, enabling them to impersonate users and move laterally within a network.

In short:
> **Credential dumping steals the keys needed for privilege escalation and lateral movement.**

---

## Core Targets and Techniques

Attackers focus on locations where credentials are stored, cached, or processed.

### 1. LSASS Memory (Primary Target)

- The **Local Security Authority Subsystem Service (lsass.exe)** stores authentication material for logged-on users.
- This includes:
  - NTLM password hashes
  - Kerberos tickets (TGTs / service tickets)
  - Cached credentials
- Attackers attempt to read LSASS memory to extract reusable authentication artifacts.

---

### 2. Active Directory Database (Domain Controllers)

- On domain controllers, attackers target the **ntds.dit** database.
- This file contains password hashes for all domain users.
- Exporting it enables offline cracking or mass credential reuse.

---

### 3. Registry Hives

- Attackers may copy:
  - `SAM`
  - `SYSTEM`
- These hives allow extraction of local account password hashes for offline cracking.

---

### 4. Application Credential Stores

Additional common targets include:
- Web browsers (saved passwords)
- Windows Credential Manager
- Unsecured configuration files containing hardcoded credentials

---

## Model Answer (Interview-Grade)

> *"Credential dumping is the unauthorized extraction of authentication data from a system’s memory or storage. By accessing targets such as LSASS memory or the NTDS.dit database, attackers can obtain password hashes or Kerberos tickets without needing plaintext passwords. The primary objective is to enable lateral movement; once attackers possess reusable credentials, they can impersonate legitimate users and navigate the network, often bypassing MFA in certain scenarios."*

---

## Mock Incident Scenario

**Scenario:** An endpoint detection system generates a critical alert for "Unapproved LSASS Memory Access" on a financial analyst’s workstation.

### Observation

- A non-system process (e.g., `procdump.exe` or a renamed binary) opens a handle to `lsass.exe` with `ReadMemory` permissions.
- A `.dmp` file is created in a temporary directory.

### Triage Steps

1. **Privilege Check**  
   Confirm whether the source process ran with high integrity (Administrator or SYSTEM).

2. **Context Analysis**  
   Determine whether this followed suspicious login activity or privilege escalation.

3. **Timeline Review**  
   Look for immediate follow-on events such as:
   - Event ID 4624 (Type 3 network logons)
   - Authentication attempts to additional servers

### Result

- High-confidence true positive
- Host isolated immediately
- All credentials used on the system scheduled for urgent reset
- Investigation expands to potential lateral movement

---

## CrowdStrike Perspective

In CrowdStrike Falcon, credential dumping is treated as a **high-severity behavioral event**, even when no traditional malware signature is present.

---

## Common Credential Dumping Methods Observed in Falcon

### 1. LSASS Memory Access

- Suspicious handle access to `lsass.exe`
- Memory reads from sensitive processes
- Code injection attempts

---

### 2. Tool-Based Dumping

Common tools include:
- `mimikatz`
- `procdump.exe`
- `rundll32.exe` with suspicious arguments
- PowerShell-based dump scripts

---

### 3. Living-Off-the-Land Variants

Attackers may avoid obvious tools by abusing built-in components such as:
- `comsvcs.dll` MiniDump technique
- Task Manager dump functionality
- Debug privilege abuse

Falcon detects these behaviors based on:
- API-level telemetry
- Process access rights
- Privilege escalation attempts
- Correlated post-dump credential reuse

---

## Why Credential Dumping Is So Dangerous

Credential dumping enables:
- Privilege escalation
- Pass-the-hash attacks
- Pass-the-ticket attacks
- Domain compromise
- Large-scale ransomware deployment

The dump itself may be quiet and low-noise. The real damage typically occurs afterward during lateral movement and privilege expansion.

---

## Key Takeaway

Credential dumping is not the end goal—it is an **enabler technique**.

By extracting authentication material, attackers convert a single-host compromise into a broader identity-based attack against the entire environment.

Stopping credential dumping early often prevents full-domain compromise.



---

**Source: 26.md**

## Why Is NTLM Considered Risky?

NTLM (NT LAN Manager) is considered a high-risk authentication protocol because of its architectural weaknesses and legacy design. It relies on an outdated challenge-response mechanism that lacks modern protections such as strong mutual authentication and robust cryptographic safeguards.

In short:
> **NTLM enables authentication using reusable hashes, making credential theft and relay attacks significantly easier.**

---

## Model Answer (Interview-Grade)

> *"NTLM is considered risky because it uses an aging challenge-response authentication mechanism that lacks the security guarantees of Kerberos. One major weakness is its susceptibility to Pass-the-Hash (PtH) attacks—since NTLM hashes are unsalted and reusable, an attacker who extracts a hash from memory can authenticate to other systems without knowing the plaintext password. Additionally, NTLM is vulnerable to relay attacks because it does not strongly bind authentication to a specific server. It also lacks true mutual authentication, meaning a client cannot verify the legitimacy of the server it is communicating with, enabling man-in-the-middle attacks."*

---

## Core Architectural Weaknesses

### 1. Unsalted Hashing

- NTLM uses unsalted password hashes.
- Identical passwords produce identical hashes.
- This enables:
  - Rainbow table attacks
  - Easier offline cracking
  - Hash reuse across systems

Because the hash itself acts as the credential, possession equals authentication capability.

---

### 2. Pass-the-Hash (PtH)

NTLM authentication relies on password hashes instead of plaintext passwords.

If attackers extract NTLM hashes (commonly via LSASS dumping), they can:
- Authenticate to other systems
- Without cracking the password
- Without knowing the actual secret

This makes NTLM extremely dangerous in post-compromise scenarios.

---

### 3. NTLM Relay Attacks

NTLM does not cryptographically bind authentication to a specific target server.

Attackers can:
- Intercept an NTLM authentication request
- Relay it to another server
- Gain access in real time

This is especially dangerous when:
- SMB signing is disabled
- Internal services are misconfigured
- LLMNR/NBT-NS poisoning is possible

---

### 4. Lack of Mutual Authentication

Unlike Kerberos:
- NTLM validates only the client to the server
- It does not strongly validate the server to the client

This enables:
- Man-in-the-middle attacks
- Credential interception
- Lateral movement chains

Kerberos, by contrast, provides mutual authentication using Service Principal Names (SPNs).

---

### 5. Protocol Fallback Behavior

NTLM often appears due to fallback conditions:

- Target specified by IP address instead of hostname
- SPN resolution failure
- Legacy application dependencies
- Hybrid on-prem/cloud misconfigurations

Because NTLM is difficult to fully disable in mixed environments, attackers frequently encounter it during internal movement.

---

## Mock Incident Scenario

**Scenario:** A SOC analyst observes a spike in Event ID 4624 (Logon Type 3) using the NTLM authentication package across multiple servers.

### Observation

- Source workstation: `WS-Admin-01`
- Account: `Administrator`
- Multiple file servers receiving NTLM-based logons
- Systems are domain-joined (Kerberos expected)

### Triage

- Authentication package shows NTLM instead of Kerberos
- Activity originates from a single compromised workstation

### Investigation

- LLMNR poisoning identified
- Admin workstation sent NTLM response
- Attacker relayed authentication to servers with SMB signing disabled

### Result

- Unauthorized lateral movement achieved
- Remote sessions established without password compromise

---

## CrowdStrike Perspective

In CrowdStrike Falcon, NTLM abuse is commonly observed during **post-compromise lateral movement**.

---

### 1. Pass-the-Hash Detection Pattern

Falcon often correlates:

```
LSASS access
→ NTLM authentication attempts from same host
→ Lateral movement indicators
```

Even if no malware is present, this behavior chain is high risk.

---

### 2. NTLM Relay Abuse

Falcon identifies suspicious NTLM-based authentication when:
- The source host is already compromised
- NTLM is used where Kerberos is expected
- Authentication appears across multiple systems rapidly

---

### 3. Identity Risk Amplification

NTLM enables:
- Credential replay
- Privilege escalation
- Domain compromise
- Ransomware deployment at scale

Often, NTLM activity itself is quiet. The damage occurs during the subsequent lateral movement.

---

## Key Takeaway

NTLM is risky because it treats reusable hashes as authentication tokens, lacks strong mutual authentication, and is vulnerable to relay and replay attacks.

In modern environments, NTLM should be:
- Restricted where possible
- Monitored aggressively
- Replaced with Kerberos wherever feasible

NTLM persistence in enterprise networks makes it a favored tool for attackers during identity-based attacks.



---

**Source: 27.md**

## What Is Pass-the-Hash?

Pass-the-Hash (PtH) is a lateral movement technique where an attacker uses a stolen NTLM password hash to authenticate to another system **without knowing or cracking the actual password**.

In Windows environments, the NT hash is effectively the secret used during NTLM authentication. Because the hash itself is accepted during authentication, possession of the hash is functionally equivalent to possessing the plaintext password.

In short:
> **If you have the NTLM hash, you have the credential.**

---

## Model Answer (Interview-Grade)

> *"Pass-the-Hash is a technique adversaries use to move laterally by leveraging stolen hashed credentials. Windows stores NTLM hashes in memory to support Single Sign-On (SSO), meaning the hash itself can be reused for authentication. After gaining local administrator or SYSTEM privileges on a compromised host, attackers dump LSASS memory to extract password hashes. They then reuse those hashes to authenticate to other systems—especially in environments where local administrator passwords are reused across multiple machines."*

---

## Core Mechanics of Pass-the-Hash

### 1. Hash Extraction (Credential Access)

Attackers first need elevated privileges on a system.

They typically:
- Access `lsass.exe` memory
- Dump credential material
- Extract NTLM hashes

This requires:
- Local administrator or SYSTEM privileges

Hashes are stored in memory to support Single Sign-On (SSO).

---

### 2. NTLM-Based Authentication Reuse

NTLM authentication accepts the hash directly.

Attackers can:
- Authenticate to remote systems
- Without cracking the password
- Without ever seeing plaintext credentials

PtH is primarily an **NTLM-based attack vector**.

---

### 3. Credential Reuse Dependency

PtH is most effective when:
- The same local administrator password is reused
- Service account credentials are shared
- Privileged credentials are broadly distributed

Credential reuse dramatically increases blast radius.

---

## What Interviewers Listen For

- Understanding that hashes are stored in LSASS for SSO functionality
- Recognizing that local admin or SYSTEM privileges are required to dump memory
- Knowing PtH is tied to NTLM authentication
- Identifying credential reuse as a key enabler

---

## Mock Incident Scenario

**Scenario:** A SOC analyst detects an unusual Logon Type 3 (Network) event on a high-value file server.

### Evidence

- Event ID 4624
- Account: `LocalAdmin`
- Source: `WS-MKT-05`
- Authentication Package: NTLM (not Kerberos)

### Triage

1. **Authentication Context**  
   NTLM used where Kerberos would normally be expected.

2. **Behavioral Anomaly**  
   The marketing workstation should not use the `LocalAdmin` account to access a file server.

3. **Endpoint Correlation**  
   On `WS-MKT-05`, logs show suspicious access to `lsass.exe` minutes earlier (e.g., Sysmon Event ID 10).

### Conclusion

Confirmed Pass-the-Hash attack.

The attacker:
- Dumped the local admin hash
- Reused it to pivot to the file server
- Achieved lateral movement without cracking any password

---

## CrowdStrike Perspective

In CrowdStrike Falcon, Pass-the-Hash is identified through **behavior correlation**, not a single alert.

---

### Step 1: Credential Access

Falcon detects:
- Suspicious LSASS handle access
- Credential dumping behavior
- Privilege escalation patterns

---

### Step 2: Authentication Reuse

Shortly afterward:
- Same user authenticates to:
  - Multiple servers
  - From a workstation that does not normally initiate admin access
- Authentication method: NTLM

---

### Step 3: Lateral Execution

Then:
- `psexec.exe`, `wmic.exe`, or `sc.exe` activity
- Remote service creation
- Remote command execution

Classic sequence:

```
LSASS access
→ NTLM authentication from compromised host
→ Remote service execution
```

Falcon flags this chain as high-confidence lateral movement.

---

## Why Pass-the-Hash Is So Dangerous

1. No password cracking required  
2. Works immediately after hash theft  
3. Hard to detect if only monitoring login success  
4. Enables:
   - Privilege escalation
   - Domain compromise
   - Ransomware deployment

---

## Key Takeaway

Pass-the-Hash converts a single compromised machine into a launch point for broader network compromise.

The real risk is not the hash theft itself—it is the rapid identity reuse and lateral movement that follows.



---

**Source: 28.md**

## Why Does MFA Not Fully Prevent Compromise?

### Model Answer (Interview‑Grade)

Multi‑Factor Authentication (MFA) significantly reduces the risk of unauthorized access by requiring multiple verification methods, but it is not a complete defense against compromise. MFA primarily protects the **authentication step**, while many modern attacks occur **after authentication or around it**.

Attackers increasingly bypass MFA by stealing session tokens, exploiting human behavior, intercepting codes, or abusing already‑authenticated systems.

---

## Core Ways MFA Is Bypassed

### 1. Session Hijacking (Pass‑the‑Cookie / Token Theft)

After MFA succeeds, applications issue session cookies or tokens.

If attackers steal these tokens they can:

- Access the application
- Skip the login portal
- Avoid MFA prompts entirely

Common sources of token theft:

- Browser session extraction
- Malware stealing cookies
- Network interception

Key concept:

> MFA protects the login event, not the session afterward.

---

### 2. MFA Fatigue (Push Bombing)

Attackers who already possess credentials repeatedly trigger MFA push notifications.

Goal:

- Annoy or confuse the user
- Pressure them into approving a request

Typical pattern:

1. Password is compromised
2. Repeated MFA push requests occur
3. User eventually approves

Once approved, attackers gain full account access.

MITRE ATT&CK:

**T1621 – Multi‑Factor Authentication Request Generation**

---

### 3. Phishing and Social Engineering

Attackers can trick users into entering both:

- Password
- One‑time MFA code

Attack flow:

1. Victim visits phishing site
2. Victim enters credentials
3. Victim enters MFA code
4. Attacker relays credentials to real service

MITRE ATT&CK:

**T1566 – Phishing**

---

### 4. SMS Interception (SIM Swapping)

SMS‑based MFA can be intercepted by taking control of the victim's phone number.

Common technique:

**SIM Swap Attack**

Steps:

1. Attacker convinces telecom provider to port the number
2. Victim's phone number moves to attacker SIM
3. MFA SMS codes are delivered to attacker

This allows full login access.

---

### 5. Post‑Exploitation Credential Reuse

Once attackers compromise a machine they can extract authentication material from memory.

Examples:

- Kerberos tickets
- NTLM hashes

Attack techniques include:

- Pass‑the‑Hash
- Pass‑the‑Ticket

These techniques allow lateral movement **without triggering MFA** because authentication already occurred.

MITRE ATT&CK:

- **T1558 – Steal or Forge Kerberos Tickets**
- **T1550 – Use Alternate Authentication Material**

---

## What Interviewers Listen For

Strong answers highlight several important concepts:

#### Authentication vs Session

MFA protects authentication, but **session tokens become the new credential afterward**.

#### Human Factors

Security systems still rely on users.

Examples:

- MFA fatigue
- Phishing approval

#### Protocol Limitations

Some authentication mechanisms do not support MFA well.

Examples:

- NTLM
- Legacy VPN systems

#### Post‑Exploitation Movement

Attackers often bypass MFA by stealing authentication artifacts from memory.

---

## MITRE ATT&CK Techniques

Common techniques associated with MFA bypass include:

- **T1621 – MFA Request Generation (Push Spam)**
- **T1550.004 – Web Session Cookie Theft**
- **T1556 – Modify Authentication Process**
- **T1558 – Kerberos Ticket Theft**
- **T1566 – Phishing**

---

## Mock Incident Scenarios

### Scenario 1: MFA Fatigue Attack

**Incident**

An attacker obtains valid credentials and repeatedly triggers MFA push notifications late at night.

The user eventually clicks **Approve**.

**SOC Detection**

- Multiple denied MFA prompts
- Followed by a successful login
- Login from unusual IP

**Response**

- Terminate session
- Disable account
- Revoke tokens
- Force password reset

---

### Scenario 2: Session Token Theft

**Incident**

Malware on the user's device extracts browser session cookies.

The attacker imports the cookie into their browser and gains direct access to cloud services.

**SOC Detection**

- Impossible travel
- Unrecognized device
- New location login

**Response**

- Invalidate sessions
- Revoke OAuth tokens
- Investigate endpoint compromise

---

### Scenario 3: SIM Swap Attack

**Incident**

An attacker convinces a telecom provider to port the victim's phone number.

The attacker receives MFA SMS codes and logs into the victim's VPN.

**SOC Detection**

- Login from unusual ASN or location

**Response**

- Disable account
- Revoke VPN access
- Move user to stronger MFA method

Examples:

- Authenticator app with number matching
- Hardware security key

---

## CrowdStrike Perspective

From a CrowdStrike Falcon and identity‑threat perspective, MFA blocks basic credential theft but does not stop modern identity attacks.

---

### 1. Session Token Theft

Common Falcon investigation pattern:

```
Endpoint compromise
→ browser token theft
→ cloud login without MFA
```

---

### 2. Adversary‑in‑the‑Middle (AiTM) Phishing

Reverse proxy phishing frameworks capture:

- Credentials
- MFA session cookies

Tools used:

- Evilginx
- Modlishka
- Phishing proxy kits

The victim completes MFA, but the attacker steals the authenticated session.

---

### 3. MFA Fatigue Attacks

Repeated push notifications are generated until a user approves one.

Once approved, attackers gain full access.

---

### 4. Compromised Endpoints

MFA protects login, not endpoint control.

If a device is compromised attackers can:

- Execute commands
- Access authenticated sessions
- Perform actions under the user's identity

Falcon often observes:

```
Endpoint malware
→ browser token access
→ cloud activity as legitimate user
```

---

### 5. Legacy Protocol Abuse

Some protocols bypass MFA entirely.

Examples:

- NTLM authentication
- Legacy email protocols
- Older VPN authentication

Attackers intentionally target these gaps.

---

## Key Takeaway

MFA significantly improves security but does not eliminate compromise risk.

It protects the **authentication step**, while many attacks exploit:

- session tokens
- user behavior
- compromised endpoints
- legacy authentication protocols

Effective defense requires **endpoint security, identity monitoring, session control, and phishing‑resistant MFA methods** in addition to MFA itself.



---

**Source: 29.md**

## Detecting Account Compromise: Logs That Matter

> **TL;DR** — Account compromise is detected by correlating identity activity with endpoint behavior and lateral movement across multiple log sources. No single log tells the full story.

---

### Overview

Account compromise doesn't announce itself. Attackers try to blend in — using valid credentials, legitimate tools, and normal-looking traffic. Detection requires connecting dots across **authentication**, **endpoint**, **network**, and **directory** layers.

---

### The Four Log Categories

#### 1. 🖥️ Endpoint Logs — *Highest Signal, Earliest Indicator*

Endpoint telemetry often catches compromise before any other source fires. Look for:

- `powershell.exe`, `cmd.exe`, LOLBins executing in unusual contexts
- **LSASS access** — credential dumping attempts (e.g., Mimikatz)
- User context changes mid-session
- Token usage anomalies

**Classic kill chain pattern:**

```
powershell.exe → LSASS access → new logins from different host
```

This sequence strongly suggests **credential theft → reuse**.

---

#### 2. 🔑 Authentication Logs — *Identity Confirmation*

Sources: Active Directory, Azure AD / Entra ID, VPN, SSO platforms

Watch for:

| Indicator | Significance |
|---|---|
| Logins from new geographies | Possible credential reuse |
| Impossible travel | Account shared or session token stolen |
| Failed logins → successful login | Brute force success |
| MFA anomalies or bypasses | Push fatigue or SIM swap |
| NTLM authentication spikes | Pass-the-Hash attempts |

---

#### 3. 🌐 Network Logs — *Movement & Reach*

Sources: Firewall, proxy, VPN, NDR tools

Watch for:

- **RDP / SMB / WinRM** connections between internal hosts
- Same account accessing multiple hosts in rapid succession
- Access to systems the account has never touched before
- Internal authentication flows at unusual hours

**Lateral movement signature:** One account → many hosts → short timeframe

---

#### 4. 📁 Directory / IAM Logs — *Privilege & Persistence*

Sources: AD event logs, Azure AD audit logs, PAM tools

Watch for:

- Group membership changes (especially `Domain Admins`, `Global Admins`)
- Account creation or modification by unexpected users
- Privilege escalation events
- Service account usage from interactive sessions

**Critical signal:** User added to `Domain Admins` outside of a change window

---

#### 5. ☁️ Cloud / SaaS Logs

Sources: Microsoft 365, Google Workspace, AWS CloudTrail, Azure Monitor

Watch for:

- Token reuse across unusual IP ranges
- Suspicious OAuth app consent grants
- API calls without MFA
- Mailbox delegation or forwarding rule creation

---

### CrowdStrike Falcon Perspective

In Falcon, account compromise detection is not about a single alert — it's about **correlation across telemetry streams**.

Falcon's Threat Graph links:

- Process executions with user context
- Credential access events
- Network connections initiated post-compromise
- Cross-host activity from the same identity

**Falcon detection model:** IOA (Indicator of Attack) over IOC — it catches *behavioral patterns* like credential access chains, not just known-bad hashes.

> A Mimikatz signature may be blocked, but `lsass.exe` being read by an unsigned process under a service account context will still trigger a behavioral detection.

---

### SIEM Correlation Logic

In Splunk / Sentinel / ArcSight, a strong account compromise detection rule combines:

```
auth_failure(count > 5) 
  → auth_success (same account) 
  → process_exec(lolbin) 
  → new_lateral_connection
```

All within a short rolling window (e.g., 30–60 minutes) = **high-confidence compromise alert**.

---

### Interview Cheat Sheet

| What interviewers want to hear | Red flags |
|---|---|
| Correlation across multiple sources | "Just check the login logs" |
| Endpoint as early signal | Only mentioning SIEM |
| Behavioral patterns, not just log names | No mention of endpoint telemetry |
| Identity + endpoint + network together | Treating log types as isolated |

**Strong answer framing:**

> "I'd start with endpoint telemetry for early signals — credential access, LOLBin execution, user context changes. Then correlate with authentication logs for impossible travel or MFA anomalies, and network logs for lateral movement. Directory logs confirm if the attacker escalated privilege or established persistence. In CrowdStrike, the Threat Graph connects all of this automatically."

---

### Quick Reference

```
Endpoint logs     → Earliest signal (credential access, LOLBins)
Auth logs         → Identity anomalies (impossible travel, MFA bypass)
Network logs      → Lateral movement (RDP, SMB, WinRM)
Directory logs    → Privilege escalation, persistence
Cloud/SaaS logs   → Token abuse, OAuth grants
```

---

*Tags: `account-compromise` `blue-team` `detection` `crowdstrike` `SIEM` `incident-response`*


---

**Source: 30.md**

## Principle of Least Privilege (PoLP): A Defender's Playbook

> **TL;DR** — Least privilege is about limiting what an attacker can do *after* compromise. It doesn't stop breaches — it contains them.

---

### What Is Least Privilege?

The Principle of Least Privilege (PoLP) dictates that users, processes, and systems should only be granted the **minimum level of access necessary** to perform their assigned tasks — nothing more, nothing permanent.

In practice, this means:

- Limiting admin rights by default
- Restricting access to only necessary systems and data
- Using temporary or Just-in-Time (JIT) access
- Continuously reviewing and removing excess privileges

**Core goal:** Reduce the *blast radius* if an account is compromised.

---

### Core Implementations

#### 🔀 Separation of Accounts

Administrators should maintain at least **two accounts**:

| Account Type | Used For |
|---|---|
| Standard (non-privileged) | Email, web browsing, daily tasks |
| Privileged (admin) | Administrative functions only |

> ⚠️ Microsoft's UAC is **not** an adequate substitute for this separation.

---

#### 🖥️ Secure Admin Workstations (SAW / PAW)

Privileged credentials should **never** be entered on general-purpose workstations. Use dedicated, hardened systems:

- Heavily monitored
- Restricted from internet access and high-risk activities
- Isolated from standard user environments

A compromised general workstation with cached admin credentials is a direct path to Domain Admin.

---

#### ⚙️ Just Enough Administration (JEA)

PowerShell JEA provides **granular, role-based access** — allowing users to run specific cmdlets without full administrator rights.

```powershell
# Example: Grant access to restart a specific service only
# User can restart IIS — nothing else
Register-PSSessionConfiguration -Name 'RestartIIS' -RunAsCredential $cred
```

Result: Task gets done. No standing admin session. No credential exposure.

---

#### 🐧 Linux Capabilities

Linux no longer requires a binary choice between unprivileged and full root. Modern practice uses **capabilities** to grant a process only what it needs:

```bash
# Grant only the ability to bind to low ports — no full root
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/myapp
```

This eliminates the "run as root or don't run" tradeoff.

---

#### 🏗️ Tiered Administrative Model

| Tier | Admin Scope | Cannot Touch |
|---|---|---|
| Tier 0 | Domain Controllers | Servers, Workstations |
| Tier 1 | Servers | Domain Controllers, Workstations |
| Tier 2 | Workstations | Servers, Domain Controllers |

A workstation compromise **stays in Tier 2** — no direct escalation path to the identity core.

---

### Interview Model Answer

> *"In practice, least privilege means moving away from standing broad permissions to a model where access is limited by role, time, and scope. For end users, this means operating as a standard account by default — malware cannot install itself or modify system settings. For administrators, it means using dedicated workstations (SAWs) and tools like PowerShell JEA to perform specific tasks without exposing a full Domain Admin credential in memory where it could be harvested by Mimikatz. Ultimately, if any single identity is compromised, the attacker finds themselves in a cul-de-sac with no immediate path to sensitive data or lateral movement."*

---

### CrowdStrike Falcon Perspective

In Falcon, least privilege directly determines the **severity and spread** of an incident — not just whether a detection fires.

#### Endpoint Impact

| Scenario | Attacker Capability |
|---|---|
| Standard user compromised | Cannot dump credentials, install services, or move laterally easily |
| Local admin compromised | Immediate high-risk — credential access, lateral movement viable |

Falcon analysts don't just ask *"Is this account compromised?"* — they ask **"What can this identity do?"**

---

#### Detection Clarity

Least privilege makes behavioral anomalies **stand out**:

```
Standard user → powershell.exe         ✅ Normal
Standard user → powershell → LSASS access  🚨 Highly suspicious
```

When privilege boundaries are enforced, abnormal privilege usage becomes an instant detection signal.

---

#### Identity & Access Context

Falcon investigations are cleaner when:

- Users are **not** local admins by default
- Service accounts have **scoped** permissions
- Admin access is **time-bound** (JIT)

Excess privilege creates noise — accounts doing things they shouldn't be able to do, making it harder to distinguish attacker activity from normal ops.

---

### Mock Incident: The Ransomware That Wasn't

**Scenario:** SOC detects malware executing on an HR employee's laptop.

**Attacker's attempt:**
```cmd
vssadmin.exe delete shadows
```

**Result:** `Access Denied`

**Why?** The HR employee was correctly configured as a **standard user**. The malware had no permissions to:
- Delete shadow copies
- Write to `C:\Windows\System32`
- Disable backup services

**Outcome:** Threat contained to a single user folder. Host isolated. No ransomware event — because the attacker couldn't achieve vertical privilege escalation.

---

### Mock Incident: Same Alert, Different Risk

**Falcon detects:** `powershell.exe → LSASS access attempt`

**Case A — Standard User:**
```
LSASS access → DENIED
Risk: Contained
```

**Case B — Local Admin:**
```
LSASS access → SUCCESS
Credentials extracted → Lateral movement begins
Risk: Critical
```

**Same alert. Completely different incident outcome.** Privilege level is the variable.

---

### MITRE ATT&CK Mapping

PoLP directly reduces the effectiveness of:

| Tactic | ID | How PoLP Helps |
|---|---|---|
| Privilege Escalation | TA0004 | No standing rights to escalate from |
| Lateral Movement | TA0008 | Limited access to other systems |
| Credential Access | TA0006 | Standard users can't access LSASS |
| Impact | TA0040 | Cannot delete backups or encrypt drives |

> PoLP doesn't prevent attacks — it limits their success and spread.

---

### What Interviewers Listen For

| Strong Signal | Red Flag |
|---|---|
| Mentions blast radius reduction | "Users should have limited access" (too vague) |
| References JIT access / time-bound privileges | No mention of privilege escalation risk |
| Connects PoLP to incident impact | Treats it as compliance-only |
| Understands it as operational control | Only knows the definition |
| Mentions LAPS, JEA, Linux capabilities | Generic answer with no technical depth |

---

### Quick Reference

```
PoLP in one line:
"If compromised, what can the attacker actually do?"

Key controls:
  → Separate admin/standard accounts
  → SAW/PAW for privileged access
  → JEA for task-scoped administration
  → Tiered admin model
  → JIT access — no standing privileges
  → Linux capabilities over full root

Detection benefit:
  → Privilege violations become high-fidelity signals
```

---

*Tags: `least-privilege` `PoLP` `blue-team` `crowdstrike` `privilege-escalation` `incident-response` `MITRE`*

