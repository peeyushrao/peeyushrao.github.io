# Day-2 : Kubernetes Fundamentals — Architecture, Pods & Replica Sets

> **Series:** Cloud Workload Protection — Day 2  
> **Topics:** Container orchestration concepts, Kubernetes architecture, cluster setup, Pods, multi-container Pods, troubleshooting, Replica Sets, scaling

---

## Table of Contents

1. [Why Container Orchestration?](#why-container-orchestration)
2. [Orchestration Tools — Landscape](#orchestration-tools--landscape)
3. [Kubernetes Architecture](#kubernetes-architecture)
4. [Setting Up a Kubernetes Cluster](#setting-up-a-kubernetes-cluster)
5. [The Pod — Kubernetes' First Object](#the-pod--kubernetes-first-object)
6. [Multi-Container Pods & Troubleshooting](#multi-container-pods--troubleshooting)
7. [CMD vs. ENTRYPOINT (Dockerfile Recap)](#cmd-vs-entrypoint-dockerfile-recap)
8. [Replica Sets](#replica-sets)
9. [Labels and Selectors — Why They Matter](#labels-and-selectors--why-they-matter)
10. [Scaling Replica Sets](#scaling-replica-sets)
11. [Quick-Check Questions](#quick-check-questions)

---

## Why Container Orchestration?

Docker on a single host is powerful. You can run containers, map ports, and deploy applications. But in production, a single machine is never enough. Consider a real-world scenario: your application is running as 300 containers spread across three virtual machines — 100 containers per machine.

Now one virtual machine goes down. Instantly your current running count drops from 300 to 200. Who notices? Who fixes it?

That is exactly the problem container orchestration solves. An orchestration tool continuously watches your cluster and enforces a simple contract:

> **Desired count must always equal current count.**

The moment they diverge — because a VM failed, a container crashed, or you just asked for more — the orchestration tool acts immediately to restore balance.

The five core capabilities every orchestration tool provides:

- **Create containers at scale** — hundreds or thousands, from a single image
- **High availability** — automatically recreate failed containers
- **Rolling updates** — update the running image version without downtime
- **Scheduling** — distribute containers intelligently across worker nodes
- **Scaling** — manually or automatically scale up or down

---

## Orchestration Tools — Landscape

| Tool | Type | Notes |
|---|---|---|
| **Docker Swarm** | Docker-native orchestration | Built into Docker; simpler than Kubernetes but less feature-rich |
| **Kubernetes (K8s)** | Open-source orchestration | Industry standard; highly flexible and extensible |
| **EKS** | Elastic Kubernetes Service (AWS) | Managed Kubernetes on AWS |
| **GKE** | Google Kubernetes Engine | Managed Kubernetes on GCP |
| **AKS** | Azure Kubernetes Service | Managed Kubernetes on Azure |
| **OCP / OpenShift** | Red Hat's Kubernetes platform | Kubernetes with enterprise tooling on top |

> **Docker Compose vs. Docker Swarm:** These are often confused. Docker Compose deploys multiple containers from a single YAML file on one Docker host — it is not an orchestration tool. Docker Swarm extends that to a cluster of machines. Kubernetes is a completely independent orchestration system that borrows only the container image from Docker; it does not use Dockerfiles or Compose files.

> **On cloud clusters (EKS, GKE, AKS):** The master node is fully managed by the cloud provider. You only see and manage the worker nodes (called a **node pool**). You connect to the cluster via `kubectl` and the API server. The manual setup below applies to self-hosted clusters only.

---

## Kubernetes Architecture

Kubernetes runs in a **cluster** — a set of virtual machines connected on the same network. Each machine plays one of two roles.

```
┌──────────────────────────────────────────────┐
│               MASTER NODE                    │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │API Server│  │Scheduler │  │   ETCD   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│  ┌───────────────────┐  ┌──────────────────┐ │
│  │ Controller Manager│  │    kubectl       │ │
│  └───────────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────┘
           │                    │
    ┌──────┴──────┐      ┌──────┴──────┐
    │ WORKER NODE 1│      │ WORKER NODE 2│
    │             │      │             │
    │  ┌────────┐ │      │  ┌────────┐ │
    │  │kubelet │ │      │  │kubelet │ │
    │  └────────┘ │      │  └────────┘ │
    │  ┌────────┐ │      │  ┌────────┐ │
    │  │kube-   │ │      │  │kube-   │ │
    │  │proxy   │ │      │  │proxy   │ │
    │  └────────┘ │      │  └────────┘ │
    └─────────────┘      └─────────────┘
```

### Master Node Components

#### 1. API Server
The single entry point for all Kubernetes operations. Every `kubectl` command you run sends an HTTP request to the API server. It receives the request, validates it, and persists the desired state — but it does not directly create any containers.

#### 2. Scheduler
The scheduler is an algorithm that runs continuously, watching the API server for newly received requests. When a request arrives (e.g. "create 10 Tomcat containers"), the scheduler:
- Queries ETCD for current cluster state (which nodes exist, how many resources are available, any affinity rules)
- Decides **which worker node** each container should be placed on
- Informs the API server of its decision

> **Important:** "Schedule" here means *where to place*, not *when to run*. The scheduler is not a time-based cron mechanism — it is a placement algorithm that runs in round-robin fashion by default.

#### 3. ETCD
A key-value store database (not relational — no SQL, no tables). ETCD is the single source of truth for the entire cluster. It stores:
- All node details and their available resources
- All running workloads and their status
- Certificates and configuration

When you run `kubectl get pods`, the API server reads this answer from ETCD.

#### 4. Controller Manager
The brain of Kubernetes. Not a single program — a collection of **controllers**, each responsible for enforcing a desired state. Controllers run in a continuous loop checking desired count vs. current count.

Examples:
- **ReplicaSet controller** — ensures the desired number of Pod replicas is always running
- **Job controller** — creates a container to run a task once, then stops
- **CronJob controller** — schedules jobs on a time-based schedule

#### 5. kubectl
The command-line client tool for Kubernetes. All commands begin with `kubectl`. It communicates with the API server via REST. It needs a configuration file (admin.conf) to know the API server's address and credentials.

### Worker Node Components

#### 6. kubelet
The most critical component on every worker node. kubelet is an agent process that:
- Receives instructions from the API server ("create these containers")
- Pulls the required images from the container registry (via the container runtime — Docker or containerd)
- Creates the containers and reports status back to the API server
- Restarts failed containers automatically

> **Note:** kubelet also runs on the master node, because Kubernetes components themselves (API server, scheduler, ETCD) run as containers. Containers can only be created by kubelet.

#### 7. kube-proxy
Manages networking for containers — exposing them to other containers within the cluster or to the external world. This is covered in detail under the Service object.

### Request Flow — End to End

```
Developer
    │
    ▼ kubectl create ...
API Server  ←── receives request, stores desired state in ETCD
    │
    ▼ (scheduler reads ETCD, decides placement)
Scheduler   ──► informs API server: "place on worker-1"
    │
    ▼
API Server  ──► tells kubelet on worker-1: "create these containers"
    │
    ▼
kubelet     ──► pulls image from Docker Hub / registry
            ──► creates containers
            ──► reports status back to API server
    │
    ▼
API Server  ──► updates ETCD with running state
```

---

## Setting Up a Kubernetes Cluster

### Self-Hosted Cluster — Minimum Requirements

| Resource | Minimum |
|---|---|
| RAM | 4 GB (8 GB recommended) |
| CPU | 2 vCPU |
| OS | Ubuntu 22.04 LTS (recommended) |
| Machines | 1 master + 1 or more workers |
| Cloud VM type | AWS T2.medium or equivalent |

### Installation Steps (Self-Hosted)

The setup is the same on master and worker nodes unless stated otherwise.

**Step 1 — Become root**

```bash
sudo su -
```

**Step 2 — Install container runtime (containerd)**

containerd is the standard container runtime for Kubernetes. Docker is built on top of containerd. Both are interchangeable for Kubernetes purposes.

```bash
# Using the instructor's setup script from GitHub
wget <script-url> -O install-containerd.sh
bash install-containerd.sh
# Script auto-detects OS (Ubuntu / CentOS / Amazon Linux) and installs accordingly
```

**Step 3 — Install Kubernetes binaries**

Three binaries are needed on every node:

| Binary | Purpose |
|---|---|
| `kubeadm` | Bootstrap tool — initialises the cluster, joins workers |
| `kubelet` | Agent that creates and manages containers |
| `kubectl` | CLI client to interact with the cluster |

```bash
# Using the instructor's setup script
wget <script-url> -O install-kubernetes.sh
bash install-kubernetes.sh
# Script installs all three binaries + required certificates / GPG keys
```

**Step 4 — Initialise the master node** *(master only)*

```bash
kubeadm init --ignore-preflight-errors=all
```

This command:
- Downloads Kubernetes component images (API server, scheduler, ETCD, controller manager)
- Creates PKI certificates in `/etc/kubernetes/pki/`
- Creates manifest files in `/etc/kubernetes/manifests/`
- Starts all control plane components as pods in the `kube-system` namespace
- Outputs a **join token** — copy this for the worker nodes

**Step 5 — Configure kubectl** *(master only)*

kubectl needs to know where the API server is. Its configuration lives in `admin.conf`:

```bash
mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
```

**Step 6 — Install the Container Network Interface (CNI)**

Kubernetes does not ship with a built-in container network. Until a CNI is installed, the node status is `NotReady` and no pods can be scheduled.

```bash
# Flannel is a common choice
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

After this the master node status changes to `Ready`.

**Step 7 — Join worker nodes** *(worker nodes only)*

Run the join command that `kubeadm init` printed. It includes the master's IP, port, and a token.

```bash
kubeadm join <master-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

**Step 8 — Verify the cluster**

```bash
kubectl get nodes
# Expected: master = Ready, workers = Ready
```

### Key Kubernetes Commands Reference

| Command | Purpose |
|---|---|
| `kubectl get nodes` | List all nodes and their status |
| `kubectl get pods` | List pods in the default namespace |
| `kubectl get pods -n kube-system` | List Kubernetes system pods |
| `kubectl get all` | List all objects (pods, services, replica sets, deployments) |
| `kubectl describe pod <name>` | Full details + events for a pod |
| `kubectl logs <pod> -c <container>` | Logs from a specific container in a pod |
| `kubectl delete pod <name>` | Delete a pod |
| `kubectl delete pod --all` | Delete all pods in default namespace |
| `kubectl apply -f <file.yaml>` | Create or update objects from a YAML file |
| `kubectl create -f <file.yaml>` | Create objects from a YAML file (fails if already exists) |
| `kubectl exec -it <pod> -- bash` | Open a shell inside a running pod |

> **`apply` vs. `create`:** Use `apply` — it creates the object if it doesn't exist and updates it if it does. `create` will error if the object already exists. In practice, always use `apply`.

---

## The Pod — Kubernetes' First Object

### What is a Pod?

A **Pod** is the smallest deployable unit in Kubernetes. It is not a container — it is a wrapper around one or more containers. Every container in Kubernetes runs inside a Pod.

Key properties of a Pod:
- Has its own **IP address** (assigned by the CNI)
- Has its own **network namespace** — all containers in a Pod share it
- Has its own **storage volumes** (optional)
- All containers in a Pod run on the same worker node

> **The shared network implication:** Because containers in the same Pod share a network namespace, they communicate via `localhost`. Consequently, two containers in the same Pod **cannot both listen on port 80** — they would conflict. This is unlike separate Pods, which have separate IPs.

### Pod YAML Structure

Kubernetes objects are always defined in YAML. Every Kubernetes YAML file has four mandatory top-level fields:

```yaml
apiVersion: v1          # API group and version (Pod is in core group, version v1)
kind: Pod               # Type of object
metadata:               # Identity information
  name: pod-1
  labels:
    app: website
spec:                   # Desired state — what should be created
  containers:
    - name: c1
      image: nginx
```

### Creating and Managing Pods

```bash
# Create a pod from YAML
kubectl create -f pod.yaml

# Check pod status
kubectl get pods

# Detailed status (includes events — essential for troubleshooting)
kubectl describe pod pod-1

# Stream logs from a pod (single container)
kubectl logs pod-1

# Delete a pod
kubectl delete pod pod-1
```

### Pod is NOT a Controller

This is a critical distinction. A Pod is a **static object**. If you delete a pod, it stays deleted — Kubernetes will not recreate it. You told Kubernetes "create this pod once"; you never said "keep this pod running always."

```bash
kubectl delete pod pod-1
kubectl get pods
# pod-1 is gone. Nothing recreates it.
```

If you want Kubernetes to maintain a running count of pods — that is the job of a **Replica Set** (covered below).

---

## Multi-Container Pods & Troubleshooting

### Multi-Container Pod YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-2
  labels:
    author: solar
spec:
  containers:
    - name: c1
      image: nginx
    - name: c2
      image: tomcat          # Port 8080 — no conflict with nginx
    - name: c3
      image: ubuntu
      command: ["/bin/bash"]
      args: ["-c", "sleep 6000"]   # Keep the container alive
```

### Why `sleep 6000` for Ubuntu?

The default command of the Ubuntu image is `/bin/bash`. When bash has nothing to do (no terminal attached, no script), it exits immediately. An exited container is restarted by Kubernetes in a loop — giving you `CrashLoopBackOff`.

Passing `sleep 6000` keeps the process running so the container stays alive.

### Troubleshooting Container Failures

**Step 1 — Check pod and container status**

```bash
kubectl get pods
# Example output:
# pod-2   1/3   CrashLoopBackOff   4   2m
# "1/3" means 1 container running, 3 total
```

**Step 2 — Describe the pod (read the Events section)**

```bash
kubectl describe pod pod-2
```

Look for:
- Which containers are running vs. which have `Error` or `CrashLoopBackOff`
- Events at the bottom showing what happened during creation

**Step 3 — Read the container logs**

```bash
# Logs from a specific container
kubectl logs pod-2 -c c2
```

The error in the example session: `nginx` (c1) and `apache` (c2) both tried to bind to port 80 — since they share the Pod's network namespace, the second one failed.

### CrashLoopBackOff — What It Means

`CrashLoopBackOff` is not a fatal cluster error. It means:
> "The container started, exited with an error, Kubernetes restarted it, it crashed again — this is now a loop."

The `BackOff` part means Kubernetes adds increasing delay between restart attempts to avoid thrashing.

**Common causes:**
- Two containers in the same Pod trying to use the same port
- The container's main process exits immediately (e.g. Ubuntu with no persistent command)
- Application startup error (check logs for the actual application error)
- Wrong image name or image pull failure (shows as `ImagePullBackOff`, a separate error)

---

## CMD vs. ENTRYPOINT (Dockerfile Recap)

A question from the session that deserves a clear answer.

| | `CMD` | `ENTRYPOINT` |
|---|---|---|
| Purpose | Default command and/or arguments for the container | Sets the fixed executable that always runs |
| Can be overridden? | Yes — entirely replaced by `docker run <image> <new-command>` | No — arguments passed at `docker run` are appended to it, not replaced |
| Use case | Default behaviour, fully replaceable | When the container should always run a specific executable |
| Combined use | `ENTRYPOINT` sets the binary; `CMD` provides default arguments | Together they give a fixed command with overridable defaults |

**Example:**

```dockerfile
# CMD only — easily overridden
CMD ["nginx", "-g", "daemon off;"]

# ENTRYPOINT + CMD — fixed executable, overridable default arg
ENTRYPOINT ["python3", "app.py"]
CMD ["--port", "80"]
# docker run myimage --port 8080   → runs python3 app.py --port 8080
```

> For configuration files (host names, IP addresses that change per environment), neither `CMD` nor `ENTRYPOINT` is the right tool. Use **Kubernetes ConfigMap volumes** — a volume of type ConfigMap that stores the configuration data; the Pod reads it at startup. This keeps configuration out of the image entirely and lets you update it without rebuilding.

---

## Replica Sets

### The Problem with Static Pods

Running individual pods works for experiments. In production you need:
1. **Multiple identical pods** running at all times
2. **Automatic recovery** when a pod dies
3. **Scaling** — increase or decrease the number of pods on demand

None of this is available with the `Pod` object alone. Enter **Replica Sets**.

### What is a Replica Set?

A Replica Set is a Kubernetes **controller** that:

1. Maintains a **desired count** of identical Pods
2. Continuously compares desired count against **current count** (via label selector query)
3. Creates new Pods if current < desired
4. Deletes excess Pods if current > desired
5. Automatically replaces any Pod that dies

The Replica Set controller runs in a continuous loop inside the Controller Manager component of the master node.

### Replica Set YAML Structure

```yaml
apiVersion: apps/v1           # Replica Set uses apps/v1, not core v1
kind: ReplicaSet
metadata:
  name: my-rs
spec:
  replicas: 6                 # DESIRED COUNT — how many pods you want

  selector:                   # CURRENT COUNT — query to find existing pods
    matchLabels:
      app: web-server         # Select pods with this label

  template:                   # POD TEMPLATE — blueprint for new pods
    metadata:
      labels:
        app: web-server       # MUST match the selector above
    spec:
      containers:
        - name: c1
          image: nginx
```

### The Three Sections Explained

**`replicas`** — Desired count. The number you want Kubernetes to maintain at all times.

**`selector`** — Before creating new pods, Kubernetes queries the cluster: "Are there any pods already running with the label `app: web-server`?" This is the current count. The Replica Set will absorb any existing pods with matching labels and count them toward the desired total.

**`template`** — The blueprint pod. When new pods need to be created (because current < desired), this template is used. The labels in the template **must match** the selector labels — otherwise the Replica Set will never count the pods it creates.

> **The selector only checks labels — not images.** If pre-existing pods have the same label but a different image version, the Replica Set will still count them. This is why consistent labelling discipline is critical in production.

### Creating a Replica Set

```bash
kubectl apply -f replicaset.yaml
kubectl get all
# Output shows: replicaset.apps/my-rs   6   6   6   (desired/current/ready)
# And 6 pods named: my-rs-<random-suffix>
```

Pod names are auto-generated as `<replicaset-name>-<random-chars>` — you cannot assign names in the template.

### High Availability in Action

```bash
# Delete one pod manually
kubectl delete pod my-rs-ab3cd

# Check immediately
kubectl get pods
# The deleted pod is gone — a new one with a new name is created within seconds
# Desired: 6   Current: 6  (restored)
```

> **This is the feature that confuses newcomers.** If you delete a pod that is managed by a Replica Set, Kubernetes immediately recreates it. The correct way to reduce the count is to scale the Replica Set — not delete individual pods.

---

## Labels and Selectors — Why They Matter

### Labels Are How Kubernetes Identifies Groups

A label is a key-value pair attached to any Kubernetes object. There is no enforced schema — you define them.

```yaml
labels:
  app: web-server
  version: v2
  environment: production
```

Labels serve two purposes:

**1. Querying / filtering:**

```bash
# Get only pods with this label
kubectl get pods -l app=web-server

# Get pods matching multiple labels
kubectl get pods -l app=web-server,environment=production
```

**2. Selector targeting** — used by Replica Sets, Services, Deployments to identify which pods they manage or expose.

### Why You Cannot Scale a Plain Pod

```bash
kubectl scale pod pod-1 --replicas=5
# Error: the server does not allow this method on the requested resource
```

A `Pod` object has no concept of desired count or current count. It is a single, static entity. Scaling is only available on controller objects (Replica Set, Deployment, StatefulSet).

---

## Scaling Replica Sets

There are two ways to change the replica count.

### Method 1 — `kubectl scale` command (recommended)

```bash
# Scale up to 5 replicas
kubectl scale replicaset my-rs --replicas=5

# Scale down to 3
kubectl scale replicaset my-rs --replicas=3
```

This is the preferred approach because it is immediate, does not require editing files, and is what the `kubectl scale` command was designed for.

### Method 2 — Edit the YAML and `kubectl apply`

```yaml
# In replicaset.yaml, change:
replicas: 2
```

```bash
kubectl apply -f replicaset.yaml
# Output: replicaset.apps/my-rs configured
```

`apply` is idempotent — it updates the existing object rather than creating a new one. Kubernetes detects the change in desired count and acts accordingly.

> **Recommendation:** Use `kubectl scale` for one-off changes. Use the YAML + `apply` approach when the change needs to be tracked in source control (Git). Both are valid.

### What Happens During Scale-Down

When you reduce the replica count, Kubernetes **terminates the excess pods gracefully**. It does not crash them — it sends a termination signal and waits for the process to exit cleanly (with a configurable grace period).

---

## Quick-Check Questions

**Q1.** A virtual machine in your cluster goes down, taking 100 containers with it. You had 300 containers across 3 nodes. What does Kubernetes do automatically?

<details>
<summary>Answer</summary>

The Replica Set controller detects that current count (200) no longer matches desired count (300). It immediately schedules 100 new pods on the remaining available worker nodes, restoring the desired count. If the remaining nodes lack sufficient resources, pods remain in `Pending` state until resources are available.

</details>

---

**Q2.** You run `kubectl delete pod my-rs-ab3cd`. The pod was created by a Replica Set with desired count 6. What happens?

<details>
<summary>Answer</summary>

Kubernetes immediately recreates the deleted pod (with a new random name) to restore the desired count of 6. Deleting a pod managed by a Replica Set does not reduce the replica count — it just triggers a replacement. To actually reduce the count, you must scale the Replica Set.

</details>

---

**Q3.** What are the three mandatory sections under `spec` in a Replica Set YAML, and what does each do?

<details>
<summary>Answer</summary>

`replicas` — specifies the desired count of pods. `selector` — a label query to count currently running pods that this Replica Set should manage (determines current count). `template` — the pod blueprint used to create new pods when current count falls below desired. The labels in the template must match the selector.

</details>

---

**Q4.** You have two pre-existing static pods with label `app: web-server`. You then create a Replica Set with `selector: app: web-server` and `replicas: 4`. How many new pods does Kubernetes create?

<details>
<summary>Answer</summary>

Two. The Replica Set runs the selector query first: it finds 2 pods already running with the matching label and counts them as current replicas. Desired is 4, current is 2 — so it creates 2 new pods, not 4.

</details>

---

**Q5.** What is `CrashLoopBackOff` and what are two common causes?

<details>
<summary>Answer</summary>

`CrashLoopBackOff` means a container started, exited with an error, was restarted by Kubernetes, and crashed again — in a loop. The `BackOff` adds increasing delay between restart attempts. Common causes: (1) two containers in the same Pod trying to bind the same port (since Pod containers share a network namespace), and (2) the container's main process exits immediately (e.g. an Ubuntu container with no persistent command).

</details>

---

**Q6.** What is the difference between `kubectl create` and `kubectl apply`?

<details>
<summary>Answer</summary>

`kubectl create` creates a new object and errors if the object already exists. `kubectl apply` creates the object if it does not exist, or updates it with the changes in the YAML if it does. In practice, always use `apply` — it is idempotent and safe to run multiple times.

</details>

---

**Q7.** The selector in a Replica Set only checks labels — not container images. Why is this significant?

<details>
<summary>Answer</summary>

If pre-existing pods have the matching label but are running a different version of the image, the Replica Set will still adopt them and count them toward the desired total. This means your replica set could be managing a mix of image versions without you realising it. It is a common source of subtle bugs in production. Always ensure labels are precise and application-specific to avoid unintended pod adoption.

</details>

---

> **Up next — Day 3:** Deployments (the object above Replica Sets), rolling updates, rollbacks, and Services — how to expose your pods to the outside world and enable pod-to-pod communication.
