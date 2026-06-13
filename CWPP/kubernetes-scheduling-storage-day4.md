# Day 4: Kubernetes Scheduling, Storage, ConfigMaps, Secrets & StatefulSets

> **Series:** Cloud Workload Protection — Day 4
> **Topics:** DaemonSet, Scheduling techniques (nodeName, nodeSelector, Node Affinity), Taints & Tolerations, Volumes, Persistent Volumes & Claims, StorageClass, ConfigMaps, Secrets, StatefulSets, Capstone: WordPress + MySQL

---

## Table of Contents

1. [DaemonSet](#daemonset)
2. [Scheduling Techniques](#scheduling-techniques)
3. [Taints and Tolerations](#taints-and-tolerations)
4. [Volumes and Persistent Storage](#volumes-and-persistent-storage)
5. [ConfigMaps](#configmaps)
6. [Secrets](#secrets)
7. [Capstone — WordPress + MySQL on Kubernetes](#capstone--wordpress--mysql-on-kubernetes)
8. [StatefulSets](#statefulsets)
9. [Quick-Check Questions](#quick-check-questions)

---

## DaemonSet

### What Problem Does DaemonSet Solve?

With a Deployment or ReplicaSet you specify a count — Kubernetes decides where to place each pod. If you have three worker nodes and create three replicas, you might get two pods on node 1 and one on node 2, with node 3 getting nothing. The scheduler chooses freely.

But some workloads **must run on every node** — exactly one pod per node, no more:

- **Log collectors** — must collect logs from every VM
- **Monitoring agents** — must observe the health of every VM
- **Security / antivirus scanners** — must scan every VM
- **Networking plugins** — kube-proxy, Flannel, Calico must run everywhere for pod-to-pod communication

A DaemonSet solves this. It creates **one pod per worker node automatically**. When a new node joins the cluster, a pod is created on it immediately. When a node is removed, its pod is deleted — no other node compensates.

> **Note:** DaemonSet targets **worker nodes** only. The master node is excluded by default (because it is tainted — explained below).

### DaemonSet vs. ReplicaSet vs. Deployment

| Feature | ReplicaSet / Deployment | DaemonSet |
|---|---|---|
| You specify replica count | Yes | No |
| Scheduler decides placement | Yes | No — one per node, always |
| Scales with node count | No | Yes — automatically |
| Survives node removal | Reschedules elsewhere | Pod on that node is deleted |
| Use case | Stateless application replicas | Node-level infrastructure agents |

> Kubernetes itself uses DaemonSets internally: kube-proxy (networking), Flannel (CNI), metrics agents, and log shippers are all DaemonSets visible in the `kube-system` namespace.

### DaemonSet YAML

DaemonSet YAML looks like a Deployment — except there is **no `replicas` field**.

```yaml
# daemonset.yml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: my-daemonset
spec:
  selector:
    matchLabels:
      type: web-server
  template:
    metadata:
      labels:
        type: web-server
    spec:
      containers:
        - name: c1
          image: nginx
```

### Commands

```bash
kubectl create -f daemonset.yml
kubectl get pods -o wide        # one pod on every worker node
kubectl get daemonset

# View system DaemonSets (Kubernetes uses them internally)
kubectl get daemonset -n kube-system
```

---

## Scheduling Techniques

By default the Kubernetes scheduler distributes pods freely across worker nodes based on available resources. Scheduling techniques let you override or influence this behaviour — restricting pods to specific nodes or preferring certain nodes over others.

There are four techniques, from most rigid to most flexible:

```
nodeName        → hardcode a specific node (strictest)
nodeSelector    → target nodes by label (label-based, binary)
Node Affinity   → weighted label preference with required/preferred rules
Taints &        → repel pods from nodes unless pods have a matching
Tolerations       toleration key (inverted logic — covered next section)
```

### Technique 1 — nodeName

The simplest scheduling control. Hardcode the exact worker node name directly in the pod spec. The scheduler is bypassed entirely — the pod goes exactly where you say.

**When to use:** Rarely. Only when you have a very specific hardware need (e.g., a node with a GPU or a specialised network card).

**Risk:** If the named node is unavailable, the pod stays in `Pending` state indefinitely. No fallback.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubeserve
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kubeserve
  template:
    metadata:
      name: kubeserve
      labels:
        app: kubeserve
    spec:
      nodeName: worker-node-1    # hardcoded — both replicas land here
      containers:
        - image: leaddevops/kubeserve:v1
          name: app
```

### Technique 2 — nodeSelector

Rather than hardcoding a node name, **label your nodes** and then select by label. The scheduler picks any node carrying the matching label. This is label-based, binary — the node either has the label or it does not.

**Step 1 — Label the nodes:**

```bash
kubectl label node <nodename1> disk=hdd
kubectl label node <nodename3> disk=hdd
kubectl label node <nodename2> disk=ssd
```

**Step 2 — Use `nodeSelector` in the pod spec:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubeserve
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kubeserve
  template:
    metadata:
      name: kubeserve
      labels:
        app: kubeserve
    spec:
      nodeSelector:
        disk: ssd          # only schedule on nodes labelled disk=ssd
      containers:
        - image: leaddevops/kubeserve:v1
          name: app
```

> **Behaviour after scheduling:** If you change or remove the label from a node after pods are already running on it, the running pods are **not evicted** — they continue running. Only new or recreated pods are affected by the label condition. This is the "IgnoredDuringExecution" behaviour.

### Technique 3 — Node Affinity

Node Affinity is a richer version of `nodeSelector`. It supports two scheduling modes and lets you assign **weights** to competing preferences.

#### `requiredDuringSchedulingIgnoredDuringExecution`

A hard rule — **must** be satisfied. If no matching node is found, the pod stays Pending. Equivalent in strictness to `nodeSelector`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: disk
                operator: In
                values:
                  - ssd
  containers:
    - name: c1
      image: nginx
```

#### `preferredDuringSchedulingIgnoredDuringExecution`

A soft preference — Kubernetes **tries** to honour it but falls back to other nodes if needed. Each preference is given a **weight (1–100)**. Kubernetes computes the total weight of each eligible node and schedules on the highest-scoring one.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      # Hard rule first — must have disk=ssd
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: disk
                operator: In
                values:
                  - ssd
      # Soft preferences — higher weight wins
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 1
          preference:
            matchExpressions:
              - key: author
                operator: In
                values:
                  - sonal
        - weight: 50
          preference:
            matchExpressions:
              - key: type
                operator: In
                values:
                  - test
  containers:
    - name: c1
      image: nginx
```

**How weight scoring works:**

Each candidate node's matching labels are summed. The node with the highest total weight is preferred. In the example above, a node with `disk=ssd` (required) **and** `type=test` (weight 50) scores higher than one that also has `author=sonal` (weight 1). If resources on the top-scoring node are exhausted, the next highest takes over.

| Affinity Type | Match required? | Fallback if no match? |
|---|---|---|
| `required` | Yes — hard rule | Pod stays Pending |
| `preferred` | No — best effort | Falls back to any available node |

---

## Taints and Tolerations

Scheduling techniques so far work by **attracting** pods to nodes. Taints work in reverse — they **repel** pods from nodes. Only pods with a matching **toleration** can be scheduled on a tainted node.

### How the Master Node Stays Clean

You have never seen your application pods scheduled on the master node. This is because the master node has a taint applied automatically:

```
Taint: node-role.kubernetes.io/control-plane:NoSchedule
```

No application pod has a toleration for this taint — so none can land there. The Kubernetes system pods (API server, scheduler, etcd, controller manager) do have tolerations baked into their YAML manifests, which is why they run on the master.

### Applying a Taint

```bash
# Syntax: kubectl taint node <nodename> <key>=<value>:<effect>

# NoSchedule — block new pods; existing pods continue running
kubectl taint node worker-node-2 color=red:NoSchedule

# NoExecute — evict existing pods AND block new ones
kubectl taint node worker-node-1 color=red:NoExecute

# Remove a taint (add - at the end)
kubectl taint node worker-node-2 color=red:NoSchedule-
```

### Taint Effects Compared

| Effect | New pods blocked? | Existing pods evicted? |
|---|---|---|
| `NoSchedule` | Yes | No — they keep running |
| `NoExecute` | Yes | Yes — terminated immediately if no toleration |

> **NoExecute** is the harsher taint. Use it when you want to drain a node (e.g., for maintenance or when resources are critically low). Use `NoSchedule` when you want to stop new deployments without disrupting what is already running.

### Tolerations — The Key to a Tainted Node

A toleration in a pod/deployment spec says: "Even though this node is tainted, I am allowed in." The key and value in the toleration must match the key and value used when applying the taint.

```yaml
# In the Deployment spec, under template.spec:
tolerations:
  - key: "color"
    operator: "Equal"
    value: "red"
    effect: "NoExecute"
```

**Combined example — Affinity + Toleration:**

```yaml
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 50
          preference:
            matchExpressions:
              - key: disk
                operator: In
                values:
                  - ssd
  tolerations:
    - key: "color"
      operator: "Equal"
      value: "red"
      effect: "NoExecute"
  containers:
    - name: app
      image: nginx
```

This deployment prefers nodes with `disk=ssd` **and** is tolerated on nodes tainted with `color=red:NoExecute`. Other deployments without this toleration cannot schedule on the tainted node.

### Real-World Use Cases

| Scenario | Mechanism |
|---|---|
| Kubernetes master node isolation | Master is tainted `NoSchedule`; system pods have tolerations |
| Dedicate a node for production workloads | Taint the production node; only production deployment YAMLs carry the toleration |
| Node has insufficient resources | Taint with `NoSchedule` to stop new pods without disrupting running ones |
| Drain a node for maintenance | Taint with `NoExecute` to evict all pods and prevent new scheduling |

---

## Volumes and Persistent Storage

### Why Volumes Exist

Containers are **ephemeral**. Any file written inside a container lives only as long as the container lives. Delete the container — delete the data. In Kubernetes, pods can be deleted by the scheduler, by rolling updates, by resource pressure, or by node failure.

Applications that need to survive pod restarts — databases, upload directories, configuration files — must store their data outside the container, in a **volume**.

### The Three-Object Model

Kubernetes implements persistent storage through three objects:

```
StorageClass  →  PersistentVolume (PV)  →  PersistentVolumeClaim (PVC)  →  Pod
```

Think of it like an IT infrastructure request process:

| Organisation analogy | Kubernetes equivalent |
|---|---|
| Pool of drives with the infrastructure team | PersistentVolume (PV) |
| You raise a ticket requesting 50 GB | PersistentVolumeClaim (PVC) |
| IT team allocates the drive to your ticket | PVC binds to the PV |
| You use the drive on your laptop | Pod mounts the PVC |
| You leave the company — drive is recycled or retained | `reclaimPolicy` on the PV |

### StorageClass — The Permission Layer

A StorageClass grants Kubernetes permission to connect to the cloud provider's storage API and dynamically provision storage volumes. On managed cloud clusters (GKE, EKS, AKS), a default StorageClass is created automatically using the Container Storage Interface (CSI) plugin.

```yaml
# sc.yml — custom StorageClass using GCE Persistent Disk (SSD)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
```

> **Static vs. Dynamic provisioning:**
> - **Static** — you manually create PV objects in the cluster, then create PVCs that bind to them. `storageClassName: manual`
> - **Dynamic** — Kubernetes uses a StorageClass to automatically create a PV on the cloud when a PVC is created. No manual PV YAML needed.

### Demo 1 — HostPath Volume (Static, Self-Hosted Cluster)

HostPath creates the volume directory on the **same VM where the pod is scheduled**. Useful for learning and local testing. Not suitable for production (data is lost if the pod reschedules to a different node).

**Step 1 — Create the PersistentVolume:**

```yaml
# pv.yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: block-pv
spec:
  storageClassName: manual
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce      # only one node can mount read/write at a time
  hostPath:
    path: /tmp/data      # directory created on the worker node VM
```

```bash
kubectl create -f pv.yml
kubectl get pv           # Status: Available
```

**Step 2 — Raise a PersistentVolumeClaim:**

```yaml
# pvc.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc
spec:
  storageClassName: manual
  resources:
    requests:
      storage: 1Gi
  accessModes:
    - ReadWriteOnce
```

```bash
kubectl create -f pvc.yml
kubectl get pvc          # Status should change to: Bound
kubectl get pv           # PV Status changes to: Bound
```

**Step 3 — Mount the PVC in a Pod:**

```yaml
# pod-pvc.yml
kind: Pod
apiVersion: v1
metadata:
  name: pod-pvc
spec:
  containers:
    - image: nginx
      name: c1
      volumeMounts:
        - mountPath: "/data"     # directory inside the container
          name: my-volume
  volumes:
    - name: my-volume
      persistentVolumeClaim:
        claimName: pvc
```

```bash
kubectl create -f pod-pvc.yml
kubectl get pods -o wide         # note which worker node the pod landed on
# SSH to that worker node:
ls /tmp/data                     # directory exists on the VM
```

Any file written to `/data` inside the container is mirrored to `/tmp/data` on the VM. If the container is deleted and recreated, `/data` mounts the same `/tmp/data` — data persists.

### AccessModes Reference

| Mode | Short | Meaning |
|---|---|---|
| `ReadWriteOnce` | RWO | One node can mount read/write |
| `ReadOnlyMany` | ROX | Many nodes can mount read-only |
| `ReadWriteMany` | RWX | Many nodes can mount read/write (requires NFS or cloud file storage) |

---

## ConfigMaps

### What Is a ConfigMap?

A ConfigMap stores **non-sensitive** configuration data as key-value pairs. It decouples environment-specific settings (URLs, ports, feature flags) from the container image so the same image can run in dev, staging, and production with different configurations.

**Limits:**
- Max data size: **1 MiB**
- Not encrypted — do not store passwords or tokens here; use Secrets

### Two Ways to Consume a ConfigMap

| Method | When to use |
|---|---|
| **Volume mount** | When the app reads a config file from disk |
| **Environment variable** | When the app reads config from `os.environ` or process env |

### Demo — ConfigMap from Files

**Step 1 — Create property files:**

```bash
# dev.properties
app.env: dev
app.mem: 2048
app.url: dev.com
```

```bash
# prod.properties
app.env: prod
app.mem: 4048
app.url: prod.com
```

**Step 2 — Create ConfigMaps from the files:**

```bash
kubectl create configmap dev-config --from-file=dev.properties
kubectl create configmap prod-config --from-file=prod.properties

kubectl describe configmap dev-config
kubectl get configmap
```

**Step 3 — Mount ConfigMap as a volume in a pod:**

```yaml
# config-devpod.yml
apiVersion: v1
kind: Pod
metadata:
  name: dev-pod
spec:
  containers:
    - name: c1
      image: nginx
      volumeMounts:
        - name: config-volume
          mountPath: /etc/config     # config file appears here inside the container
  volumes:
    - name: config-volume
      configMap:
        name: dev-config             # name of the ConfigMap to mount
```

```bash
kubectl create -f config-devpod.yml
kubectl exec -it dev-pod -- bash
  cd /etc/config
  ls                                 # dev.properties file is present
  cat dev.properties
```

The prod pod uses the same image but mounts `prod-config` instead:

```yaml
# conf-prodpod.yml
apiVersion: v1
kind: Pod
metadata:
  name: prod-pod
spec:
  containers:
    - name: c1
      image: nginx
      volumeMounts:
        - name: config-volume
          mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: prod-config            # different ConfigMap, same image
```

### Live ConfigMap Updates

ConfigMaps mounted as volumes **update automatically** — no pod restart needed. Kubernetes syncs the file in the volume within a few seconds of the ConfigMap being edited.

```bash
kubectl edit configmap dev-config -o yaml
# Press i, make changes, save (:wq)
# Wait a few seconds, then:
kubectl exec -it dev-pod -- cat /etc/config/dev.properties
# Changes are reflected without restarting the pod
```

### ConfigMap as Environment Variables

```yaml
# In the container spec:
env:
  - name: WORDPRESS_DB_HOST
    valueFrom:
      configMapKeyRef:
        name: my-config        # name of the ConfigMap
        key: db-host           # key inside the ConfigMap
  - name: WORDPRESS_DB_USER
    valueFrom:
      configMapKeyRef:
        name: my-config
        key: db-user
```

> **Volume mount vs. env var:** Use volume mount when the app reads a config file. Use env vars when the app reads `os.environ`. Changes to ConfigMap-mounted volumes propagate live; env var changes require a pod restart.

---

## Secrets

### What Is a Secret?

A Secret stores **sensitive data** — passwords, tokens, certificates, API keys. Its structure is identical to a ConfigMap, but:

- Data is **base64-encoded** (not encrypted by default — enable encryption at rest separately)
- Kubernetes takes additional steps to minimise exposure (not written to logs, mounted as tmpfs)
- Access is restricted via RBAC

> **Important security note:** By default, Secrets are stored **unencrypted** in etcd. Anyone with API access or etcd access can read them. Production hardening requires: encryption at rest, RBAC least-privilege, and ideally an external secret store (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager via Secrets Store CSI Driver).

### Encoding a Secret Value

```bash
echo -n "password" | base64
# Output: cGFzc3dvcmQ=

# Decode to verify
echo "cGFzc3dvcmQ=" | base64 -d
# Output: password
```

### Secret YAML

```yaml
# secrets.yml
kind: Secret
apiVersion: v1
metadata:
  name: mysql-pwd
data:
  password: "cGFzc3dvcmQ="    # base64-encoded value of "password"
```

```bash
kubectl create -f secrets.yml
kubectl get secret
kubectl describe secret mysql-pwd    # value is not shown in plain text
```

### Consuming a Secret as an Environment Variable

```yaml
# In the container spec:
env:
  - name: MYSQL_ROOT_PASSWORD
    valueFrom:
      secretKeyRef:
        name: mysql-pwd      # name of the Secret object
        key: password        # key inside the Secret
```

---

## Capstone — WordPress + MySQL on Kubernetes

This end-to-end example brings together Deployments, Services, ConfigMaps, Secrets, and PersistentVolumeClaims in a single working project.

### Architecture

```
Browser
  │
  ▼ NodePort
WordPress Deployment  ──(env: DB_HOST from ConfigMap)──► MySQL Service (ClusterIP)
                      ──(env: DB_PASS from Secret)  ──►
                                                         │
                                                   MySQL Deployment
                                                         │
                                                   PersistentVolumeClaim
                                                         │
                                                   Cloud Storage (GCE PD / EBS)
```

### Step 1 — Create the Secret

```yaml
# secrets.yml
kind: Secret
apiVersion: v1
metadata:
  name: mysql-pwd
data:
  password: "cGFzc3dvcmQ="     # "password" base64-encoded
```

```bash
kubectl create -f secrets.yml
```

### Step 2 — Create the ConfigMap

```yaml
# configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  db-host: mysql           # matches the MySQL Service name
  db-user: root
```

```bash
kubectl create -f configmap.yml
```

### Step 3 — Deploy MySQL

```yaml
# deploy-mysql.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql-wordpress
  template:
    metadata:
      labels:
        app: mysql-wordpress
        product: mysql
    spec:
      containers:
        - name: mysql-container
          image: mysql
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-pwd
                  key: password
            - name: MYSQL_DATABASE
              value: wordpress
---
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  type: ClusterIP
  ports:
    - targetPort: 3306
      port: 3306
  selector:
    app: mysql-wordpress
    product: mysql
```

```bash
kubectl create -f deploy-mysql.yml
kubectl get pods    # wait for mysql pod to be Running

# Verify the wordpress database was created
kubectl exec -it <mysql-pod-name> -- bash
  mysql -u root -p
  # Enter: password
  show databases;
  # wordpress database should be listed
```

### Step 4 — Deploy WordPress

```yaml
# deploy-wordpress.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql-wordpress
      tier: frontend
  template:
    metadata:
      labels:
        app: mysql-wordpress
        tier: frontend
    spec:
      containers:
        - name: wordpress-container
          image: wordpress
          env:
            - name: WORDPRESS_DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: my-config
                  key: db-host       # resolves to "mysql" — the Service name
            - name: WORDPRESS_DB_USER
              valueFrom:
                configMapKeyRef:
                  name: my-config
                  key: db-user
            - name: WORDPRESS_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-pwd
                  key: password
---
apiVersion: v1
kind: Service
metadata:
  name: wordpress
spec:
  type: NodePort
  ports:
    - targetPort: 80
      port: 80
  selector:
    app: mysql-wordpress
    tier: frontend
```

```bash
kubectl create -f deploy-wordpress.yml
kubectl get svc                           # note the NodePort for wordpress
kubectl get nodes -o wide                 # get a worker node external IP

# Open in browser:
# http://<worker-node-IP>:<NodePort>
# Complete the WordPress setup wizard
# Any post/comment/user you create is written to the MySQL database
```

> **What this project demonstrates:** A Secret keeps the DB password out of all YAML files. A ConfigMap externalises the DB hostname so changing the Service name only requires updating the ConfigMap. WordPress discovers MySQL via the Service name (`mysql`) — not an IP address. Data in MySQL persists across pod restarts because MySQL writes to its volume.

---

## StatefulSets

### When Deployment Is Not Enough

Deployments are designed for **stateless** applications — every pod is identical, interchangeable, and can be deleted and replaced with any name.

Databases and stateful middleware have different requirements:
- Pods need a **stable, predictable name** so other pods can address them directly
- Pod recreation should preserve the same identity (same name, same DNS entry)
- Scaling should happen in **order** (pod-0 first, then pod-1, then pod-2)
- Deletion should happen in **reverse order** (highest index first)

StatefulSet provides all of these guarantees.

### StatefulSet vs. Deployment

| Behaviour | Deployment | StatefulSet |
|---|---|---|
| Pod names | `<name>-<random-hash>` | `<name>-0`, `<name>-1`, `<name>-2` |
| Name on recreation | New random name | **Same name** (e.g., `web-1` always comes back as `web-1`) |
| Scale-up order | Any order | Sequential — 0, 1, 2, ... |
| Scale-down order | Any pod | Reverse sequential — highest index first |
| DNS addressability | Via Service only | Via Service **and** by pod name (headless service) |
| Use case | Stateless apps | Databases, message queues, distributed data stores |

### Headless Service — Stable DNS for Each Pod

A standard Service load-balances across all endpoints — you cannot target a specific pod by name. For databases, you often need to reach a specific replica (e.g., the primary write node vs. a read replica).

A **headless service** (ClusterIP: None) registers each pod's name in DNS. Other pods can reach `web-0.my-headless-service` or `web-1.my-headless-service` directly — no IP address needed, and the address remains stable across pod restarts.

```yaml
# headless-service.yml
apiVersion: v1
kind: Service
metadata:
  name: web-headless
spec:
  clusterIP: None          # headless — no virtual IP, just DNS entries per pod
  selector:
    app: nginx
  ports:
    - port: 80
```

### StatefulSet YAML

```yaml
# statefulset.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "web-headless"    # must match the headless service name
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
          volumeMounts:
            - name: www
              mountPath: /usr/share/nginx/html
  volumeClaimTemplates:          # each pod gets its own PVC automatically
    - metadata:
        name: www
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

### Commands

```bash
kubectl create -f headless-service.yml
kubectl create -f statefulset.yml

# Watch pods come up one at a time (in order)
kubectl get pods -w
# web-0 → Running → web-1 → Running → web-2 → Running

# Scale down — deletes from highest index first
kubectl scale statefulset web --replicas=2
# web-2 deleted first, then web-1 if scaled further

# Scale up — creates in order
kubectl scale statefulset web --replicas=4
# web-2 created → web-3 created

# Delete a pod — it comes back with the SAME name
kubectl delete pod web-1
kubectl get pods   # web-1 reappears with the same name
```

### Why Ordered Startup Matters for Databases

When a database cluster boots, each replica needs to sync data from the previous one. If all replicas start simultaneously, they have no way to establish which is the source of truth and synchronisation conflicts occur. StatefulSet's ordered startup ensures pod-0 is fully running before pod-1 starts — pod-1 can then sync from pod-0, pod-2 from pod-1, and so on.

---

## Quick-Check Questions

**Q1.** You want to deploy a log-collection agent on every worker node, including nodes added in the future. Which controller do you use, and what is the key difference from a Deployment?

<details>
<summary>Answer</summary>

Use a **DaemonSet**. The key difference is that you do not specify a replica count — the DaemonSet ensures exactly one pod runs on every worker node automatically. When a new node joins the cluster, a pod is created on it immediately. Deployments require you to specify a count and let the scheduler choose placement freely.

</details>

---

**Q2.** What is the difference between `NoSchedule` and `NoExecute` taint effects?

<details>
<summary>Answer</summary>

`NoSchedule` prevents **new** pods from being scheduled on the tainted node, but all pods already running there continue uninterrupted. `NoExecute` does both — it blocks new pods and **evicts all currently running pods** that do not have a matching toleration. Use `NoSchedule` to stop new workloads without disruption; use `NoExecute` to drain a node completely.

</details>

---

**Q3.** A pod is running on a node with `nodeSelector: disk=hdd`. You remove the `disk=hdd` label from that node. What happens to the running pod?

<details>
<summary>Answer</summary>

Nothing — the pod continues running. This is the "IgnoredDuringExecution" behaviour. Scheduling rules apply only at pod creation time. Only new or recreated pods will be affected by the updated label condition.

</details>

---

**Q4.** What are the three storage objects in Kubernetes and what does each one represent?

<details>
<summary>Answer</summary>

**PersistentVolume (PV)** — a description/entry of what type of storage (e.g., GCE Persistent Disk) and how much capacity is available in the cluster. **PersistentVolumeClaim (PVC)** — a request raised by an administrator or developer to bind a specific capacity and type of storage. The PVC binds to a matching PV. **StorageClass** — a permission object that allows Kubernetes to dynamically provision new storage on the cloud when a PVC is created, without manual PV creation.

</details>

---

**Q5.** When should you use a ConfigMap vs. a Secret?

<details>
<summary>Answer</summary>

Use a **ConfigMap** for non-sensitive configuration data — URLs, hostnames, feature flags, environment names. Use a **Secret** for sensitive data — passwords, API keys, tokens, certificates. Both can be consumed as environment variables or volume-mounted files. The difference is intent and access control — Secrets carry additional safeguards and should have RBAC restrictions. Neither encrypts data at rest by default.

</details>

---

**Q6.** In the WordPress + MySQL deployment, why does `WORDPRESS_DB_HOST` use the value `mysql` (a Service name) rather than a pod IP?

<details>
<summary>Answer</summary>

Pod IPs change every time a pod is recreated. The MySQL Service (`name: mysql`) has a stable ClusterIP and is registered in the cluster's DNS. WordPress resolves `mysql` via DNS to the Service's ClusterIP, which always forwards to the current MySQL pod regardless of IP changes. This is why services, not pod IPs, are used for inter-pod communication.

</details>

---

**Q7.** What are the three guarantees StatefulSet provides that a Deployment does not?

<details>
<summary>Answer</summary>

1. **Stable pod identity** — pods are named `<name>-0`, `<name>-1` etc. and retain the same name on recreation. 2. **Ordered, sequential startup** — pod-0 must be Running before pod-1 starts; pod-1 before pod-2. This enables data synchronisation between database replicas. 3. **Ordered, reverse deletion** — scale-down removes the highest-indexed pod first, preventing data loss by always removing the most recently added replica first.

</details>

---

> **Up next — Day 5:** RBAC (Role-Based Access Control), Kubernetes Dashboard, cluster setup on cloud (EKS), and integrating external Secret Managers (AWS Secrets Manager, HashiCorp Vault).
