# Kubernetes Services, Deployments & Auto-Scaling

> **Series:** Cloud Workload Protection — Day 3
> **Topics:** Services (ClusterIP, NodePort, LoadBalancer, Ingress, ExternalName), Deployments, Rolling Updates, Rollback, Horizontal Pod Autoscaler (HPA), Vertical Pod Autoscaler (VPA)

---

## Table of Contents

1. [Recap — Pods and ReplicaSets](#recap--pods-and-replicasets)
2. [Why Services Exist](#why-services-exist)
3. [Service Type 1 — ClusterIP](#service-type-1--clusterip)
4. [Service Type 2 — NodePort](#service-type-2--nodeport)
5. [Service Type 3 — LoadBalancer](#service-type-3--loadbalancer)
6. [Ingress — Single Load Balancer, Multiple Services](#ingress--single-load-balancer-multiple-services)
7. [ExternalName Service](#externalname-service)
8. [Deployment Object](#deployment-object)
9. [Rolling Update Strategy](#rolling-update-strategy)
10. [Rollback](#rollback)
11. [Horizontal Pod Autoscaler (HPA)](#horizontal-pod-autoscaler-hpa)
12. [Vertical Pod Autoscaler (VPA)](#vertical-pod-autoscaler-vpa)
13. [Quick-Check Questions](#quick-check-questions)

---

## Recap — Pods and ReplicaSets

Before Day 3, you should be comfortable with:

- Creating single and multi-container Pods from YAML
- Labels, selectors, and how the ReplicaSet controller uses them
- Scaling replica counts with `kubectl scale`

Day 3 builds on top of this — the focus shifts to **accessing** what is running (Services) and **updating** it safely (Deployment + Rolling Update).

**Quick ReplicaSet reference from the lab notes:**

```yaml
# replicaset.yml
kind: ReplicaSet
apiVersion: apps/v1
metadata:
  name: myrs
spec:
  replicas: 3
  selector:       # current count — query existing pods
    matchLabels:
      app: webserver
  template:       # blueprint for new pods
    metadata:
      labels:
        app: webserver
    spec:
      containers:
        - name: c1
          image: nginx
```

```bash
kubectl create -f replicaset.yml
kubectl get all
kubectl get pods -l app=webserver

# Scale up / down
kubectl scale replicaset myrs --replicas=5
kubectl scale replicaset myrs --replicas=2

# Explore YAML field reference
kubectl explain Pod
kubectl explain ReplicaSet
```

---

## Why Services Exist

Two pods in the same Kubernetes cluster can communicate with each other directly via their Pod IP addresses — the CNI (Flannel, Calico, etc.) puts all pods on the same overlay network.

**So why not just use Pod IPs?**

Three hard problems make direct Pod-IP communication impractical in production:

| Problem | Detail |
|---|---|
| **Pod IP changes on recreation** | Every time a pod is deleted and recreated (by a ReplicaSet, rolling update, or node failure), it gets a **new IP address**. Any hardcoded IP breaks. |
| **Pods are not DNS-resolvable by name** | You cannot `curl pod-1` — pod names are not registered in the cluster's DNS. |
| **Pods are not reachable from outside the cluster** | Browsers and external services cannot reach a Pod IP — it lives in the cluster's private overlay network. |

A **Service** object solves all three problems:
- It gets a stable **Cluster IP** that never changes
- It gets a **DNS name** resolvable by any pod in the cluster
- It can optionally expose a **port on every node** or create an **external load balancer**

There are five types of Services in Kubernetes. Three are covered by YAML type values; the other two are Ingress and ExternalName.

---

## Service Type 1 — ClusterIP

ClusterIP is the **default** service type. It creates a stable virtual IP address visible only **within the cluster**. Use it when two pods need to talk to each other and external access is not required.

```
Pod A  ──► Service (ClusterIP + DNS name)  ──► Pod B (nginx, port 80)
```

### YAML

```yaml
# pod-definition.yml — the target pod (web application)
apiVersion: v1
kind: Pod
metadata:
  name: pod1
  labels:
    app: webserver
spec:
  containers:
    - name: c1
      image: nginx
```

```yaml
# test-pod.yml — the client pod that will call pod1
kind: Pod
apiVersion: v1
metadata:
  name: test-pod
spec:
  containers:
    - name: c1
      image: ubuntu
      command: ["bash", "-c", "sleep 6000"]
```

```yaml
# service.yml — ClusterIP service in front of pod1
apiVersion: v1
kind: Service
metadata:
  name: mysvc
spec:
  type: ClusterIP
  selector:
    app: webserver       # routes traffic to pods with this label
  ports:
    - targetPort: 80     # container's listening port
      port: 80           # service's listening port
```

### Commands

```bash
kubectl create -f pod-definition.yml
kubectl create -f test-pod.yml
kubectl create -f service.yml

kubectl get svc                  # see the ClusterIP address
kubectl get endpoints            # verify the service has found a pod endpoint

# Test pod-to-pod communication via the service
kubectl exec -it test-pod -- bash
  apt-get update && apt-get install curl -y
  curl mysvc                     # DNS name of the service — reaches nginx
```

### Port Fields Explained

| Field | Meaning |
|---|---|
| `targetPort` | The port the container application actually listens on (e.g., nginx = 80) |
| `port` | The port the service itself listens on (clients connect here) |
| `nodePort` | (NodePort only) Port opened on every node VM — range 30000–32767 |

---

## Service Type 2 — NodePort

NodePort is a **superset of ClusterIP**. In addition to the stable cluster-internal IP, it opens a port on **every node (VM)** in the cluster. This makes the application reachable from outside the cluster via `<NodeExternalIP>:<nodePort>`.

```
Browser  ──► NodeExternalIP:30009  ──► Service (port 80)  ──► Pod (targetPort 80)
```

The NodePort range is **30000–32767**. If you omit `nodePort` in the YAML, Kubernetes picks a random available port within that range.

### YAML

```yaml
# service-nodeport.yml
apiVersion: v1
kind: Service
metadata:
  name: mysvc1
spec:
  type: NodePort
  selector:
    app: webserver
  ports:
    - targetPort: 80       # container port (mandatory)
      port: 80             # service port (mandatory)
      # nodePort: 30009    # optional — omit to let Kubernetes assign
```

### Commands

```bash
kubectl create -f service-nodeport.yml
kubectl get svc                           # note the NodePort assigned
kubectl get nodes -o wide                 # get the external IP of any worker node

# Access from browser
# http://<worker-node-external-IP>:<nodePort>
```

> **NodePort vs. ClusterIP:** Every NodePort service also has a ClusterIP. Pods within the cluster can still use the service name or ClusterIP for internal communication. NodePort just adds the external access layer on top.

> **When to use NodePort:** Testing environments and lab clusters. Not recommended for production — exposing VM IPs and high port numbers to end users is not clean. Use LoadBalancer or Ingress for production.

### Load Balancing Across Multiple Pods

When a service's selector matches multiple pods (e.g., a ReplicaSet of 3 nginx pods), the service automatically load balances requests across all matching pod endpoints in round-robin fashion.

```bash
kubectl get endpoints    # shows all pod IPs the service forwards to
```

> **Important rule:** Each application should have its own dedicated Service. Do not use one service to front pods running different applications — the service only checks labels, not images. A service pointing to pods running nginx AND Apache will forward traffic to both unpredictably.

---

## Service Type 3 — LoadBalancer

LoadBalancer is a **superset of NodePort** (which is itself a superset of ClusterIP). It is designed for **cloud-hosted clusters** (EKS, GKE, AKS). When you create a LoadBalancer service, Kubernetes instructs the cloud provider's API to provision a **managed network load balancer** automatically.

```
Internet  ──► Cloud Load Balancer (External IP)  ──► NodePort  ──► Service  ──► Pods
```

The load balancer gets a **public external IP** which you can register with your DNS provider. End users reach your application via that IP — no node IPs or high port numbers exposed.

### YAML

```yaml
# service-lb.yml
apiVersion: v1
kind: Service
metadata:
  name: mysvc
spec:
  type: LoadBalancer
  selector:
    app: webserver
  ports:
    - targetPort: 80
      port: 80
      # No nodePort needed — Kubernetes assigns it automatically
```

### Commands

```bash
kubectl create -f service-lb.yml
kubectl get svc
# EXTERNAL-IP column shows the load balancer's public IP once provisioned
# (may show <pending> for 30–60 seconds while cloud provisions it)
```

### What a LoadBalancer service creates internally

| Layer | What gets created |
|---|---|
| ClusterIP | Stable internal IP for pod-to-pod communication |
| NodePort | Port on every node for cluster-to-external routing |
| Cloud LB | Managed load balancer with public IP, provisioned by the cloud provider |

> **Cost consideration:** Every LoadBalancer service provisions a separate cloud load balancer. At scale (30–40 services), this becomes expensive to manage and pay for. This is where **Ingress** solves the problem with a single load balancer routing to multiple services.

---

## Ingress — Single Load Balancer, Multiple Services

Ingress is **not a Service type** — it is a separate Kubernetes object. It creates a single application load balancer (Layer 7) that routes incoming HTTP/HTTPS requests to different Services based on the **hostname** or **URL path** in the request.

```
Internet
    │
    ▼
Ingress Controller (single cloud LB, single external IP)
    │
    ├── website01.example.com  ──► Service1  ──► Pod1 (nginx)
    └── website02.example.com  ──► Service2  ──► Pod2 (nginx)
```

This is equivalent to AWS ALB (Application Load Balancer) path/host routing.

### Setup

**Step 1 — Install the nginx Ingress Controller**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.2.1/deploy/static/provider/cloud/deploy.yaml
```

**Step 2 — Create the backend pods and services**

```bash
kubectl run pod1 --image nginx
kubectl run pod2 --image nginx

kubectl expose pod pod1 --name service1 --port=80 --target-port=80
kubectl expose pod pod2 --name service2 --port=80 --target-port=80

kubectl get svc   # note ClusterIPs of service1 and service2
```

**Step 3 — Customise the pod HTML (optional — for testing)**

```bash
kubectl exec -it pod1 -- bash
  cd /usr/share/nginx/html
  echo "this is website1" > index.html

kubectl exec -it pod2 -- bash
  cd /usr/share/nginx/html
  echo "this is website2" > index.html
```

**Step 4 — Create a frontend test pod**

```bash
kubectl run frontend-pod --image ubuntu --command -- sleep 36000
```

**Step 5 — Create the Ingress object**

```yaml
# ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: name-virtual-host-ingress
spec:
  ingressClassName: nginx
  rules:
    - host: website01.example.com
      http:
        paths:
          - pathType: Prefix
            path: "/"
            backend:
              service:
                name: service1
                port:
                  number: 80
    - host: website02.example.com
      http:
        paths:
          - pathType: Prefix
            path: "/"
            backend:
              service:
                name: service2
                port:
                  number: 80
```

```bash
kubectl apply -f ingress.yml
kubectl get ingress
kubectl describe ingress name-virtual-host-ingress

# Get the load balancer external IP assigned to the Ingress controller
kubectl get svc -n ingress-nginx
# Note the EXTERNAL-IP (e.g., 34.135.243.240)
```

**Step 6 — Test from the frontend pod**

```bash
kubectl exec -it frontend-pod -- bash
  nano /etc/hosts
  # Add this line:
  # 34.135.243.240 website01.example.com website02.example.com

  curl website01.example.com    # returns "this is website1"
  curl website02.example.com    # returns "this is website2"
```

**Step 7 — Test from your laptop browser (Windows)**

Open Notepad as Administrator → open `C:\Windows\System32\Drivers\etc\hosts` → add:

```
34.135.243.240 website01.example.com website02.example.com
```

Save. Visit `http://website01.example.com` and `http://website02.example.com` in the browser.

```bash
kubectl get ingressclass    # verify the ingressClassName value to use in YAML
```

---

## ExternalName Service

ExternalName is a special service type that maps a Kubernetes DNS name to an **external domain** outside the cluster. No proxy or load balancing is created — the DNS resolution simply returns a CNAME to the external hostname.

**Use case:** A pod inside the cluster needs to call an external API or legacy system. Instead of hardcoding the external URL inside the application, you define a Service and the application calls the service name. If the external URL ever changes, you update the Service — not the application.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-external-service
spec:
  type: ExternalName
  externalName: www.google.com
```

```bash
# From inside any pod:
kubectl exec -it test-pod -- bash
  curl my-external-service    # DNS resolves to www.google.com
```

---

## Deployment Object

In production you will almost never write a bare `Pod` or `ReplicaSet` YAML. The standard object is a **Deployment**.

### Deployment vs. ReplicaSet

| Feature | ReplicaSet | Deployment |
|---|---|---|
| Create and maintain replicas | ✅ | ✅ |
| Scale up / scale down | ✅ | ✅ |
| Update to a new image version | ❌ | ✅ (rolling update) |
| Rollback to previous version | ❌ | ✅ |
| Maintains update history | ❌ | ✅ (via multiple ReplicaSets) |

### How a Deployment works internally

```
Deployment (desired: 3 replicas of v1)
    │
    └──► ReplicaSet-1  ──► Pod-v1, Pod-v1, Pod-v1

# After image update to v2:
Deployment
    ├──► ReplicaSet-1 (scaled to 0)   ← old pods
    └──► ReplicaSet-2 (scaled to 3)   ← new v2 pods

# After rollback to v2 (from broken v3):
Deployment
    ├──► ReplicaSet-1 (count: 0)   ← v1 pods (kept for history)
    ├──► ReplicaSet-2 (count: 3)   ← v2 pods (restored)
    └──► ReplicaSet-3 (count: 0)   ← v3 pods (scaled down)
```

Deployments **keep all previous ReplicaSets** at count zero — this is what enables rollback. You are never deleting history; you are just shifting which ReplicaSet holds the active count.

### Deployment YAML

```yaml
# deployment.yml
kind: Deployment
apiVersion: apps/v1
metadata:
  name: kubeserve
spec:
  replicas: 3
  minReadySeconds: 10        # wait 10s after a new pod is ready before proceeding
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1      # max old pods to delete at a time
      maxSurge: 1            # max new pods to create above desired count at a time
  selector:
    matchLabels:
      app: kubeserve
  template:
    metadata:
      name: kubeserve
      labels:
        app: kubeserve
    spec:
      containers:
        - name: app
          image: leaddevops/kubeserve:v1
```

### Commands

```bash
kubectl create -f deployment.yml
kubectl get deployment
kubectl get all        # shows deployment + replicaset + pods

# Scale
kubectl scale deployment kubeserve --replicas=5
kubectl scale deployment kubeserve --replicas=2

# Check deployed image
kubectl get deployment -o wide    # shows container name and current image
```

---

## Rolling Update Strategy

The rolling update strategy replaces pods one by one (or in configurable batches) so that the application remains available throughout the update. Zero downtime is the goal.

### Strategy Parameters

| Parameter | Meaning |
|---|---|
| `maxUnavailable` | How many old pods can be deleted at once. Can be a number or percentage (e.g., `25%`). |
| `maxSurge` | How many new pods above the desired count can be created at once. |
| `minReadySeconds` | How many seconds to wait after a new pod becomes Ready before it is considered stable and the next step proceeds. |

**Example with `replicas: 3`, `maxSurge: 1`, `maxUnavailable: 1`:**

```
Start:   v1, v1, v1   (3 pods)
Step 1:  v1, v1, v1, v2   (create 1 new — surge = 4 total)
Step 2:  v1, v1, v2   (delete 1 old — back to 3)
Step 3:  v1, v1, v2, v2   (create 1 new)
Step 4:  v1, v2, v2   (delete 1 old)
Step 5:  v1, v2, v2, v2   (create 1 new)
Step 6:  v2, v2, v2   (delete last old — done)
```

At no point are all pods down. At least 2 pods are always serving traffic.

### Performing a Rolling Update

```bash
# Update to v2
kubectl set image deployment kubeserve app=leaddevops/kubeserve:v2

# Watch the rollout progress
kubectl rollout status deployment kubeserve

# Update to v3
kubectl set image deployment kubeserve app=leaddevops/kubeserve:v3
kubectl rollout status deployment kubeserve
```

> **Alternative update strategy — Recreate:** Setting `strategy.type: Recreate` deletes all old pods first, then creates new ones. Simple, but causes downtime. Use only when running two image versions simultaneously would cause conflicts (e.g., database schema migrations).

---

## Rollback

If the new image is faulty (application errors, failed health checks, CrashLoopBackOff), roll back to the previous version:

```bash
# Roll back one step (to the previous ReplicaSet)
kubectl rollout undo deployment kubeserve

# Check rollout history
kubectl rollout history deployment kubeserve

# Roll back to a specific revision number
kubectl rollout undo deployment kubeserve --to-revision=2
```

Rolling back works because the previous ReplicaSet is still present (at replica count 0). Kubernetes scales it back up and scales the current one down using the same rolling strategy.

---

## Horizontal Pod Autoscaler (HPA)

Manual scaling (`kubectl scale`) requires a human decision. HPA automates it: when CPU (or memory) utilisation on the existing pods crosses a threshold, Kubernetes automatically adds more pods. When load drops, it scales back down.

```
Load increases
    │
    ▼
CPU utilisation on pods > threshold
    │
    ▼
HPA creates new pods (up to maxReplicas)
    │
Load decreases
    │
    ▼
HPA terminates excess pods (down to minReplicas)
```

### Prerequisites — Install Metrics Server

HPA relies on real-time resource metrics from the **Metrics Server**.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Apply the patch needed for self-hosted clusters (TLS certificate bypass)
wget -c https://gist.githubusercontent.com/initcron/1a2bd25353e1faa22a0ad41ad1c01b62/raw/008e23f9fbf4d7e2cf79df1dd008de2f1db62a10/k8s-metrics-server.patch.yaml
kubectl patch deploy metrics-server -p "$(cat k8s-metrics-server.patch.yaml)" -n kube-system

kubectl get pods -n kube-system    # metrics-server pod should be Running
```

### HPA YAML (combined with Deployment and Service)

All three objects can be defined in a single file separated by `---`:

```yaml
# hpa.yml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      name: nginxpod
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          resources:
            limits:
              cpu: 10m          # very low CPU limit — makes it easy to trigger HPA in labs
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-svc
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 5    # scale up when avg CPU > 5% of limit
```

### Commands

```bash
kubectl delete all --all
kubectl create -f hpa.yml
kubectl get all

# Monitor HPA status
kubectl get hpa

# Real-time resource usage
kubectl top pods
```

### Generating Load to Trigger Scale-Up

```bash
# Open a second terminal and run the load generator pod
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- \
  /bin/sh -c "while sleep 0.01; do wget -q -O- http://<Service-ClusterIP>:80; done"

# Watch pods scale up in the first terminal
kubectl get pods
kubectl top pods
```

When you stop the load generator (Ctrl+C), HPA detects the drop in CPU utilisation and begins terminating the excess pods. There is a **scale-down cooldown** (default: a few minutes) — this prevents thrashing when load is intermittent.

> **HPA behaviour when maxReplicas is reached:** If requests keep arriving but all pods are at their CPU limit and `maxReplicas` has been hit, the application will start returning errors. HPA cannot scale beyond the configured maximum. Size `maxReplicas` appropriately for your expected peak.

---

## Vertical Pod Autoscaler (VPA)

HPA adds more pods. VPA does the opposite — it **increases the CPU and memory allocated to existing pods** when they need more resources, rather than adding new ones.

| | HPA | VPA |
|---|---|---|
| Scales | **Out** — adds/removes pods | **Up** — increases/decreases resources per pod |
| Use case | Stateless apps where adding instances helps | Apps that cannot be horizontally scaled (stateful, single-instance) |
| Disruption | Non-disruptive (new pods, old stay running) | **Disruptive** — pod must be restarted to change its resource allocation |
| Default availability | Built-in (via Metrics Server) | Must be installed separately from GitHub |
| Commonly used? | Yes — standard production practice | Less common due to disruption |

### How VPA Works

1. VPA's **Recommender** monitors actual CPU/memory usage of the target pods
2. It calculates a recommended resource allocation
3. Based on `updateMode`:
   - `Auto` — restarts the pod with the new resource allocation automatically
   - `Off` — only provides recommendations; does not change anything

VPA does **not** increase resources by fixed steps (e.g., 50m → 100m → 150m). It recommends exactly the amount needed based on observed usage, which may be 73m or 128m.

### Installation

```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh

kubectl get pods -n kube-system    # VPA components should appear
```

### Resource Limits and Requests

Understanding `limits` and `requests` is essential for VPA (and for Kubernetes scheduling generally):

| Field | Meaning |
|---|---|
| `requests.cpu` | **Minimum** guaranteed CPU the node reserves for this container. The scheduler uses this to decide which node to place the pod on. |
| `limits.cpu` | **Maximum** CPU the container is allowed to use. If exceeded, the container is throttled (for CPU) or OOMKilled (for memory). |

```yaml
resources:
  requests:
    cpu: 50m       # guaranteed minimum — scheduler reserves this
  limits:
    cpu: 50m       # hard ceiling — cannot use more than this
```

VPA works within the bounds you define in its own YAML — `minAllowed` and `maxAllowed` — not within the pod's own requests/limits. It is allowed to change the pod's requests/limits **up to** the VPA-defined max.

### VPA YAML Example

```yaml
# vpa.yml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stress-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stress
  template:
    metadata:
      labels:
        app: stress
    spec:
      containers:
        - name: stress-container
          image: ubuntu
          resources:
            requests:
              cpu: 50m      # starting allocation
            limits:
              cpu: 50m
          command:
            - /bin/bash
            - -c
            - "apt-get update && apt-get install -y stress-ng && stress-ng --cpu 1 --timeout 0"
---
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: stress-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: stress-app
  updatePolicy:
    updateMode: "Auto"        # automatically restart pods with new resources
  resourcePolicy:
    containerPolicies:
      - containerName: stress-container
        minAllowed:
          cpu: 100m           # VPA will not allocate less than 100m
        maxAllowed:
          cpu: 200m           # VPA will not allocate more than 200m
```

### Monitoring VPA Behaviour

```bash
kubectl apply -f vpa.yml
kubectl get pods
kubectl top pods                            # watch CPU usage climb due to stress-ng

# After VPA acts:
kubectl describe vpa stress-vpa             # see recommendations
kubectl get pods                            # pods will restart with updated resources
kubectl top pods                            # CPU allocation should have increased
```

**Expected sequence:**
1. Pods start at 50m CPU
2. `stress-ng` consumes CPU — utilisation exceeds 50m
3. VPA recommends a higher allocation (e.g., 126m)
4. VPA (in `Auto` mode) restarts the pods — new pods start with ~100–126m CPU
5. As stress continues, VPA may recommend up to 200m (the configured max)

> **VPA assignment:** Try this as a lab exercise — it is not mandatory course content but demonstrates Kubernetes resource management at a deeper level.

---

## Quick-Check Questions

**Q1.** A pod's IP address is `10.244.1.5`. It gets deleted and recreated by a ReplicaSet. Can you still send requests to `10.244.1.5`? What should you use instead?

<details>
<summary>Answer</summary>

No. When a pod is recreated, it gets a new IP address. The old IP is no longer valid. You should create a **Service** in front of the pod. The Service gets a stable ClusterIP and DNS name that never changes, even as pods behind it are recreated.

</details>

---

**Q2.** What are the three port fields in a NodePort service YAML, and which one is optional?

<details>
<summary>Answer</summary>

`targetPort` — the container's listening port (mandatory). `port` — the service's listening port (mandatory). `nodePort` — the port opened on every node VM in the 30000–32767 range (optional — Kubernetes assigns a random port within the range if omitted).

</details>

---

**Q3.** You have 40 microservices, each needing external access. Why is LoadBalancer service type problematic at this scale, and what should you use instead?

<details>
<summary>Answer</summary>

Each LoadBalancer service provisions a separate cloud load balancer, which is a paid resource. 40 services mean 40 load balancers — expensive and difficult to manage. Use **Ingress** instead — it creates a single application load balancer that routes to multiple services based on hostname or URL path rules.

</details>

---

**Q4.** What is the key difference between a ReplicaSet and a Deployment? When would you choose one over the other?

<details>
<summary>Answer</summary>

A ReplicaSet maintains a desired pod count and provides high availability, but it cannot update the running image version or roll back changes. A Deployment wraps a ReplicaSet and adds rolling update and rollback capabilities by maintaining multiple ReplicaSets at different replica counts. In practice, always use Deployment — you will almost never write a bare ReplicaSet YAML in production.

</details>

---

**Q5.** During a rolling update with `maxSurge: 1` and `maxUnavailable: 1` on a 3-replica deployment, what is the minimum number of pods serving traffic at any point during the update?

<details>
<summary>Answer</summary>

2 pods. `maxUnavailable: 1` means at most 1 old pod is deleted at a time. With 3 replicas, at least 2 pods (desired 3 minus 1 unavailable) are always running and available to serve traffic.

</details>

---

**Q6.** What happens to HPA when the load drops after scaling up?

<details>
<summary>Answer</summary>

HPA detects that CPU utilisation has fallen below the target threshold. After a scale-down cooldown period (default ~5 minutes, to prevent thrashing), it begins terminating the excess pods until the count returns to `minReplicas` or until utilisation stabilises at the threshold.

</details>

---

**Q7.** What is the fundamental difference between HPA and VPA, and why is VPA considered "disruptive"?

<details>
<summary>Answer</summary>

HPA scales **out** — it adds or removes pod instances. VPA scales **up** — it increases or decreases the CPU/memory allocation of existing pods. VPA is disruptive because changing a pod's resource allocation requires restarting the pod; Kubernetes cannot change CPU/memory limits on a running container. HPA is non-disruptive because new pods are added alongside existing ones.

</details>

---

> **Up next — Day 4:** Volumes, Persistent Volumes, Persistent Volume Claims, ConfigMaps, Secrets, Kubernetes scheduling techniques (node affinity, taints and tolerations).
