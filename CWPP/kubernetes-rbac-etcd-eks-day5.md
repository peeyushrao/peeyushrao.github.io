# Kubernetes RBAC, Namespaces, Dashboard, ETCD Backup, EKS & Troubleshooting

> **Series:** Cloud Workload Protection — Day 5
> **Topics:** Namespaces, Authentication (certificates + tokens), RBAC (Role, RoleBinding, ClusterRole, ClusterRoleBinding), Kubernetes Dashboard, ETCD Backup & Restore, EKS Cluster Setup, Cluster Troubleshooting

---

## Table of Contents

1. [Namespaces](#namespaces)
2. [Authentication in Kubernetes](#authentication-in-kubernetes)
3. [Creating a User with Certificate Authentication](#creating-a-user-with-certificate-authentication)
4. [RBAC — Role and RoleBinding](#rbac--role-and-rolebinding)
5. [Switching Context — Running as a Restricted User](#switching-context--running-as-a-restricted-user)
6. [Remote Access from a Separate Machine](#remote-access-from-a-separate-machine)
7. [ClusterRole and ClusterRoleBinding](#clusterrole-and-clusterrolebinding)
8. [Kubernetes Dashboard](#kubernetes-dashboard)
9. [ETCD Backup and Restore](#etcd-backup-and-restore)
10. [EKS — Kubernetes on AWS](#eks--kubernetes-on-aws)
11. [Cluster Troubleshooting](#cluster-troubleshooting)
12. [Accessing Ingress on a Self-Hosted Cluster](#accessing-ingress-on-a-self-hosted-cluster)
13. [CrashLoopBackOff — Port Conflict Deep Dive](#crashloopbackoff--port-conflict-deep-dive)
14. [ImagePullBackOff — Diagnosis Checklist](#imagepullbackoff--diagnosis-checklist)
15. [Helm — Package Manager for Kubernetes](#helm--package-manager-for-kubernetes)
16. [Taints and Tolerations — Quick Recap](#taints-and-tolerations--quick-recap)
17. [CKA Certification — Quick Reference](#cka-certification--quick-reference)
18. [Quick-Check Questions](#quick-check-questions)

---

## Namespaces

### The Problem Without Namespaces

Imagine multiple teams — Java, Python, QA — all deploying pods into the same Kubernetes cluster. Everything goes into the default namespace. A new team member, unfamiliar with what is running, executes `kubectl delete all`. Every pod in the cluster is gone — not just theirs.

Namespaces solve this by **partitioning the cluster** into isolated spaces. Resources in one namespace are unaffected by `delete all` in another namespace.

### How Namespaces Work

A namespace is a virtual partition within the cluster. Each team gets their own namespace — pods, services, deployments, and secrets created within it are scoped to that namespace only.

By default, you have been working in the `default` namespace. Kubernetes also uses system namespaces internally:

| Namespace | Purpose |
|---|---|
| `default` | Where all resources go unless you specify otherwise |
| `kube-system` | Kubernetes system components (API server, scheduler, etcd, kube-proxy) |
| `kube-public` | Publicly accessible data, e.g. cluster info |
| `kubernetes-dashboard` | Created when you deploy the dashboard |

### Working with Namespaces

```bash
# Create a namespace
kubectl create namespace dev

# Create a namespace via YAML
kubectl apply -f namespace.yml
```

```yaml
# namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
```

```bash
# List all namespaces
kubectl get namespaces

# Create a pod in a specific namespace (in the YAML)
# metadata:
#   name: pod1
#   namespace: dev

# Get pods from a specific namespace
kubectl get pods -n dev

# Get pods from ALL namespaces
kubectl get pods --all-namespaces

# Set default namespace for the current context (via config — shown in RBAC section)
# Delete everything in a namespace (only that namespace — not others)
kubectl delete all --all -n dev
```

### Resource Quotas — Limiting Namespace Consumption

You can cap how much CPU and memory a namespace is allowed to use with a `ResourceQuota` object. This is created separately from the namespace object itself.

```yaml
# resourcequota.yml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "2"
    requests.memory: "1Gi"
    limits.cpu: "4"
    limits.memory: "2Gi"
    pods: "10"
```

```bash
kubectl apply -f resourcequota.yml
kubectl describe namespace dev    # see quota usage
```

> **Namespace ≠ security boundary for network traffic.** Pods in different namespaces can still communicate by default. Namespaces primarily provide resource isolation and access control scoping. Network Policies are needed to enforce network-level isolation.

---

## Authentication in Kubernetes

### No Passwords in Kubernetes

Unlike most systems, Kubernetes does not use username/password for user authentication. Instead it uses:

1. **Client certificates and keys** (X.509) — used for human users
2. **Bearer tokens** — used for Service Accounts (automated processes, CI/CD pipelines)
3. **Authenticated proxy** — external identity providers (LDAP, OIDC)

The `~/.kube/config` file (also called `kubeconfig`) holds all authentication details for `kubectl`. When you run any `kubectl` command, it reads this file to determine:

- **Which cluster** to connect to (API server URL)
- **Which user** is making the request (certificate and key)
- **Which namespace** to operate in (via context)

### Anatomy of the kubeconfig File

```bash
cat ~/.kube/config
```

```yaml
# Simplified structure
apiVersion: v1
kind: Config

clusters:
  - name: kubernetes          # cluster name
    cluster:
      server: https://<master-IP>:6443    # API server URL
      certificate-authority-data: <base64-CA-cert>

users:
  - name: kubernetes-admin    # default admin user
    user:
      client-certificate-data: <base64-cert>
      client-key-data: <base64-key>

contexts:
  - name: kubernetes-admin@kubernetes    # context name
    context:
      cluster: kubernetes
      user: kubernetes-admin
      namespace: default      # default namespace for this context

current-context: kubernetes-admin@kubernetes
```

A **context** ties together a cluster, a user, and a namespace. Switching context = switching who you are and where you operate.

```bash
# See all available contexts
kubectl config get-contexts

# See current context
kubectl config current-context

# Switch to a different context
kubectl config use-context dave-context
```

---

## Creating a User with Certificate Authentication

The workflow to add a new user (e.g., a developer named Dave) to the cluster:

```
Generate private key  →  Create CSR  →  Sign CSR with K8s CA  →  Add user to kubeconfig  →  Bind a Role
```

### Step 1 — Generate a private key for Dave

```bash
mkdir /root/dev && cd /root/dev
openssl genrsa -out dave.key 2048
```

### Step 2 — Create a Certificate Signing Request (CSR)

```bash
openssl req -new -key dave.key -out dave.csr \
  -subj "/CN=dave/O=dev"
# CN (Common Name) = the Kubernetes username
# O (Organization) = the Kubernetes group / namespace
```

> Leave all optional fields (email, challenge password, company) empty.

### Step 3 — Sign the CSR with the Kubernetes CA

Kubernetes itself is the Certificate Authority. Its CA certificate and key live at `/etc/kubernetes/pki/`:

```bash
openssl x509 -req -in dave.csr \
  -CA /etc/kubernetes/pki/ca.crt \
  -CAkey /etc/kubernetes/pki/ca.key \
  -CAcreateserial \
  -out dave.crt \
  -days 365
```

You now have:
- `dave.key` — private key (never share this; share the `.crt` with the developer)
- `dave.crt` — signed certificate (share with the developer so they can authenticate)

### Step 4 — Add the user to kubeconfig

```bash
# Add user credentials to the config file
kubectl config set-credentials dave \
  --client-certificate=/root/dev/dave.crt \
  --client-key=/root/dev/dave.key

# Create a context for Dave in the dev namespace
kubectl config set-context dave-context \
  --cluster=kubernetes \
  --namespace=dev \
  --user=dave
```

```bash
# Verify
kubectl config get-contexts
# Both admin and dave-context should appear
```

---

## RBAC — Role and RoleBinding

Having a certificate only authenticates Dave — it does not give him any permissions. Without a Role bound to his user, every `kubectl` command returns `Forbidden`.

### What is a Role?

A Role is a **namespace-scoped** permission object. It defines:
- **`apiGroups`** — which API group the resources belong to (`""` for core, `"apps"` for Deployments, `"networking.k8s.io"` for Ingress)
- **`resources`** — which objects the rule applies to (pods, deployments, services, secrets, etc.)
- **`verbs`** — what operations are allowed (get, list, watch, create, update, patch, delete)

```yaml
# role.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dev-role
  namespace: dev
rules:
  - apiGroups: ["", "apps"]          # "" = core group (pods, services); "apps" = deployments
    resources: ["pods", "deployments", "services"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

```bash
kubectl apply -f role.yml
kubectl get role -n dev
```

> Dave cannot query secrets, persistent volumes, or any other resource not listed in `resources`. This is the principle of least privilege in practice.

### API Groups Quick Reference

| Resource | API Group | apiVersion in YAML |
|---|---|---|
| Pod, Service, Secret, ConfigMap | `""` (core) | `v1` |
| Deployment, ReplicaSet, DaemonSet, StatefulSet | `apps` | `apps/v1` |
| Job, CronJob | `batch` | `batch/v1` |
| Ingress | `networking.k8s.io` | `networking.k8s.io/v1` |
| Role, RoleBinding | `rbac.authorization.k8s.io` | `rbac.authorization.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling` | `autoscaling/v1` |

### What is a RoleBinding?

A RoleBinding links a Role to a subject (user, group, or ServiceAccount). The Role defines the permissions; the RoleBinding says who gets them.

```yaml
# rolebinding.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-rolebinding
  namespace: dev
subjects:
  - kind: User
    name: dave              # must match the CN in the certificate
    apiGroup: ""            # core group for users
roleRef:
  kind: Role
  name: dev-role            # the Role created above
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f rolebinding.yml
kubectl get rolebinding -n dev
```

---

## Switching Context — Running as a Restricted User

After creating the user, role, and binding, you can verify the restrictions by switching to Dave's context on the same machine:

```bash
# Switch to Dave's context
kubectl config use-context dave-context

# Allowed — pods and deployments in dev namespace
kubectl get pods
kubectl get deployments

# Allowed — create a pod in dev namespace
kubectl run pod1 --image=nginx

# Forbidden — secrets not in Dave's Role
kubectl get secrets
# Error: secrets is forbidden: User "dave" cannot list resource "secrets"

# Forbidden — operating in default namespace
kubectl get pods -n default
# Error: pods is forbidden: User "dave" cannot list resource "pods" in "default"

# Switch back to admin
kubectl config use-context kubernetes-admin@kubernetes
```

---

## Remote Access from a Separate Machine

In real projects, a developer works from their own machine — not on the master node. The workflow to enable this:

**On the master node (admin):**

1. Generate Dave's certificate and key (or Dave generates and sends you the CSR)
2. Copy `dave.crt`, `dave.key`, and a trimmed `kubeconfig` (Dave's context only) to Dave's machine

**On Dave's machine:**

Only `kubectl` is needed — no Docker, no containerd, no kubeadm.

```bash
# Install kubectl only
# (use the same script; only kubectl binary is required)

# Create the .kube directory and config file
mkdir -p ~/.kube
# Paste the kubeconfig content with only dave-context (no admin credentials)
vim ~/.kube/config

# Set ownership
chown $(id -u):$(id -g) ~/.kube/config

# Verify — runs as dave, in dev namespace
kubectl get pods
kubectl get deployments
```

The kubeconfig for Dave should contain:
- The cluster's API server URL and CA cert
- Dave's certificate and key
- The `dave-context` context set as `current-context`
- **No** admin user or admin context entries

> The master node stays secure. Dave never has SSH access to the master. He only has `kubectl` access scoped to what his Role permits.

---

## ClusterRole and ClusterRoleBinding

A **Role** is namespace-scoped — it applies only within one namespace. A **ClusterRole** applies **cluster-wide** — it can grant permissions across all namespaces or on cluster-level resources (nodes, persistent volumes, namespaces themselves).

### When to Use ClusterRole

- Monitoring and logging agents that must read data from every namespace
- Kubernetes Dashboard (needs cluster-wide read access to display all resources)
- Administrators who manage the entire cluster

```bash
# See all built-in cluster roles
kubectl get clusterroles

# Describe a specific cluster role
kubectl describe clusterrole cluster-admin
# cluster-admin = full permissions on everything
```

### ClusterRoleBinding YAML

```yaml
# clusterrolebinding.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-admin
subjects:
  - kind: ServiceAccount
    name: kubernetes-dashboard
    namespace: kubernetes-dashboard
roleRef:
  kind: ClusterRole
  name: cluster-admin             # built-in full-access role
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f clusterrolebinding.yml
```

> **ClusterRole with limited permissions:** You can bind a ClusterRole that allows only specific verbs on specific resources cluster-wide. For example, `system:controller:replicaset-controller` allows managing only ReplicaSets and Pods. Use `kubectl describe clusterrole <name>` to inspect any built-in role's permissions before binding it.

---

## Kubernetes Dashboard

The Kubernetes Dashboard is a web-based GUI for viewing and managing cluster resources — pods, deployments, services, namespaces, volumes, config maps, and more. You can deploy from it, exec into pods, view logs, and delete objects — all without a terminal.

### Deploy the Dashboard

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
```

This creates:
- `kubernetes-dashboard` namespace
- Dashboard Deployment
- ClusterIP Service (needs to be changed to NodePort for browser access)
- ConfigMap and ServiceAccount

```bash
kubectl get all -n kubernetes-dashboard
```

### Expose the Dashboard via NodePort

By default, the dashboard service is ClusterIP — not reachable from outside. Edit it to NodePort:

```bash
kubectl edit service kubernetes-dashboard -n kubernetes-dashboard
# Change: type: ClusterIP
# To:     type: NodePort
# Save and exit (:wq)

kubectl get svc -n kubernetes-dashboard
# Note the NodePort assigned (e.g., 32000)
```

Access in browser: `https://<worker-node-IP>:<NodePort>`

> The dashboard uses HTTPS by default. You will see a browser security warning — accept it to proceed.

### Create a ServiceAccount and Token for Login

The dashboard requires a token to authenticate. Create a ServiceAccount and bind it to a ClusterRole:

```bash
# Create a ServiceAccount
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard

# Bind cluster-admin role
kubectl create clusterrolebinding dashboard-admin-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:dashboard-admin

# Generate a login token
kubectl create token dashboard-admin -n kubernetes-dashboard
# Copy the output token — paste it into the dashboard login page
```

### What You Can Do in the Dashboard

- View all namespaces, pods, deployments, services, replica sets, volumes, config maps, ingress rules
- Create objects by pasting YAML into the `+` button
- View pod logs in-browser
- `exec` into a running container's shell directly from the browser
- Delete, edit, or scale objects
- Monitor CPU/memory graphs per pod (requires Metrics Server)

---

## ETCD Backup and Restore

### Why ETCD Backup Matters

ETCD is Kubernetes' only database — it stores all state: nodes, pods, deployments, namespaces, secrets, everything. If the ETCD data directory is deleted or corrupted, the cluster loses all knowledge of what is running. The cluster nodes are still there, but Kubernetes has no record of any workload.

ETCD stores its data on the master node's filesystem via a hostPath volume at `/var/lib/etcd`.

```bash
# Confirm ETCD data path
kubectl describe pod etcd-<master-name> -n kube-system | grep -A5 Volumes
```

### Install ETCD Client

```bash
# Install version matching your cluster's ETCD version
ETCD_VER=v3.3.13
curl -L https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd.tar.gz
tar xzf /tmp/etcd.tar.gz -C /usr/local/bin --strip-components=1
```

### Take a Snapshot (Backup)

```bash
# Get the ETCD pod IP
kubectl get pod etcd-<master> -n kube-system -o wide
# Note the IP (e.g., 10.0.0.100)

# Create backup directory
mkdir /root/etcd-backup

# Take the snapshot
ETCDCTL_API=3 etcdctl snapshot save /root/etcd-backup/snapshot.db \
  --endpoints=https://10.0.0.100:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify
ETCDCTL_API=3 etcdctl snapshot status /root/etcd-backup/snapshot.db
```

**Port reference:** ETCD listens on **2379** for client reads and **2380** for peer communication.

### Simulate Data Loss

```bash
# Delete the ETCD data directory — wipes all cluster state
rm -rf /var/lib/etcd

# All cluster data is now gone
kubectl get pods          # returns nothing
kubectl get namespaces    # returns nothing
```

### Restore from Snapshot

```bash
ETCDCTL_API=3 etcdctl snapshot restore /root/etcd-backup/snapshot.db \
  --endpoints=https://10.0.0.100:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --data-dir=/var/lib/etcd

# Verify restoration
kubectl get pods
kubectl get namespaces    # previous namespaces and pods should reappear
```

> **Production recommendation:** Schedule automated ETCD snapshots as a CronJob or external cron script. Store snapshots in object storage (S3, GCS) — not on the master node itself. On managed clusters (EKS, GKE, AKS), the cloud provider manages ETCD backup automatically.

---

## EKS — Kubernetes on AWS

AWS offers Kubernetes as a managed service called **Elastic Kubernetes Service (EKS)**. EKS manages the master node (control plane) on your behalf — you only create and manage the worker nodes.

### EKS vs. Self-Hosted vs. GKE

| | Self-Hosted | GKE (Google) | EKS (AWS) |
|---|---|---|---|
| Master node managed by you? | Yes | No | No |
| Worker nodes managed by you? | Yes | Yes (via node pool) | Yes (via node group) |
| Setup complexity | High | Low (single click) | Medium (roles required) |
| Default StorageClass | None | `standard` (GCE PD) | `gp2` (EBS) |
| Default CNI | Manual (Flannel) | Calico | Amazon VPC CNI |
| Free tier availability | N/A | Yes (limited) | No — EKS control plane is paid |

### Creating an EKS Cluster — Step by Step

#### Part 1 — Create the Control Plane

**Step 1 — Create an IAM Role for EKS**

The EKS control plane needs permission to manage AWS resources (EC2, networking) on your behalf.

```
AWS Console → IAM → Roles → Create Role
  → Trusted entity: AWS Service
  → Use case: EKS → EKS Cluster
  → Add policy: AmazonEKSClusterPolicy
  → Role name: eks-cluster-role
  → Create
```

**Step 2 — Create the EKS Cluster**

```
AWS Console → EKS → Create Cluster
  → Name: kube-cluster
  → Kubernetes version: default (latest stable)
  → Cluster service role: eks-cluster-role (created above)
  → Networking: default VPC, default subnets
  → Security group: Create a new SG with all-traffic inbound rule
  → Cluster endpoint access: Public and Private
  → Add-ons: keep defaults (kube-proxy, Amazon VPC CNI, CoreDNS, EBS CSI driver)
  → Create
```

Cluster creation takes approximately **10 minutes**.

#### Part 2 — Create the Node Group (Worker Nodes)

**Step 3 — Create an IAM Role for EC2 Node Group**

Worker nodes need three IAM policies:

| Policy | Purpose |
|---|---|
| `AmazonEKSWorkerNodePolicy` | Allows worker nodes to connect to EKS control plane |
| `AmazonEKS_CNI_Policy` | Allows the CNI plugin to configure VPC networking |
| `AmazonEC2ContainerRegistryReadOnly` | Allows pulling images from ECR (private registry) |

```
IAM → Roles → Create Role
  → AWS Service → EC2
  → Add policies: all three above
  → Role name: eks-nodegroup-role
  → Create
```

**Step 4 — Add Node Group to the Cluster**

```
EKS → Your cluster → Compute → Add node group
  → Name: eks-node-group
  → Node IAM role: eks-nodegroup-role
  → AMI type: Amazon Linux 2023
  → Instance type: t3.medium
  → Desired nodes: 1 (minimum for testing)
  → Keep default subnets
  → Create
```

Node group creation takes approximately **5 minutes**.

### Connecting kubectl to EKS

From the AWS CloudShell (or any machine with AWS CLI installed and configured):

```bash
# Update kubeconfig to connect to your EKS cluster
aws eks update-kubeconfig \
  --region us-east-2 \
  --name kube-cluster

# Verify connection
kubectl get nodes     # shows the worker node(s)
kubectl get pods      # any running workloads

# Run a pod
kubectl run pod1 --image=nginx
kubectl get pods
```

> **Using LoadBalancer services on EKS:** When you create a `type: LoadBalancer` Service on EKS, AWS automatically provisions an Elastic Load Balancer (ELB) and assigns it a public DNS name. This works out of the box — no additional configuration needed.

---

## Cluster Troubleshooting

Troubleshooting a Kubernetes cluster follows a structured top-down approach. Start at the highest observable level and drill down.

### Scenario 1 — `kubectl` Commands Fail with "Connection Refused"

**Symptom:** Any `kubectl` command returns `Unable to connect to the server: connection refused`

**Root cause:** `kubectl` cannot reach the API server.

**Diagnosis steps:**

```bash
# Check the API server URL in kubeconfig
cat ~/.kube/config | grep server
# Expected: https://<master-IP>:6443
```

Verify:
- Is the IP address correct?
- Is the port **6443** (API server default)? Common mistake: port becomes corrupted after a cluster reset.

```bash
# Correct it if wrong
kubectl config set-cluster kubernetes \
  --server=https://<correct-master-IP>:6443
```

### Kubernetes Component Port Reference

| Component | Port | Protocol |
|---|---|---|
| API Server | 6443 | HTTPS |
| ETCD (client) | 2379 | HTTPS |
| ETCD (peer) | 2380 | HTTPS |
| kubelet | 10250 | HTTPS |
| kube-scheduler | 10259 | HTTPS |
| kube-controller-manager | 10257 | HTTPS |
| NodePort range | 30000–32767 | TCP |

### Scenario 2 — Pod Stuck in `Pending` State

**Symptom:** `kubectl get pods` shows a pod as `Pending` indefinitely.

**Step 1 — Describe the pod:**

```bash
kubectl describe pod <pod-name>
# Look at the Events section at the bottom
```

Common messages and what they mean:

| Event message | Cause | Fix |
|---|---|---|
| `0/2 nodes are available: 2 node(s) had untolerated taint` | Node is tainted; pod has no toleration | Add toleration to pod spec or remove taint |
| `Insufficient CPU/memory` | No node has enough resources | Scale down other workloads or add nodes |
| `FailedScheduling` | General scheduling failure | Check taints, resource limits, node selectors |
| `Unschedulable` | All nodes are tainted or have NoSchedule | Check node taints |

**Step 2 — Check node status:**

```bash
kubectl get nodes
kubectl describe node <node-name>
# Look for: Conditions section (Ready/NotReady), Events section
```

### Scenario 3 — Worker Node `NotReady`

When a worker node shows `NotReady`, kubelet on that node has stopped reporting its status to the master.

**Diagnosis sequence:**

```bash
# On the master node — check which node is NotReady
kubectl get nodes

# Describe the problematic node
kubectl describe node <worker-node-name>
# Look for: "kubelet stopped posting node status" or "container runtime not responding"
```

**Go to the worker node and check services:**

```bash
# Check kubelet service
systemctl status kubelet

# If inactive/failed — check logs first
journalctl -u kubelet --since today | tail -50
# Common log errors:
# "unable to register node" → API server IP wrong in kubelet config
# "swap is enabled" → swap must be disabled for kubelet to work

# Fix kubelet config if API server IP is wrong
cat /etc/kubernetes/kubelet.conf | grep server
# Update if incorrect, then restart
systemctl restart kubelet
```

```bash
# If kubelet is running but node still NotReady — check container runtime
systemctl status containerd    # or: systemctl status docker

# If containerd is stopped
systemctl start containerd
```

**Swap check (a common cause of kubelet failure):**

```bash
# Check if swap is enabled
free -h | grep Swap
# Should show 0B used/total if properly disabled

# Disable swap immediately (non-persistent)
swapoff -a

# Disable swap permanently
sed -i '/ swap / s/^/#/' /etc/fstab

# Restart kubelet after disabling swap
systemctl restart kubelet
```

### Scenario 4 — Node Consistently Failing — Full Reset

If all diagnostics pass but the node still does not join, reset and rejoin:

```bash
# On the worker node — reset kubernetes state
kubeadm reset

# On the master node — generate a fresh join token
kubeadm token create --print-join-command

# On the worker node — rejoin the cluster
kubeadm join <master-IP>:6443 --token <new-token> --discovery-token-ca-cert-hash sha256:<hash>
```

### Troubleshooting Decision Tree

```
kubectl command fails
    │
    ├── "connection refused"
    │       └── Check ~/.kube/config → verify API server IP and port 6443
    │
    └── commands work → pod is Pending or node NotReady
            │
            ├── Describe the pod → check Events
            │       ├── Taint issue → add toleration or remove taint
            │       └── Insufficient resources → scale down or add nodes
            │
            └── Node NotReady → describe node → check Events
                    │
                    ├── "kubelet stopped posting"
                    │       ├── systemctl status kubelet
                    │       ├── journalctl -u kubelet (check for swap error or bad API IP)
                    │       └── systemctl restart kubelet
                    │
                    └── "container runtime not responding"
                            ├── systemctl status containerd
                            └── systemctl start containerd
```

---

## Accessing Ingress on a Self-Hosted Cluster

On a cloud cluster (EKS, GKE, AKS), an Ingress object automatically provisions a cloud load balancer with a public **External IP**. On a **self-hosted cluster** (bare VMs, no cloud provider integration), there is no cloud API to provision a load balancer — so the Ingress controller's Service stays stuck with `EXTERNAL-IP: <pending>` forever.

### The Fix — Convert the Ingress Controller's Service to NodePort

```bash
# Edit the ingress-nginx controller's service
kubectl edit service ingress-nginx-controller -n ingress-nginx
```

In the opened YAML, change:

```yaml
spec:
  type: LoadBalancer    # change this...
```

to:

```yaml
spec:
  type: NodePort        # ...to this
```

Save and exit. Kubernetes assigns NodePort values (30000–32767 range) for the HTTP/HTTPS ports.

```bash
kubectl get svc -n ingress-nginx
# Note the NodePort values, e.g. 80:31234/TCP, 443:31876/TCP
```

### Accessing the Application

```
http://<any-worker-node-IP>:<assigned-NodePort>
```

> **Important:** After switching to NodePort, the `EXTERNAL-IP` field will **not** populate — this is expected and correct for self-hosted clusters. Use the worker node's IP address (master or worker — any node IP works) combined with the assigned NodePort. Host-based routing rules in your Ingress YAML (`spec.rules[].host`) still work — you map the hostname to the worker node IP in `/etc/hosts` (or your local DNS) as covered in the Day 3 Ingress demo.

---

## CrashLoopBackOff — Port Conflict Deep Dive

### The Scenario

A multi-container pod has two containers, both using images that listen on port 80 by default (e.g., nginx and httpd/Apache). The pod status shows `CrashLoopBackOff`.

### Why This Happens

All containers within a single Pod **share the same network namespace** — meaning they share the same IP address and the same port space. If two containers both attempt to bind to port 80, the second container to start fails immediately with a "port already in use" / "address already in use" error, gets restarted by kubelet, fails again, and enters the restart loop that produces `CrashLoopBackOff`.

```bash
# Confirm the actual error
kubectl logs <pod-name> -c <second-container-name>
# Output will show something like:
# "bind: address already in use" or "port 80 is already in use"
```

> **Diagnostic note:** This is never an **IP address** conflict — each Pod gets a single unique IP regardless of how many containers it has. The conflict is always at the **port** level, because the port space is shared across containers within the same Pod's network namespace.

### Three Ways to Fix It

**Option 1 — Split into separate Pods (recommended)**

Each application gets its own Pod, its own IP, and its own port 80. No conflict possible. This is the standard production pattern — one container per Pod for primary application containers.

```yaml
# pod-nginx.yml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
    - name: nginx
      image: nginx
---
# pod-apache.yml
apiVersion: v1
kind: Pod
metadata:
  name: apache-pod
  labels:
    app: apache
spec:
  containers:
    - name: apache
      image: httpd
```

**Option 2 — Build a custom image with a different port**

If both containers genuinely need to be in the same Pod (e.g., a sidecar pattern), build a custom Dockerfile for one of them that listens on a different port:

```dockerfile
FROM httpd
# Reconfigure Apache to listen on 8080 instead of 80
RUN sed -i 's/Listen 80/Listen 8080/' /usr/local/apache2/conf/httpd.conf
EXPOSE 8080
```

```bash
docker build -t myapache:8080 .
```

```yaml
spec:
  containers:
    - name: nginx
      image: nginx          # listens on 80
    - name: apache
      image: myapache:8080  # listens on 8080 — no conflict
```

**Option 3 — Use sidecar containers that don't bind HTTP ports**

For genuine sidecar patterns (log shippers, service mesh proxies, config reloaders), the sidecar typically does not bind to port 80 at all — this scenario only arises when two *primary application* containers with overlapping default ports are placed in the same Pod, which is itself usually a design smell.

---

## ImagePullBackOff — Diagnosis Checklist

When a pod shows `ImagePullBackOff` or `ErrImagePull`, work through this checklist in order:

```bash
kubectl describe pod <pod-name>
# Read the Events section — it shows the exact error from the container runtime
```

| Check | Command | What to look for |
|---|---|---|
| 1. Image name/tag correct? | `kubectl get pod <name> -o jsonpath='{.spec.containers[*].image}'` | Typos, wrong tag (e.g. `latest` vs a version that doesn't exist) |
| 2. Image exists publicly? | `docker pull <image-name>` from a terminal | If this also fails, the image name/tag itself is wrong — not a cluster issue |
| 3. Private registry credentials? | `kubectl get secrets` | Private images need an `imagePullSecrets` entry in the pod spec |
| 4. Node-level pull working? | SSH to the worker node, run `docker pull <image>` or `crictl pull <image>` directly | If it fails on the node but works from your laptop, the node lacks network access or registry auth |
| 5. Rate limiting? | Check `kubectl describe pod` Events for "too many requests" | Docker Hub rate-limits anonymous pulls — authenticate or use a mirror |

### `imagePullPolicy` Reference

```yaml
spec:
  containers:
    - name: app
      image: myapp:v1
      imagePullPolicy: IfNotPresent   # default for tags other than "latest"
      # Always       — always pulls, even if cached locally (default for "latest" tag)
      # IfNotPresent — uses local cache if image exists
      # Never        — never pulls; fails if not already present locally
```

> **Common confusion clarified:** A pod stuck in `ImagePullBackOff` on a specific worker node — while the *same image* works on another node — is almost always a **node-level access issue** (that node lacks registry credentials, network egress, or has a corrupted local image cache) rather than an issue with the image itself. If the image were genuinely broken, **no** node would be able to schedule it successfully; Kubernetes would retry across all available nodes and fail everywhere.

---

## Helm — Package Manager for Kubernetes

### What Problem Does Helm Solve?

A real application is rarely a single YAML file. A typical deployment includes a Deployment, a Service, a ConfigMap, a Secret, a PersistentVolumeClaim, an Ingress, and a ServiceAccount — six or seven separate YAML files that must all be applied together, in the right order, with consistent naming.

Helm packages all of these into a single unit called a **chart**. One command deploys the entire application.

```bash
# Without Helm — apply each file individually
kubectl apply -f deployment.yml
kubectl apply -f service.yml
kubectl apply -f configmap.yml
kubectl apply -f secret.yml
kubectl apply -f pvc.yml
kubectl apply -f ingress.yml

# With Helm — one command
helm install my-release ./my-chart
```

### Two Main Use Cases

**1. Package your own multi-resource application**

Bundle your application's YAML files into a chart with configurable values (`values.yaml`) so the same chart can be deployed to dev, staging, and production with different settings — just like the ConfigMap pattern from earlier days, but for the entire application stack at once.

**2. Install ready-made charts for popular open-source tools**

Helm has a public chart repository (Artifact Hub) with pre-packaged charts for common tools:

```bash
# Add a chart repository
helm repo add jenkins https://charts.jenkins.io
helm repo update

# Install Jenkins with one command
helm install my-jenkins jenkins/jenkins

# Other commonly-installed charts
helm install my-argocd argo/argo-cd
helm install my-prometheus prometheus-community/kube-prometheus-stack
```

> **Practical note:** Most ready-made Helm charts assume a cloud-managed cluster — they often expect a default StorageClass (for PVCs) and a LoadBalancer-capable Service type to work out of the box. On self-hosted clusters, you may need to override these values (`--set service.type=NodePort`, `--set persistence.storageClass=manual`) for the chart to deploy successfully.

### Helm and CKA

Helm is **not part of the CKA exam syllabus** — the exam focuses on raw `kubectl` and YAML manifests, since the open-book reference allowed during the exam is the official Kubernetes documentation only (not Helm's docs). However, Helm is widely used in real-world organisations, so it is worth learning after certification — particularly for managing complex stacks like monitoring (Prometheus/Grafana) and GitOps tooling (ArgoCD).

---

## Taints and Tolerations — Quick Recap

A quick reinforcement of an earlier concept, as it came up again in Q&A:

- A **taint** is applied to a **node** — think of it as a lock on that node.
- A **toleration** is applied to a **pod** — think of it as the key that opens that specific lock.
- If a node is tainted and a pod does not carry the matching toleration, the pod is repelled from that node.

| Taint effect | Behaviour |
|---|---|
| `NoSchedule` | New pods without a matching toleration will not be scheduled on this node. Existing pods are unaffected. |
| `NoExecute` | New pods without a matching toleration will not be scheduled, **and** any existing pods without the toleration are evicted immediately. |

```bash
# Apply a taint
kubectl taint node worker-1 env=prod:NoSchedule

# A pod tolerates this taint only if it has:
tolerations:
  - key: "env"
    operator: "Equal"
    value: "prod"
    effect: "NoSchedule"
```

This pairs directly with **node affinity**: affinity *attracts* pods toward nodes with matching labels; taints/tolerations *permit or repel* pods from nodes regardless of attraction. Both can be combined: a pod can be attracted to a node via affinity AND carry the toleration required to actually land there.

---

## CKA Certification — Quick Reference

Based on the five-day course, you are well-prepared for the **CKA (Certified Kubernetes Administrator)** certification.

### Exam Details

| Detail | Value |
|---|---|
| Provider | CNCF / Linux Foundation |
| Cost | ~$395 (includes 1 free retake) |
| Format | Practical lab-based + some MCQ |
| Duration | 2 hours |
| Passing score | 66% |
| Environment | Browser-based terminal, live cluster |

### Topics Covered by This Course → CKA Exam Mapping

| Course Day | CKA Domain |
|---|---|
| Day 1–2: Docker, Pods, ReplicaSets | Workloads & Scheduling |
| Day 3: Deployments, Services, HPA | Workloads & Scheduling, Services & Networking |
| Day 4: Scheduling, Volumes, ConfigMaps, Secrets | Storage, Workloads |
| Day 5: RBAC, Namespaces, Troubleshooting, ETCD | Cluster Architecture, Troubleshooting |

### Sample CKA Question Types

```bash
# List all pods in all namespaces
kubectl get pods --all-namespaces

# Get the IP address of a pod
kubectl get pod <pod-name> -o wide

# Create a pod and output its YAML without creating it
kubectl run nginx --image=nginx --dry-run=client -o yaml

# Scale a deployment
kubectl scale deployment <name> --replicas=5

# Roll back a deployment
kubectl rollout undo deployment <name>

# Get a specific field from resource output (JSONPath)
kubectl get pod <name> -o jsonpath='{.status.podIP}'

# Create a service and expose a pod
kubectl expose pod <pod-name> --port=80 --target-port=80 --name=my-svc

# Create a namespace and deploy a pod into it
kubectl create namespace staging
kubectl run pod1 --image=nginx -n staging
```

### Next Steps Beyond CKA

| Certification | Focus |
|---|---|
| **CKA** — Certified Kubernetes Administrator | Cluster administration, scheduling, storage, networking, RBAC |
| **CKAD** — Certified Kubernetes Application Developer | Application design, workloads, config, networking (for developers) |
| **CKS** — Certified Kubernetes Security Specialist | Pod security, supply chain security, RBAC hardening, runtime security |

> **Recommendation from the instructor:** Book the exam first — having a deadline accelerates preparation. Practice on a self-hosted cluster daily. CKA aligns with everything covered in Days 1–5. Target CKA, then CKAD, then CKS if your role moves into cloud workload security.

---

## Quick-Check Questions

**Q1.** A developer runs `kubectl delete all` and accidentally wipes all your Java team's pods. How could namespaces have prevented this?

<details>
<summary>Answer</summary>

If each team's workloads were in a dedicated namespace, `kubectl delete all` (without `-n <namespace>`) only deletes resources in the current context's namespace — typically `default`. Other namespaces are unaffected. The Java team's namespace would be isolated from the deletion.

</details>

---

**Q2.** You create a new user certificate with `CN=alice`. You create a Role that allows `get` and `list` on pods in the `staging` namespace, and a RoleBinding that references `User: alice`. Alice runs `kubectl get secrets -n staging` — what happens and why?

<details>
<summary>Answer</summary>

Alice gets a `Forbidden` error. Her Role only grants `get` and `list` verbs on `pods`. The `secrets` resource is not included in her Role's `resources` list. Any resource or verb not explicitly listed in a Role is denied by default — Kubernetes RBAC is deny-by-default.

</details>

---

**Q3.** What is the difference between a Role and a ClusterRole?

<details>
<summary>Answer</summary>

A **Role** is namespace-scoped — its permissions apply only within the namespace it is created in. A **ClusterRole** is cluster-scoped — its permissions apply across all namespaces and can also grant access to cluster-level resources (nodes, persistent volumes, namespaces) that do not belong to any single namespace.

</details>

---

**Q4.** ETCD stores its data at `/var/lib/etcd`. You delete that directory. What has been lost and what has not?

<details>
<summary>Answer</summary>

Lost: all Kubernetes state — every pod, deployment, service, namespace, secret, configmap, and RBAC object recorded in the cluster database. Not lost: the physical cluster nodes (VMs) and container images cached on them are still present, but Kubernetes has no record of any workload and cannot schedule or manage them.

</details>

---

**Q5.** A worker node shows `NotReady`. You run `systemctl status kubelet` on it and see it is `active (running)`. What do you check next?

<details>
<summary>Answer</summary>

Check the container runtime: `systemctl status containerd`. If containerd is stopped or failed, kubelet cannot create containers and will stop reporting node status. If containerd is also running, read kubelet logs with `journalctl -u kubelet --since today` to look for the specific error — common causes include an incorrect API server IP/port in `/etc/kubernetes/kubelet.conf` or swap enabled on the VM.

</details>

---

**Q6.** What three IAM policies must be attached to the IAM role for an EKS node group, and why does each one exist?

<details>
<summary>Answer</summary>

**AmazonEKSWorkerNodePolicy** — allows worker nodes to authenticate to and communicate with the EKS control plane. **AmazonEKS_CNI_Policy** — allows the Amazon VPC CNI plugin to modify VPC networking, assign pod IP addresses from the VPC subnet, and configure routing. **AmazonEC2ContainerRegistryReadOnly** — allows worker nodes to pull container images from Amazon ECR (Elastic Container Registry) private repositories.

</details>

---

**Q7.** You want a service account used by the Kubernetes Dashboard to have read access to all resources in all namespaces, but no write access. What RBAC approach do you use?

<details>
<summary>Answer</summary>

Create a **ClusterRoleBinding** (cluster-scoped binding) that binds the dashboard's ServiceAccount to the built-in `view` ClusterRole. The `view` ClusterRole grants `get`, `list`, and `watch` permissions on most resources across all namespaces — but no `create`, `update`, `patch`, or `delete`. This avoids granting `cluster-admin` and follows the principle of least privilege.

</details>

---

> **Five-day series complete.** You have covered the full arc from Docker containerisation to production Kubernetes operations: container fundamentals → orchestration → services and scaling → storage and configuration → access control, observability, and cloud deployment. The next natural path is practising for the CKA certification and exploring Kubernetes security in depth (Pod Security Standards, NetworkPolicies, Secrets encryption at rest) in preparation for CKS.
