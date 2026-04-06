# CrowdStrike & Cloud Security — A Deep Dive
> A comprehensive technical guide covering Cloud Workloads, Falcon Sensor, Kernel Monitoring, and Cloud Workload Protection

---

## Table of Contents

1. [Cloud Workload Concepts — Images, Containers, Pods & More](#1-cloud-workload-concepts)
2. [What is the Falcon Sensor?](#2-what-is-the-falcon-sensor)
3. [Channel File Updates — If No Signatures, Why Update?](#3-channel-file-updates)
4. [How Does the Sensor Handle Offline Protection?](#4-offline-protection)
5. [Kernel-Level Monitoring — The Deep Dive](#5-kernel-level-monitoring)
6. [CrowdStrike Cloud Workload Protection — All Components](#6-cloud-workload-protection)
7. [Where to Install What and How](#7-installation-guide)

---

## 1. Cloud Workload Concepts

### Image

A **container image** is a lightweight, standalone, executable package that includes everything needed to run a piece of software — code, runtime, libraries, environment variables, and config files.

- Think of it as a **blueprint or template**
- Built using a `Dockerfile`
- Stored in registries like **Docker Hub, AWS ECR, Azure Container Registry**
- Images are **immutable** — you don't change them, you rebuild them
- Example: `ubuntu:22.04`, `nginx:latest`

> **Security concern:** Vulnerable base images are a common attack vector — this is where tools like **CrowdStrike Falcon Image Assessment** come in.

---

### Container

A **container** is a **running instance of an image** — isolated processes on a host OS sharing the same kernel.

- Lightweight compared to VMs (no full OS per instance)
- Uses **namespaces** (isolation) and **cgroups** (resource limits)
- Managed by runtimes like **Docker, containerd, CRI-O**
- Ephemeral by nature — can be stopped, replaced, restarted

> **Security concern:** Container escape, privilege escalation, and runtime threats — monitored by **CrowdStrike Falcon for Containers**.

---

### Cluster

A **Kubernetes cluster** is a set of machines (nodes) that run containerized workloads, managed by Kubernetes.

| Component | Role |
|---|---|
| **Control Plane** | Manages the cluster (API server, scheduler, etcd) |
| **Worker Nodes** | Where your actual workloads (pods) run |

- You interact with a cluster via `kubectl`
- Multiple clusters can exist per environment (dev, staging, prod)

---

### Pod

A **Pod** is the **smallest deployable unit in Kubernetes** — a wrapper around one or more containers that share:

- The same **network namespace** (same IP)
- The same **storage volumes**
- The same **lifecycle**

Pods are **ephemeral** — if a pod dies, Kubernetes spins up a new one. Usually managed by higher-level objects (Deployments, StatefulSets).

> **Security concern:** Lateral movement between pods, over-privileged pods, and inter-pod traffic — monitored via **network policies and runtime security**.

---

### Other Important Concepts

| Concept | Description |
|---|---|
| **Namespace** | Logical isolation within a cluster. Separates workloads by team/environment |
| **Deployment** | Defines desired state for a set of pods. Kubernetes maintains this state |
| **Service** | Provides a stable network endpoint to access pods |
| **Ingress** | Manages external HTTP/HTTPS traffic routing — essentially a reverse proxy |
| **ConfigMap & Secret** | Store config data and sensitive data separately from the container image |
| **Persistent Volume (PV)** | Storage that outlives a pod's lifecycle, used for stateful applications |
| **Node** | A physical or virtual machine in the cluster running a kubelet and container runtime |

---

## 2. What is the Falcon Sensor?

The **Falcon Sensor** is a lightweight agent installed on endpoints (Windows, Linux, macOS, containers) that serves as the **data collection and enforcement engine** for the entire CrowdStrike Falcon platform.

It is the **"eyes and ears"** on the endpoint — everything CrowdStrike does flows through it.

### How It Works

```
Endpoint Activity
      ↓
Falcon Sensor (collects telemetry)
      ↓
CrowdStrike Cloud (AI/ML analysis)
      ↓
Detection / Prevention / Response
```

- The sensor is **kernel-level** — it hooks into the OS at a deep level
- Sends telemetry to the **Falcon cloud** in real time
- Very **lightweight** — designed for minimal performance impact
- Does **NOT require signature updates** (cloud-native, unlike legacy AV)

---

### Key Functions of the Falcon Sensor

#### 1. Telemetry Collection
Collects raw system activity:
- Process creation and termination
- Network connections
- File system changes
- Registry modifications (Windows)
- User logon/logoff events
- DNS queries

#### 2. Prevention (NGAV)
- Blocks known malware using **ML models**
- Blocks unknown threats using **behavioral AI**
- Works **on-sensor** — even offline, without cloud connectivity

#### 3. Detection (EDR)
- Records everything for **threat hunting**
- Raises detections based on **IOAs (Indicators of Attack)**
- Sends alerts to Falcon console for analyst review

#### 4. Firewall Management
- Enforces host-based firewall rules pushed from Falcon console
- Replaces need for managing Windows Firewall manually

#### 5. Real Time Response (RTR)
- Allows live remote shell access to endpoint
- Run commands, pull files, kill processes — all from Falcon console
- Used for incident response and threat hunting

---

### Sensor Deployment Policies

| Policy Type | Purpose |
|---|---|
| **Sensor Update Policy** | Controls which sensor version is deployed, rollout pace |
| **Prevention Policy** | Configures what actions sensor blocks vs detects |
| **Firewall Policy** | Defines host firewall rules per group |
| **Device Control Policy** | Controls USB/removable media access |
| **Containment Policy** | Network isolation during incident response |

---

### Sensor on Different Platforms

| Platform | Sensor Type | Notes |
|---|---|---|
| **Windows** | `.exe` installer | Kernel driver, runs as service |
| **Linux** | `.rpm` / `.deb` | Supports major distros |
| **macOS** | `.pkg` | System extension based |
| **Containers** | Daemonset on Kubernetes node | Protects all pods on that node |
| **Cloud VMs** | Same as OS-based | AWS, Azure, GCP supported |

---

### Exclusions Tuning

| Exclusion Type | Purpose |
|---|---|
| **IOA Exclusions** | Exclude specific behavioral patterns that are legitimate but trigger detections |
| **ML Exclusions** | Exclude files/paths from Machine Learning analysis to reduce false positives |
| **Sensor Visibility Exclusions (SVE)** | Reduce telemetry noise from known-good processes |

> ⚠️ These require careful tuning — too broad an exclusion creates security gaps, too narrow causes alert fatigue.

---

## 3. Channel File Updates

### Traditional AV Signatures vs Channel Files

| | Traditional AV Signatures | CrowdStrike Channel Files |
|---|---|---|
| **What they contain** | Known malware hashes/patterns | Behavioral detection logic & IOA rules |
| **What they match against** | File hashes | Process behavior, attack patterns |
| **Purpose** | "Is this file malicious?" | "Is this behavior an attack?" |
| **Catches** | Known malware only | Known AND unknown attacks |

---

### So What ARE Channel Files?

Channel Files are **configuration and logic updates** pushed to the sensor. They contain:

**1. IOA (Indicator of Attack) Rules**
- Define behavioral patterns that indicate an attack
- Example: *"If PowerShell spawns from Word and makes a network connection → flag it"*
- Need updating as new attack techniques emerge

**2. ML Model Parameters**
- Fine-tuning parameters for the on-sensor AI models
- Not the full model — just calibration updates

**3. Sensor Behavior Configuration**
- How aggressively to monitor certain activities
- Which system events to capture and how

**4. Telemetry Collection Rules**
- What data to collect from the endpoint
- Which process behaviors to watch closely

---

### Simple Analogy

```
Traditional AV = Wanted Posters (recognize known criminals by face)

Falcon Sensor  = Trained Detective (recognizes criminal BEHAVIOR)

Channel Files  = Updated Training Manual for the Detective
                 (new techniques criminals are using,
                  refined interrogation methods)
```

---

### The July 2024 Incident

A real-world example of channel file impact:

- CrowdStrike pushed an update to **Channel File 291** (handles named pipe IOA logic on Windows)
- A **logic error** in the new IOA rule caused the sensor to read out-of-bounds memory
- This triggered a kernel panic → **Blue Screen of Death (BSOD)**
- Affected **8.5 million Windows machines** globally
- Had nothing to do with signatures — it was a **behavioral rule logic error**

---

### Update Frequency

| Update Type | Frequency | Method |
|---|---|---|
| **Channel Files** | Multiple times per day | Automatic, silent |
| **Sensor version** | Controlled by Sensor Update Policy | You control rollout |
| **Cloud AI Models** | Continuous | Entirely cloud-side, no endpoint impact |

---

## 4. Offline Protection

### Core Principle

```
Online  = Full Power (Sensor + Cloud AI + Real-time threat intel)
Offline = Reduced but Meaningful Protection (On-sensor ML + Cached IOAs)
```

---

### What Protects the Endpoint When Offline?

#### 1. On-Sensor Machine Learning (ML)
This is the **primary offline defense** — ML models are embedded directly into the sensor.

| ML Layer | What it does |
|---|---|
| **Static Analysis** | Analyzes file attributes before execution |
| **Behavioral Analysis** | Monitors process behavior during execution |

#### 2. Cached IOA Rules (Channel Files)
- IOA behavioral rules from Channel Files are **cached locally**
- Sensor continues enforcing these rules without cloud connection
- Cache persists until new Channel File update is received when back online

#### 3. Prevention Policies (Local Enforcement)

| Prevention Setting | Offline Behavior |
|---|---|
| **Suspicious Processes** | Still blocked locally |
| **Ransomware Protection** | Still active |
| **Exploit Mitigation** | Still enforced |
| **Malicious Files** | Still blocked via on-sensor ML |

#### 4. Host Firewall Rules
- Firewall policies are **fully cached locally**
- All firewall rules continue to enforce without cloud

---

### What You LOSE Offline

| Capability | Offline Status | Why |
|---|---|---|
| **Real-time cloud AI analysis** | ❌ Unavailable | Needs cloud for correlation |
| **Threat Graph correlation** | ❌ Unavailable | Cross-customer intel is cloud-side |
| **Real Time Response (RTR)** | ❌ Unavailable | Needs cloud tunnel |
| **New IOA rule updates** | ❌ Paused | Channel files can't be pushed |
| **Falcon Spotlight (vuln mgmt)** | ❌ Unavailable | Cloud dependent |
| **Detection uploads** | ⏸️ Queued | Sent when back online |
| **Telemetry streaming** | ⏸️ Queued | Buffered locally, synced later |

---

### Telemetry Buffering

```
Endpoint goes offline
        ↓
Sensor continues collecting all events locally
        ↓
Buffer fills up to storage limit
        ↓
Endpoint comes back online
        ↓
Buffered telemetry uploads to Falcon cloud
        ↓
Threat hunting & detection analysis runs retroactively
```

> ⚠️ If the buffer fills up before reconnecting, oldest events get dropped — prolonged offline periods create visibility gaps.

---

### RFM — Reduced Functionality Mode

**RFM triggers when:**
- Sensor cannot reach Falcon cloud for extended period
- Sensor license expires
- Incompatible kernel detected (Linux)

```bash
# Check RFM state on Linux
sudo /opt/CrowdStrike/falconctl -g --rfm-state
```

**In RFM:**
- On-sensor ML still runs ✅
- IOA enforcement continues (cached) ✅
- Cloud-dependent features disabled ❌
- Console shows endpoint as **"RFM"** status

---

## 5. Kernel-Level Monitoring

### Why Kernel Level?

```
┌─────────────────────────────────────┐
│           USER SPACE (Ring 3)       │
│   Apps, Browsers, Malware, AV...    │
│   Limited OS access, easier to fool │
├─────────────────────────────────────┤
│           KERNEL SPACE (Ring 0)     │
│   OS Core, Drivers, Hardware access │
│   Complete system visibility        │
│   ← Falcon Sensor lives here        │
└─────────────────────────────────────┘
```

Running at kernel level means:
- **Sees everything** before userspace tools can hide it
- **Cannot be easily bypassed** by malware running in userspace
- **First to know** about any system activity
- Malware **cannot hide from it** using userspace rootkit techniques

---

### How the Sensor Hooks Into the Kernel

#### Windows — ETW + Minifilter Driver

**1. ETW (Event Tracing for Windows)**
- Built-in Windows kernel telemetry framework
- Falcon subscribes to ETW providers for process creation, network activity, registry changes, memory allocation events

**2. Minifilter Driver**
- Sits in the **file system filter stack**
- Intercepts all file I/O operations
- Can **allow, block, or modify** file operations in real time
- How Falcon catches ransomware encrypting files

**3. Kernel Callbacks**

| Callback | What it monitors |
|---|---|
| `PsSetCreateProcessNotifyRoutine` | Every process creation |
| `PsSetCreateThreadNotifyRoutine` | Every thread creation |
| `PsSetLoadImageNotifyRoutine` | Every DLL/driver load |
| `CmRegisterCallback` | Registry operations |
| `ObRegisterCallbacks` | Object handle operations |

---

#### Linux — eBPF + Kernel Modules

**eBPF (Extended Berkeley Packet Filter) — Modern Approach**

```
System Call Made by Process
          ↓
    eBPF Program Intercepts
          ↓
    Telemetry Collected
          ↓
    Sent to Falcon Sensor
          ↓
    Forwarded to Cloud
```

- Runs **safely inside kernel** without modifying kernel code
- Extremely **low overhead**
- Cannot crash the kernel (verified by eBPF verifier)

**Kernel Module — Legacy/Fallback**
- Traditional loadable kernel module (LKM)
- Used on older kernels that don't support eBPF
- Incompatible kernel = RFM mode

---

### What the Kernel Sensor Monitors

#### Process Monitoring

```
Parent Process spawns Child Process
              ↓
Sensor captures at kernel level:
  - Full command line arguments
  - Parent-child relationship
  - User context (who ran it)
  - Integrity level
  - Memory permissions requested
  - DLLs loaded into process
```

Catches: **Living off the Land (LotL)** attacks, **Process injection**, **Hollow process** attacks

#### Network Monitoring

| What's Captured | Why It Matters |
|---|---|
| DNS queries (pre-resolution) | Catches DNS tunneling |
| Raw socket connections | Catches custom protocol C2 |
| Connection metadata | Source/dest IP, port, process |
| HTTP headers (pre-encryption context) | Catches some C2 patterns |

#### File System Monitoring

- Every **file create, modify, delete, rename**
- File **entropy analysis** — high entropy = possible encryption (ransomware)
- **Shadow copy deletion** attempts — classic ransomware behavior
- Executable files written to **unusual locations**

#### Memory Monitoring

| Technique Detected | How Kernel Monitoring Catches It |
|---|---|
| **Process Injection** | Detects VirtualAllocEx + WriteProcessMemory + CreateRemoteThread sequence |
| **Reflective DLL Injection** | Detects DLL loaded without hitting disk |
| **Process Hollowing** | Detects legitimate process with replaced memory |
| **AMSI Bypass** | Detects memory patches to amsi.dll |
| **Credential Dumping** | Detects LSASS memory reads |

---

### Kernel vs Userspace — Fileless Malware Example

```
❌ Traditional Userspace AV:
Malware runs entirely in memory
→ No file written to disk
→ AV never scans it
→ Malware runs undetected

✅ Falcon Kernel Sensor:
Malware runs in memory
→ Kernel sees process creation
→ Kernel sees memory allocations
→ Kernel sees network connections
→ Behavioral IOA triggers
→ Blocked and alerted
```

---

### The July 2024 Incident — Kernel Context

- Channel File 291 updated **named pipe IOA logic** monitored at **kernel level**
- Logic error caused sensor to access **out-of-bounds kernel memory**
- Kernel memory access violations = **immediate system crash (BSOD)**
- Required **manual intervention per machine** — no remote recovery possible

This is the double-edged sword of kernel-level access:
- **More powerful** detection capability
- **Higher blast radius** when something goes wrong

---

## 6. Cloud Workload Protection — All Components

CrowdStrike's cloud security falls under the **Falcon Cloud Security** umbrella:

```
┌─────────────────────────────────────────────────────┐
│              FALCON CLOUD SECURITY                  │
│                                                     │
│  CWPP  │  CSPM  │  CIEM  │  CNAPP  │  CAS  │  CDR  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Component 1 — CWPP (Cloud Workload Protection Platform)

**Runtime protection layer** — protecting what's actually running.

#### For Virtual Machines (VMs)

| Feature | What it does |
|---|---|
| **Falcon Prevent (NGAV)** | Blocks malware on cloud VMs |
| **Falcon Insight (EDR)** | Full telemetry from cloud instances |
| **Falcon Firewall** | Host-based firewall on cloud VMs |
| **RTR** | Live remote response into cloud instances |
| **Spotlight** | Vulnerability management on cloud VMs |

Supports: AWS EC2, Azure VMs, GCP Compute Engine, On-prem VMs

#### For Containers

**Falcon Container Sensor**
- Deployed **inside** the container
- Per-container deep visibility
- Monitors process, network, file activity within container

**Falcon Node Sensor (DaemonSet)**
- Single sensor per **Kubernetes node**
- Protects **all containers** on that node
- Lower overhead at scale

#### Container Runtime Threat Detection

| Threat | How Falcon Detects It |
|---|---|
| **Container escape** | Detects syscalls attempting namespace breakout |
| **Privilege escalation** | Detects capability abuse inside container |
| **Cryptomining** | Detects mining process behavior and CPU patterns |
| **Lateral movement** | Detects unusual network connections between pods |
| **Fileless attacks** | Kernel-level memory monitoring inside container |
| **Reverse shells** | Detects shell spawned from unexpected parent |

---

### Component 2 — CSPM (Cloud Security Posture Management)

Continuously scans your cloud accounts for **misconfigurations**:

```
Your Cloud Account (AWS/Azure/GCP)
          ↓
Falcon CSPM scans all resources
          ↓
Checks against security benchmarks
  - CIS Benchmarks / NIST / PCI-DSS / HIPAA / SOC2
          ↓
Raises findings with severity scores
```

#### Examples of What CSPM Catches

| Misconfiguration | Risk |
|---|---|
| S3 bucket publicly accessible | Data exposure |
| Security group allows 0.0.0.0/0 on port 22 | SSH open to internet |
| RDS instance without encryption | Data at rest exposed |
| CloudTrail logging disabled | No audit trail |
| MFA not enabled on root account | Account takeover risk |
| Secrets hardcoded in EC2 userdata | Credential exposure |
| Kubernetes API server publicly accessible | Cluster compromise |

---

### Component 3 — CIEM (Cloud Infrastructure Entitlement Management)

Focuses entirely on **identities and permissions** in cloud.

#### The Problem it Solves

```
Cloud environments have thousands of:
- IAM users / IAM roles / Service accounts / Federated identities

Most are OVER-PRIVILEGED
→ Attackers exploit excessive permissions
→ Blast radius of compromise is massive
```

#### What CIEM Does

| Feature | Description |
|---|---|
| **Permission analysis** | Maps every identity to every permission |
| **Effective permissions** | Shows what each identity CAN actually do |
| **Unused permissions** | Identifies permissions granted but never used |
| **Least privilege recommendations** | Suggests tighter policies |
| **Cross-account access mapping** | Finds risky trust relationships |
| **Privilege escalation paths** | Finds chains that lead to admin |

---

### Component 4 — CNAPP (Cloud Native Application Protection Platform)

CNAPP is the **unified umbrella** that combines:

```
CNAPP = CWPP + CSPM + CIEM + Image Scanning + IaC Scanning
```

Provides:
- **Unified risk scoring** across runtime + posture + identity
- **Attack path analysis** — connects misconfig → identity → runtime risk
- **Single pane of glass** for cloud security

---

### Component 5 — Falcon Image Assessment

Protects the **supply chain** — before containers even run.

#### Scanning Pipeline

```
Developer writes code
        ↓
Builds container image
        ↓
Falcon scans image in CI/CD pipeline ← HERE
        ↓
Checks for:
  - OS vulnerabilities (CVEs)
  - Application dependency vulnerabilities
  - Embedded secrets/credentials
  - Malware in image layers
  - Misconfigurations in Dockerfile
        ↓
Pass → Image pushed to registry
Fail → Build blocked, developer notified
```

#### Integration Points
- Jenkins, GitHub Actions, GitLab CI, AWS CodePipeline, Azure DevOps

#### Registry Scanning
- Docker Hub, AWS ECR, Azure Container Registry, Google Artifact Registry, JFrog Artifactory

---

### Component 6 — Kubernetes Admission Controller (KAC)

Acts as a **gatekeeper** for your Kubernetes cluster.

#### How it Works

```
Developer submits pod deployment
              ↓
Kubernetes API Server receives request
              ↓
Falcon Admission Controller intercepts ← HERE
              ↓
Checks pod spec against policies:
  - Is image from approved registry?
  - Does image have critical CVEs?
  - Is container running as root?
  - Are dangerous capabilities requested?
  - Is privileged mode requested?
              ↓
ALLOW or DENY the deployment
```

#### Example Policies

| Policy | Action |
|---|---|
| Image not from approved registry | Block deployment |
| Critical CVE in image | Block or warn |
| Container runs as root | Block |
| Privileged container requested | Block |
| Host network access requested | Warn |

#### The Three-Layer Container Defense Chain

```
Image Scanning          KAC                  CWPP Runtime
(Dev Phase)        (Deploy Phase)           (Runtime Phase)
     │                   │                       │
Catch CVEs          Block bad             Detect/Respond
before build        deployments           to live threats
     │                   │                       │
  PREVENT             PREVENT                 DETECT &
  at source          at gate                  RESPOND
```

---

### Component 7 — CAS (Cloud Application Security) / ASPM

- **API security** — discovers and monitors APIs
- **Secret scanning** — finds hardcoded credentials in code
- **Software composition analysis (SCA)** — open source dependency risks
- **DAST integration** — dynamic application testing

---

### Component 8 — CDR (Cloud Detection and Response)

The **SIEM/hunting layer** specifically for cloud.

Ingests: CloudTrail (AWS), Azure Activity Logs, GCP Audit Logs

#### Pre-built Cloud Attack Detections

| Attack Technique | CDR Detection |
|---|---|
| **IAM privilege escalation** | Detects role assumption chains |
| **S3 data exfiltration** | Detects mass GetObject calls |
| **EC2 cryptomining** | Detects unusual instance types launched |
| **Credential stuffing** | Detects failed login patterns |
| **Impossible travel** | API calls from geographically impossible locations |

---

### Component 9 — Falcon Horizon (CSPM Extended)

- **Multi-cloud support** — AWS, Azure, GCP in one view
- **Custom policies** — write your own compliance rules
- **Automated remediation** — auto-fix certain misconfigurations
- **Cloud asset graph** — visual relationship mapping of all resources

---

### Full Architecture Map

```
┌─────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT PHASE                        │
│  Code Scanning │ IaC Scanning │ Image Scanning │ SCA        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    DEPLOYMENT PHASE                         │
│       KAC │ Registry Scanning │ Policy Gates                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    RUNTIME PHASE                            │
│  CWPP (VM+Container) │ CDR │ Network Monitoring             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                 POSTURE & IDENTITY LAYER                    │
│          CSPM │ CIEM │ CNAPP │ Falcon Horizon               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    FALCON PLATFORM                          │
│     Threat Graph │ AI/ML │ Threat Intel │ OverWatch         │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Installation Guide

### Decision Tree — Install What?

```
What are you protecting?
│
├── Physical/Virtual Machine (Windows/Linux/Mac)
│         → Install Falcon Sensor (full agent)
│
├── Kubernetes Cluster
│         │
│         ├── On the NODE
│         │         → Install Falcon Node Sensor (DaemonSet)
│         │
│         ├── Inside CONTAINER
│         │         → Install Falcon Container Sensor
│         │
│         └── At CLUSTER GATE
│                   → Install KAC (Admission Controller)
│
├── Container IMAGE (before it runs)
│         → Integrate Falcon Image Assessment in CI/CD
│
├── Cloud ACCOUNT (AWS/Azure/GCP)
│         → Connect Falcon CSPM/Horizon (agentless)
│
└── Cloud IDENTITIES & PERMISSIONS
          → Connect Falcon CIEM (agentless, API based)
```

---

### 1. Standard Endpoints & Cloud VMs

**Install:** Falcon Sensor (standard agent)

```bash
# Linux
sudo apt install ./falcon-sensor_*.deb
sudo /opt/CrowdStrike/falconctl -s \
  --cid=YOUR_CID \
  --tags="cloud,production"
sudo systemctl start falcon-sensor

# Windows (silent install)
msiexec /i falcon-sensor.msi \
  CID=YOUR_CID \
  /quiet

# Verify
sudo systemctl status falcon-sensor
```

| Environment | Install Method |
|---|---|
| AWS EC2 | User Data script at launch |
| Azure VM | Custom Script Extension |
| GCP Compute | Startup script |
| On-prem VM | GPO / SCCM / Ansible |

---

### 2. Kubernetes — Node Level (DaemonSet)

**Install:** Falcon Node Sensor

```bash
# Add CrowdStrike Helm repo
helm repo add crowdstrike \
  https://crowdstrike.github.io/falcon-helm

# Install Node Sensor as DaemonSet
helm install falcon-sensor \
  crowdstrike/falcon-sensor \
  --namespace falcon-system \
  --create-namespace \
  --set falcon.cid=YOUR_CID \
  --set falcon.tags="kubernetes,production"

# Verify — should show one pod per node
kubectl get pods -n falcon-system
```

**When to use:** Standard EKS, AKS, GKE clusters where you want low overhead with one sensor covering all pods per node.

---

### 3. Kubernetes — Container Level

**Install:** Falcon Container Sensor

```bash
# Install Falcon Injector
helm install falcon-container \
  crowdstrike/falcon-container \
  --namespace falcon-system \
  --set falcon.cid=YOUR_CID
```

Injector automatically patches new pods via **mutating webhook**.

**When to use:**
- Need per-container deep visibility
- Running containers as root on nodes
- Managed Kubernetes where node access is restricted
- AWS Fargate (no node access at all)

---

### 4. Kubernetes — Admission Controller (KAC)

**Install:** Falcon Kubernetes Admission Controller

```bash
# Install KAC via Helm
helm install falcon-kac \
  crowdstrike/falcon-kac \
  --namespace falcon-kac \
  --create-namespace \
  --set falcon.cid=YOUR_CID

# Verify webhook is registered
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations
```

**Example policy enforced by KAC:**

```yaml
policies:
  - blockPrivilegedContainers: true
  - blockRootContainers: true
  - allowedRegistries:
      - registry.company.com
      - 123456789.dkr.ecr.us-east-1.amazonaws.com
  - blockCriticalCVEs: true
  - blockHighCVEs: false  # warn only
```

---

### 5. CI/CD Pipeline — Image Scanning

**GitHub Actions:**

```yaml
- name: Scan Container Image
  uses: crowdstrike/container-image-scan-action@v1
  with:
    container_repository: myapp
    container_tag: ${{ github.sha }}
    crowdstrike_region: us-1
    crowdstrike_client_id: ${{ secrets.CS_CLIENT_ID }}
    crowdstrike_client_secret: ${{ secrets.CS_CLIENT_SECRET }}
```

**Azure DevOps:**

```yaml
- task: CrowdStrikeImageScan@1
  inputs:
    clientId: $(CS_CLIENT_ID)
    clientSecret: $(CS_CLIENT_SECRET)
    imageRepository: myapp
    imageTag: $(Build.BuildId)
    failOnCritical: true
    failOnHigh: false
```

---

### 6. Cloud Account — CSPM/Horizon (Agentless)

**AWS Setup:**

```bash
# CloudFormation stack registers account
aws cloudformation create-stack \
  --stack-name CrowdStrike-CSPM \
  --template-url https://cs-prod-cloudconnect-templates\
     .s3.amazonaws.com/aws_cspm.template \
  --parameters \
    ParameterKey=RoleName,\
    ParameterValue=CrowdStrikeCSPMRole \
  --capabilities CAPABILITY_IAM
```

**Azure Setup:**
- Register Falcon app in Azure AD
- Grant Reader role on subscription
- Falcon polls Azure Resource Manager APIs

---

### 7. Cloud Identities — CIEM (Agentless)

No additional installation required — enabled via Falcon console toggle once cloud account is connected via CSPM.

---

### Complete Installation Summary

| Component | Where Installed | Method | Agent? |
|---|---|---|---|
| **Falcon Sensor** | Each VM/Server | Package manager/GPO/script | Yes |
| **Node Sensor** | Kubernetes Node | Helm DaemonSet | Yes (node level) |
| **Container Sensor** | Inside Container | Helm + Mutating Webhook | Yes (container level) |
| **KAC** | Kubernetes Cluster | Helm | Yes (cluster level) |
| **Image Assessment** | CI/CD Pipeline | GitHub Action/ADO Task/CLI | No (API based) |
| **CSPM/Horizon** | Cloud Account | IAM Role/CloudFormation | No (agentless) |
| **CIEM** | Cloud Account | Extends from CSPM | No (agentless) |
| **CDR** | Cloud Account | Log ingestion via APIs | No (agentless) |

---

### Full Installation Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     DEVELOPER LAPTOP                         │
│                   fctl CLI (image scan)                      │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                     CI/CD PIPELINE                           │
│              Image Assessment Action/Task                    │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                  CONTAINER REGISTRY                          │
│              Registry Scanning (agentless)                   │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                  KUBERNETES CLUSTER                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    KAC — intercepts all deployments at API server    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   NODE 1    │  │   NODE 2    │  │   NODE 3    │         │
│  │ Node Sensor │  │ Node Sensor │  │ Node Sensor │         │
│  │ (DaemonSet) │  │ (DaemonSet) │  │ (DaemonSet) │         │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │         │
│  │ │  Pod 1  │ │  │ │  Pod 3  │ │  │ │  Pod 5  │ │         │
│  │ │Container│ │  │ │Container│ │  │ │Container│ │         │
│  │ │ Sensor* │ │  │ │ Sensor* │ │  │ │ Sensor* │ │         │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   CLOUD ACCOUNT LAYER                        │
│   CSPM/Horizon          CIEM              CDR                │
│   (agentless)        (agentless)       (agentless)           │
│   config scanning    IAM analysis    log ingestion           │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   FALCON PLATFORM                            │
│        All data converges here for unified detection         │
│     Threat Graph │ AI/ML │ OverWatch │ Threat Intelligence   │
└──────────────────────────────────────────────────────────────┘
```

---

### Key Decision Rules

```
Protecting a SERVER or VM?          → Falcon Sensor (always)
Protecting KUBERNETES NODES?        → Node Sensor via DaemonSet
Need per-CONTAINER visibility?      → Container Sensor via webhook
Running on AWS Fargate?             → Container Sensor (no node access)
Need to GATE deployments?           → KAC (always in production)
Want to scan IMAGES before runtime? → Image Assessment in CI/CD
Want to audit CLOUD CONFIG?         → CSPM (agentless)
Want to audit CLOUD PERMISSIONS?    → CIEM (free with CSPM)
Want CLOUD LOGS and detections?     → CDR (connect cloud audit logs)
```

---

*Author: Peeyush Kumar Rao | Senior Specialist, GSOC Security Technical Operations | CGI*  
*Topics: CrowdStrike Falcon | Cloud Security | Kubernetes | EDR | CWPP | CSPM | CIEM*
