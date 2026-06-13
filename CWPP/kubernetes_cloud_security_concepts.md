# Kubernetes & Cloud Workload Security — An Introduction

> A practical guide for security professionals moving from endpoint security into cloud workload protection.
> Written from the perspective of someone who already knows CrowdStrike Falcon, Active Directory, and enterprise infrastructure.

---

## Table of Contents

1. [Containers vs Virtual Machines](#1-containers-vs-virtual-machines)
2. [What is a Kubernetes Cluster?](#2-what-is-a-kubernetes-cluster)
3. [What is a Pod?](#3-what-is-a-pod)
4. [What is a Node Pool?](#4-what-is-a-node-pool)
5. [Kubernetes Deployment Types](#5-kubernetes-deployment-types)
6. [How CrowdStrike Falcon Protects All of This](#6-how-crowdstrike-falcon-protects-all-of-this)
7. [Quick Reference — The Full Picture](#7-quick-reference--the-full-picture)

---

## 1. Containers vs Virtual Machines

### The Core Difference

You already work with Virtual Machines. When you spin up a VM on VMware or Hyper-V, each VM gets its own full copy of Windows or Linux — its own kernel, OS files, and memory allocation. That's heavy. A single VM can be 10–20 GB just for the OS alone.

A **container** is different. Instead of copying the whole OS, it **shares the host OS kernel** — only the application and its libraries are packaged together. That's why a container is tiny (50–500 MB) and starts in seconds instead of minutes.

```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│     VIRTUAL MACHINES        │    │        CONTAINERS           │
├──────────────┬──────────────┤    ├──────────────┬──────────────┤
│     VM 1     │     VM 2     │    │ Container 1  │ Container 2  │
├──────────────┼──────────────┤    │   App A      │   App B      │
│  Guest OS    │  Guest OS    │    │   Libs only  │   Libs only  │
│  (full copy) │  (full copy) │    ├──────────────┴──────────────┤
├──────────────┴──────────────┤    │   Host OS + Shared Kernel   │
│         Hypervisor          │    │     (ONE OS for all)        │
├─────────────────────────────┤    ├─────────────────────────────┤
│      Physical Hardware      │    │      Physical Hardware      │
└─────────────────────────────┘    └─────────────────────────────┘

Each VM: 1–20 GB (full OS copy)    Each container: 50–500 MB (no duplicate OS)
```

### The Analogy

Think of a VM like a **separate apartment** — its own walls, plumbing, electricity, and kitchen. A container is like a **room in a shared house** — everyone shares the same plumbing and electricity, but each person has their own space.

### Why This Matters for Security

Since containers share the OS kernel, if that kernel has a vulnerability, **all containers on that host are at risk**. This is the core security challenge of containers — and why kernel-level monitoring (like CrowdStrike Falcon) is essential.

| Property | Virtual Machine | Container |
|---|---|---|
| OS | Own full OS copy | Shares host OS kernel |
| Size | 1–20 GB | 50–500 MB |
| Startup | Minutes | Seconds |
| Isolation | Strong (hypervisor) | Weaker (shared kernel) |
| Security risk | VM escape | Kernel exploit, container breakout |

### What is Docker?

**Docker** is the most popular tool for creating and running containers. You write a `Dockerfile` (a recipe), Docker builds a container **image** from it, and you run that image as a container. **Kubernetes** then orchestrates thousands of these containers across many servers.

---

## 2. What is a Kubernetes Cluster?

### Definition

A **cluster** is a group of machines (called nodes) that work together as one system to run containers. Instead of managing each machine separately, you manage the whole group through a single control point.

### The Analogy from Your World

You already understand this from **Active Directory**:

| Active Directory | Kubernetes |
|---|---|
| Domain | Cluster |
| Domain Controller | Control Plane |
| Member server | Worker node |
| Service/process | Pod |
| Group Policy | Deployment policy |

### Cluster Structure

```
┌─────────────────────────────────────────────────────────┐
│                   KUBERNETES CLUSTER                    │
│                                                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │              CONTROL PLANE (Master)             │  │
│   │    API Server · Scheduler · etcd · Controller   │  │
│   │         "The brain — decides everything"        │  │
│   └──────────────┬──────────┬───────────────────────┘  │
│                  │          │          │                 │
│        ┌─────────▼──┐  ┌───▼──────┐  ┌▼────────────┐  │
│        │  Worker    │  │  Worker  │  │   Worker    │  │
│        │  Node 1    │  │  Node 2  │  │   Node 3    │  │
│        │            │  │          │  │             │  │
│        │  [Pod A]   │  │  [Pod C] │  │  [Pod E]   │  │
│        │  [Pod B]   │  │  [Pod D] │  │  [Pod F]   │  │
│        └────────────┘  └──────────┘  └─────────────┘  │
│                                                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │  CrowdStrike Falcon sensor on every worker node │  │
│   └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### The Two Types of Nodes

**Control Plane (Master Node)**
- The brain of the cluster
- Decides which node should run which container
- Watches for failures and restarts things automatically
- You never run your actual applications here — purely management
- Components: API Server, Scheduler, etcd (database), Controller Manager

**Worker Nodes**
- The actual servers (physical machines or cloud VMs like AWS EC2 or Azure VMs)
- Your containers run here inside objects called **pods**
- Each worker node runs a Falcon sensor (deployed as a DaemonSet — explained later)

---

## 3. What is a Pod?

### Definition

A **pod** is the smallest deployable unit in Kubernetes. It is a wrapper around one or more containers that must work closely together.

The key feature: **all containers inside a pod share the same IP address and the same storage volume**.

### Pod Structure

```
┌─────────────────────────────────────────────────────────┐
│                        WORKER NODE                      │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │                       POD                       │   │
│  │    IP Address: 10.0.0.5  (shared by all inside) │   │
│  │                                                  │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │    Shared Network (localhost between    │    │   │
│  │  │    all containers in this pod)          │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  │                                                  │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐ │   │
│  │  │  Main Container  │  │  Sidecar Container   │ │   │
│  │  │  e.g. web app    │  │  e.g. log collector  │ │   │
│  │  │  your workload   │  │  helper process      │ │   │
│  │  └────────┬─────────┘  └──────────┬───────────┘ │   │
│  │           │                       │              │   │
│  │  ┌────────▼───────────────────────▼───────────┐  │   │
│  │  │         Shared Storage Volume              │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌────────────────────┐                                 │
│  │   Another Pod      │  ← Different IP: 10.0.0.6      │
│  │   Container: DB    │    Completely separate          │
│  └────────────────────┘                                 │
└─────────────────────────────────────────────────────────┘
```

### Key Rules About Pods

- Every pod gets its **own IP address**
- Containers **inside** the same pod talk via `localhost`
- Containers **in different pods** talk via IP (even on same node)
- When a pod dies and restarts, it gets a **new IP** — CrowdStrike tracks by pod identity and image name, not IP
- You almost never create pods directly — you create a **Deployment** (explained next) and it manages pods for you

### The Analogy from Your World

A pod is like a **Windows service group** — multiple processes running together on the same host, sharing resources, treated as one unit. You don't manage individual processes one by one; you manage the service group. Same idea.

### Security Implication

CrowdStrike monitors process activity **inside each pod independently**. Even though two pods are on the same node, Falcon tracks each container's syscalls, network connections, and file activity separately — giving you per-pod visibility.

---

## 4. What is a Node Pool?

### Definition

A **node pool** is a group of worker nodes inside a cluster that all have the **same hardware configuration** (same CPU, RAM, disk type). You create different pools for different types of workloads.

### Node Pool Structure

```
┌───────────────────────────────────────────────────────────────┐
│                       KUBERNETES CLUSTER                      │
│                                                               │
│         ┌─────────────────────────────────────────┐          │
│         │    CONTROL PLANE — manages all pools    │          │
│         └───────────┬──────────────┬──────────────┘          │
│                     │              │              │            │
│   ┌─────────────────▼─┐  ┌────────▼──────┐  ┌───▼──────────┐ │
│   │   NODE POOL 1     │  │  NODE POOL 2  │  │ NODE POOL 3  │ │
│   │  General workload │  │ High-compute  │  │   System /   │ │
│   │  Standard VMs     │  │   GPU VMs     │  │   Infra      │ │
│   │                   │  │               │  │              │ │
│   │  ┌─────────────┐  │  │ ┌───────────┐ │  │ ┌──────────┐ │ │
│   │  │   Node A    │  │  │ │  Node C   │ │  │ │  Node E  │ │ │
│   │  │ [Pod][Pod]  │  │  │ │[Pod][Pod] │ │  │ │[Pod][Pod]│ │ │
│   │  └─────────────┘  │  │ └───────────┘ │  │ └──────────┘ │ │
│   │  ┌─────────────┐  │  │ ┌───────────┐ │  │ ┌──────────┐ │ │
│   │  │   Node B    │  │  │ │  Node D   │ │  │ │  Node F  │ │ │
│   │  │ [Pod][Pod]  │  │  │ │[Pod][Pod] │ │  │ │[Pod][Pod]│ │ │
│   │  └─────────────┘  │  │ └───────────┘ │  │ └──────────┘ │ │
│   └───────────────────┘  └───────────────┘  └──────────────┘ │
│                                                               │
│         Each pool scales independently — auto add/remove nodes│
└───────────────────────────────────────────────────────────────┘
```

### Why Node Pools Exist

Think of it like organising servers in your data centre. You probably have:
- Some servers for databases (high RAM)
- Some for application workloads (balanced CPU/RAM)
- Some for security tools (lightweight, dedicated)

A node pool is that same concept — but formalised in Kubernetes.

**Real-world examples on AWS EKS / Azure AKS:**

| Pool | VM Type | Purpose |
|---|---|---|
| `general` | Standard 4-CPU VMs | Web apps, APIs |
| `compute` | 32-CPU high-memory VMs | Data processing, ML |
| `system` | Small VMs | Monitoring, Falcon sensor, logging |

### The Key Benefit — Autoscaling

Each node pool **scales independently**. If your web app gets heavy traffic, Kubernetes automatically adds more nodes to `pool-general` without touching `pool-system`. You define min/max node count per pool, and Kubernetes handles the rest.

This doesn't exist in traditional on-prem infrastructure — servers don't appear and disappear automatically.

### Security Note — DaemonSet Coverage

When autoscaling adds a new node to a pool, the Falcon sensor DaemonSet **automatically deploys to it** — no manual agent push needed. This guarantees 100% sensor coverage regardless of how many nodes exist at any point in time.

---

## 5. Kubernetes Deployment Types

There are six main ways to deploy workloads in Kubernetes. Each is designed for a specific purpose.

### Quick Reference Table

| Type | Purpose | Analogy | Persists? |
|---|---|---|---|
| **Deployment** | N identical replaceable pods | Falcon agent on 100K endpoints | Yes (keeps running) |
| **StatefulSet** | Ordered pods with fixed identity + storage | McAfee ePO cluster nodes | Yes (with own disk) |
| **DaemonSet** | One pod per node, always | How Falcon deploys to every node | Yes (follows nodes) |
| **Job** | Run once, finish, stop | Windows scheduled task (one-time) | No (exits on completion) |
| **CronJob** | Run on a schedule | Linux cron / Windows Task Scheduler | Repeating schedule |
| **ReplicaSet** | Engine behind Deployment (rarely touch directly) | Windows kernel thread management | Yes (managed by Deployment) |

---

### 5.1 Deployment

**What it does:** Runs N identical, interchangeable pods. If one dies, it is automatically replaced. Supports rolling updates with zero downtime.

```
                    ┌─────────────────┐
  Traffic ───────►  │  Load Balancer  │
                    └────────┬────────┘
                    ┌────────▼────────┐
               ┌────┤   3 Replicas   ├────┐
               │    └────────────────┘    │
               │                          │
        ┌──────▼──────┐            ┌──────▼──────┐
        │   Pod 1     │            │   Pod 2     │
        │  (web app)  │            │  (web app)  │
        └─────────────┘            └─────────────┘
                           ┌──────▼──────┐
                           │   Pod 3     │
                           │  (web app)  │
                           └─────────────┘
          Pod dies → auto-replaced. All identical.
```

**Use case:** Web apps, REST APIs, microservices — anything stateless.

**Analogy:** Like deploying the Falcon agent to 100K endpoints — every instance is identical and interchangeable. If one endpoint goes offline, the others keep working. Kubernetes replaces the dead pod automatically, like SCCM would redeploy a failed agent.

**Security risk:** If one pod is compromised, the attacker may try lateral movement to replica pods or shared network. CrowdStrike monitors each pod's process activity independently.

---

### 5.2 StatefulSet

**What it does:** Runs N pods where **each pod has a fixed name, fixed storage, and fixed startup order**. Even after restart, the pod keeps its identity.

```
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │  mysql-0    │    │  mysql-1    │    │  mysql-2    │
  │  (Primary)  │    │  (Replica)  │    │  (Replica)  │
  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
         │                  │                  │
  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
  │  Disk PVC-0 │    │  Disk PVC-1 │    │  Disk PVC-2 │
  │  (own disk) │    │  (own disk) │    │  (own disk) │
  └─────────────┘    └─────────────┘    └─────────────┘
  Each pod keeps its name and disk even after restart.
  Pods start/stop in strict order: 0 → 1 → 2
```

**Use case:** Databases (MySQL, MongoDB, PostgreSQL), message queues (Kafka, RabbitMQ), anything that stores state.

**Analogy:** Like your McAfee multi-node ePO cluster — each node has a specific role (primary/replica), a fixed hostname, and its own database. You cannot swap nodes randomly. StatefulSet enforces the same discipline in Kubernetes.

**Security risk:** Persistent volumes survive pod deletion — sensitive data remains on disk. CrowdStrike watches for unusual file access patterns on these volumes.

---

### 5.3 DaemonSet ⭐ Most Important for Security

**What it does:** Ensures **exactly one pod runs on every node** — always. When a new node joins the cluster, the DaemonSet automatically deploys its pod to it. You cannot have two copies on the same node.

```
       ┌──────────────────────────────────┐
       │   DaemonSet: Falcon Sensor Pod   │
       └──────┬──────────────┬────────────┘
              │              │              │
    ┌─────────▼───┐  ┌───────▼─────┐  ┌────▼────────┐
    │   Node 1    │  │   Node 2    │  │   Node 3    │
    │ 1 sensor pod│  │ 1 sensor pod│  │ 1 sensor pod│
    └─────────────┘  └─────────────┘  └─────────────┘
    New node joins → Falcon auto-deploys. No manual action.
```

**Use case:** Security agents (Falcon), log collectors, monitoring tools, network plugins — anything that must run on every node.

**Analogy:** This is exactly how you deploy the CrowdStrike Falcon agent today — every endpoint must have exactly one sensor. DaemonSet does this automatically in Kubernetes. New node joins → Falcon sensor deploys to it instantly, without manual action. Same guarantee you enforce via policy, but fully automated.

**Why this is critical for you:** CrowdStrike Falcon Cloud Security deploys as a DaemonSet, giving you kernel-level visibility into every pod on every node across the entire cluster. When autoscaling adds nodes, Falcon coverage is immediate and guaranteed.

**Security risk of DaemonSets in general:** A malicious DaemonSet is one of the most dangerous attack outcomes — it runs on every single node. If an attacker creates an unauthorised DaemonSet, they effectively own the entire cluster. Falcon CSPM detects unexpected DaemonSet creation as a high-priority alert.

---

### 5.4 Job

**What it does:** Runs a pod to **completion**. Once the task finishes, the pod stops. Kubernetes tracks success or failure and retries on failure.

```
  ┌───────────┐      ┌───────────┐      ┌─────────────┐
  │  Pending  │ ───► │  Running  │ ───► │  Completed  │
  └───────────┘      └───────────┘      └─────────────┘
                                          Pod exits. Done.
                                          Not restarted.
```

**Use case:** Database migrations, batch data processing, one-time setup scripts, report generation, compliance scans.

**Analogy:** Like a Windows scheduled task that runs a script and exits — a database backup, a report generation script, or a one-time patch script. It runs, finishes its work, and stops.

**Security risk:** Jobs are short-lived and easy to miss. Attackers abuse Jobs to run malicious scripts that complete quickly and disappear. CrowdStrike captures all process executions even from short-lived pods — the telemetry persists even after the pod is gone.

---

### 5.5 CronJob

**What it does:** A Job that runs **on a schedule** — uses the same cron syntax as Linux cron (`minute hour day month weekday`). Creates a new Job each time the schedule triggers.

```
  ┌──────────────────────┐
  │ Schedule: 0 * * * *  │  (every hour)
  └──────────┬───────────┘
             │ triggers
    ┌─────────▼──────┐   ┌────────────────┐   ┌────────────────┐
    │  Job (12:00)   │   │  Job (13:00)   │   │  Job (14:00)   │
    │  [runs, done]  │   │  [runs, done]  │   │  [runs, done]  │
    └────────────────┘   └────────────────┘   └────────────────┘
    Old completed Jobs are cleaned up automatically.
```

**Use case:** Nightly database backups, hourly reports, periodic compliance scans, scheduled cleanup tasks.

**Analogy:** Exactly like Linux cron or Windows Task Scheduler. You already use scheduled tasks for things like Zabbix polling, log rotation, or patch compliance checks. CronJob is that same concept inside Kubernetes — uses the identical cron syntax.

**Security risk (persistence technique):** Attackers who gain cluster access often create malicious CronJobs for **persistence** — even if you delete the pod, the CronJob recreates it on the next schedule. This is a common post-exploitation technique. CrowdStrike and Falcon CSPM detect unexpected CronJob creation and alert on it.

---

### 5.6 ReplicaSet

**What it does:** Ensures N copies of a pod are always running. Constantly reconciles actual count vs desired count and replaces dead pods.

```
  ┌────────────┐    creates    ┌─────────────────────┐    manages    ┌────────┐
  │ Deployment │ ────────────► │     ReplicaSet      │ ────────────► │ Pod 1  │
  └────────────┘               │  (desired: 3 pods)  │               ├────────┤
                                └─────────────────────┘               │ Pod 2  │
                                                                       ├────────┤
                                                                       │ Pod 3  │
                                                                       └────────┘
  You almost never create a ReplicaSet directly.
  Deployment manages it for you automatically.
```

**Use case:** You rarely interact with this directly — Deployment creates and manages ReplicaSets automatically.

**Analogy:** Like Windows kernel thread management — you don't manage individual threads, the OS does. But knowing threads exist helps when you're debugging performance issues. Same idea here.

**Why it matters for investigations:** If CrowdStrike flags a suspicious pod, checking its ReplicaSet tells you which Deployment created it and whether the container image is expected or was injected by an attacker. This is your first step in a Kubernetes incident investigation.

---

## 6. How CrowdStrike Falcon Protects All of This

### The Single Most Important Fact

CrowdStrike Falcon for cloud workloads uses the **same Falcon sensor** you already manage — it just deploys to cloud VMs and Kubernetes nodes instead of Windows endpoints. The console, policies, host groups, and detection workflows are identical to what you already know.

### How Falcon Deploys in Kubernetes

```
  kubectl apply -f falcon-daemonset.yaml
         │
         ▼
  Kubernetes Control Plane
         │
         ├──► Node 1 → Falcon sensor pod auto-deployed
         ├──► Node 2 → Falcon sensor pod auto-deployed
         ├──► Node 3 → Falcon sensor pod auto-deployed
         └──► Node 4 (new, autoscaled) → Falcon sensor pod auto-deployed
  
  One sensor per node. Kernel-level visibility.
  All container processes on that node are monitored.
```

### What Falcon Sees Per Deployment Type

| Deployment Type | What Falcon Monitors |
|---|---|
| Deployment | Process spawns, network connections, file writes per pod |
| StatefulSet | File access on persistent volumes, unusual DB process activity |
| DaemonSet | Watches for unauthorised DaemonSets (high severity alert) |
| Job | All process executions even in short-lived pods — telemetry retained |
| CronJob | Unexpected schedule creation, malicious command execution |

### Key CrowdStrike Features for Cloud Workloads

**Falcon Cloud Security (CSPM):** Scans your cloud environment for misconfigurations — open storage buckets, overpermissive IAM roles, insecure Kubernetes RBAC settings.

**Falcon Container Security:** Runtime protection inside containers — detects process injection, privilege escalation, container breakout attempts.

**Falcon FileVantage (FIM):** File Integrity Monitoring on cloud VMs and container host nodes — same tool, extended to cloud workloads. Critical for PCI DSS, HIPAA compliance on cloud servers.

**Falcon for IT (IT Automation):** Run remediation scripts across cloud nodes automatically — OS patching, software verification, compliance enforcement at scale.

---

## 7. Quick Reference — The Full Picture

### The Hierarchy

```
  CLUSTER
  └── NODE POOL (group of same-spec nodes)
      └── NODE (a VM or physical server)
          └── POD (wrapper around containers)
              └── CONTAINER (your actual app)
                  └── PROCESS (what Falcon monitors)
```

### Kubernetes Object Cheat Sheet

| Object | What it is | Created by |
|---|---|---|
| Cluster | All machines managed as one | Cloud provider (EKS/AKS/GKE) |
| Node Pool | Group of same-spec nodes | You (in cloud console or IaC) |
| Node | Individual VM | Kubernetes (via node pool config) |
| Pod | Wrapper around containers | Deployment / StatefulSet / DaemonSet |
| Container | Running instance of an image | Pod spec |
| Image | Packaged app + libraries | Docker build process |

### Deployment Type Decision Guide

```
  What are you deploying?
  │
  ├── A web app or API that can scale horizontally?
  │   └── DEPLOYMENT
  │
  ├── A database or stateful service that needs its own disk?
  │   └── STATEFULSET
  │
  ├── A security agent / monitoring tool on every node?
  │   └── DAEMONSET  ← This is how Falcon deploys
  │
  ├── A one-time script or migration?
  │   └── JOB
  │
  ├── A recurring task on a schedule?
  │   └── CRONJOB
  │
  └── Already using Deployment? (ReplicaSet is managed for you)
      └── REPLICASET (don't create directly)
```

### Security Risk Summary

| Deployment Type | Top Threat | CrowdStrike Detection |
|---|---|---|
| Deployment | Lateral movement between replicas | Per-pod process monitoring |
| StatefulSet | Data exfiltration from persistent disk | FIM + file access alerts |
| DaemonSet | Attacker creates malicious DaemonSet | CSPM — high severity alert |
| Job | Short-lived malicious script execution | RTR telemetry retention |
| CronJob | Persistence via scheduled re-execution | Unexpected CronJob creation alert |

---

## Further Learning

- **CrowdStrike University:** `university.crowdstrike.com` — Falcon Cloud Security course
- **Kubernetes official docs:** `kubernetes.io/docs`
- **AWS EKS Getting Started:** For hands-on practice with a real managed cluster
- **CrowdStrike CCFA → CCFR:** Your next certification after CCFA builds directly on this knowledge

---

*Author: Peeyush Kumar Rao | Senior Specialist, GSOC Security Technical Operations*
*Tags: kubernetes, cloud-security, crowdstrike, containers, CWP, CSPM*
