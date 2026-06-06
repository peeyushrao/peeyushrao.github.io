# Docker & Containerization Fundamentals

> **Series:** Cloud Workload Protection — Day 1  
> **Topics:** Physical servers → VMs → Containers, Docker core commands, container lifecycle, port mapping, Dockerfile authoring

---

## Table of Contents

1. [From Physical Servers to Containers](#from-physical-servers-to-containers)
2. [What Is a Container?](#what-is-a-container)
3. [Core Docker Commands](#core-docker-commands)
4. [Container Lifecycle & Modes](#container-lifecycle--modes)
5. [Port Mapping](#port-mapping)
6. [Dockerfile & Custom Images](#dockerfile--custom-images)
7. [Deploying Applications — End-to-End](#deploying-applications--end-to-end)
8. [Quick-Check Questions](#quick-check-questions)

---

## From Physical Servers to Containers

Application deployment has evolved through three distinct eras. Understanding *why* each era emerged makes Docker's design decisions intuitive.

### Era 1 — Physical Servers

In the pre-virtualisation era, each application was deployed on a dedicated physical server. A high-spec machine — say, 256 GB RAM, 32 CPUs — was handed to a team, an OS was installed, a runtime (Java, .NET) was installed on top, then the app server (Tomcat, JBoss), and finally the build artifact was placed.

**Problems:**
- The application might use only 10–16 GB of the available resources. The rest was wasted.
- No other application could run on the same machine.
- No auto-scaling; no monitoring of concurrent users.
- Expensive hardware, entirely dedicated to one workload.

### Era 2 — Virtual Machines

Hypervisor software (VMware, VirtualBox, Hyper-V) partitioned a single physical host into multiple virtual machines. Each VM got a slice of resources, its own OS, and its own application stack. Cloud VMs (AWS EC2, Azure VMs, GCP Compute) work on the same principle.

**Improvements over physical servers:**
- Multiple applications could share one host.
- Better resource utilisation.

**Remaining problems:**
- **Fixed allocation:** Once a VM is created with 50 GB, those 50 GB are reserved — whether the app uses them or not. You pay for the allocation, not the usage.
- **Heavyweight:** VMs carry a complete operating system. Your application may only need a few Java libraries, yet the VM ships Windows or Ubuntu with everything pre-installed — anti-virus, SQL Server, all default services — consuming resources you never use.
- **Slow to scale:** Spinning up 500 VMs, configuring them, and getting approvals takes significant time. Scaling cannot happen in seconds.

### Era 3 — Containers

Install a **container runtime** (Docker, containerd) on any host — physical or virtual — and it gives you containers instead of VMs. Containers solve all three problems above.

| | Virtual Machines | Containers |
|---|---|---|
| Resources | Fixed on creation | Allocated dynamically, freed on stop |
| OS overhead | Full OS per VM | Only required OS libraries |
| Spin-up time | Minutes | Seconds |
| Scaling | Slow, approval-gated | Thousands in seconds |
| Cost | Pay for allocation | Pay for actual use |

> **Real-world scale:** Google creates and terminates millions of containers per week. That's the level of agility containers enable.

---

## What Is a Container?

A container is a **lightweight, isolated process** created by a container runtime like Docker. It is not a virtual machine.

A container has:
- Its own **network**
- Its own **storage and file system**
- The **OS library files** the application depends on
- The **application** itself and its runtime libraries

A container does **not** have:
- A full kernel
- A complete operating system
- Any software beyond what the application needs

This is why containers are called lightweight. An nginx container, for example, carries only Debian base libraries (enough for nginx to run) — not a full Debian installation. Tools like `sudo`, `curl`, or `apt` may not exist unless explicitly installed.

> **Key distinction:** Containers share the host's kernel. What they package is the *user-space* OS libraries the application depends on — not the kernel itself.

---

## Core Docker Commands

Every Docker workflow centers on two objects: **images** (packaged snapshots) and **containers** (running instances of images).

| Command | What it does |
|---|---|
| `docker images` | List all images stored locally |
| `docker pull <image>` | Download an image from Docker Hub (rarely needed — `run` does this automatically) |
| `docker run <image>` | Pull if absent, then create and start a new container. Every `run` creates a **new** uniquely-identified container. |
| `docker ps` | List running containers only |
| `docker ps -a` | List all containers (running + exited) |
| `docker start <name/id>` | Start a stopped container without creating a new one |
| `docker stop <name/id>` | Gracefully stop a running container |
| `docker rm <name/id>` | Delete a container permanently |
| `docker rmi <image>` | Delete an image from local storage |
| `docker exec -it <name> bash` | Open an interactive shell inside a running container |
| `docker attach <name>` | Re-attach your terminal to a container's default process |
| `docker build -t <name> .` | Build an image from the Dockerfile in the current directory |

> **`docker run` vs. `docker start`:** `run` always creates a *brand new* container. `start` restarts an *existing, stopped* container. Running the same image 10 times with `run` gives you 10 separate containers, each with a unique ID and name.

---

## Container Lifecycle & Modes

When you run an image, the container executes the command defined in the image's `CMD` instruction. Understanding the default command determines which mode flag to use.

### Foreground Mode — `-it`

```bash
docker run -it ubuntu
```

Attaches your terminal to the container's terminal. Use this when the image's default command is a shell (`/bin/bash`, `python`, `sh`). You are effectively "inside" the container.

- **Exit without stopping:** `Ctrl+P`, then `Ctrl+Q`
- **Exit and stop:** type `exit` — this sends a stop signal to the container

### Detached Mode — `-d`

```bash
docker run -d nginx
```

Container runs in the background. You remain on the host machine. Use this for web applications, databases, and any image whose default process is an application server rather than a terminal.

### The `-itd` Pattern

For OS-level and programming language images (Ubuntu, Python, Node), the default CMD is a terminal process (`/bin/bash`). Giving only `-d` causes the container to exit immediately because there is nothing to keep it alive interactively. The correct flag is `-itd`:

```bash
docker run -itd --name mybox ubuntu
```

This creates the container, keeps it running in the background, but does not attach your terminal to it.

> **Rule of thumb:** If the image's default CMD is a terminal → use `-itd`. If it's an application (nginx, Tomcat, Jenkins) → use `-d` alone.

### Entering a Running Container

The `exec` command is how you interact with any running container — including in Kubernetes (`kubectl exec`):

```bash
# Open a bash shell inside a running container
docker exec -it <container-name> bash

# Run a one-off command without entering the shell
docker exec <container-name> ls /usr/share/nginx/html
```

### Container Lifecycle Summary

```
docker run -itd ubuntu
        ↓
Container CREATED (new unique ID + name)
        ↓
Container RUNNING (CMD process executing)
        ↓
  ┌─────────────┐
  │  Ctrl+P+Q   │ → Container stays RUNNING, you exit terminal
  │  exit       │ → Container STOPPED
  └─────────────┘
        ↓ (if stopped)
docker start <name>   → Container RUNNING again
docker rm <name>      → Container DELETED permanently
```

---

## Port Mapping

Containers run inside Docker's **private network namespace**. Even if nginx is listening on port 80 inside a container, your browser cannot reach it — requests stop at the host machine's network boundary.

### Why Direct Access Fails

```
Your laptop browser → Host VM (port 80) → ✗ Docker network → Container (port 80)
```

The request reaches the VM but Docker's internal network is not reachable from outside without a bridge.

### Port Mapping Builds the Bridge

Port mapping is declared at container creation time with `-p` or `-P`. You **cannot add or change port mapping on an existing container** — you must delete and recreate it.

```bash
# Auto-assign a free host port → container's exposed port
docker run -d --name web1 -P nginx

# Specify explicitly: host port 8080 → container port 80
docker run -d --name web2 -p 8080:80 nginx

# Check the assigned port
docker ps   # look at the Ports column
```

**Capital `-P`** lets Docker pick any available host port automatically.  
**Lowercase `-p host:container`** gives explicit control.

### Accessing the Application

```
http://<VM-public-IP>:<host-port-from-docker-ps>
```

The container port (target port) comes from the `EXPOSE` instruction in the image's Dockerfile. The host port is what Docker assigns or what you specify.

> **Analogy:** The VM is one side of a river; the container is a resort on the far bank. Without a bridge, you cannot cross. Port mapping constructs the bridge — forwarding traffic from the VM bank to the container bank.

---

## Dockerfile & Custom Images

A **Dockerfile** is a plain text file (filename: `Dockerfile`, no extension) containing ordered build instructions. Docker reads it top to bottom to produce a custom image. Every custom image must be based on an existing Docker image — you never start from bare hardware.

### Core Dockerfile Keywords

| Keyword | Purpose | Repeatable? |
|---|---|---|
| `FROM` | Sets the base image. **Mandatory first instruction.** | No |
| `RUN` | Executes a Linux command during the build step (install packages, create dirs). | Yes |
| `COPY` | Copies files/directories from the host into the container filesystem. | Yes |
| `ADD` | Like `COPY`, but also extracts tar/compressed archives. | Yes |
| `EXPOSE` | Declares the port the containerised application listens on. | Yes |
| `CMD` | The default command that runs when the container starts. Can be overridden at runtime. | No (last wins) |
| `LABEL` | Metadata key-value pairs (e.g., maintainer info). Replaces deprecated `MAINTAINER`. | Yes |
| `ENV` | Sets environment variables. Referenced as `${VAR_NAME}` elsewhere in the file. | Yes |

> **Sequence matters:** `FROM` is always first. `RUN` steps execute in order — ensure dependencies are installed before the `COPY` step that needs them. `CMD` belongs last.

### Example 1 — nginx with Custom HTML

```dockerfile
FROM ubuntu
LABEL maintainer="peeyush.rao@example.com"
RUN apt-get update
RUN apt-get install -y nginx
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Example 2 — Java WAR on Tomcat

```dockerfile
FROM tomcat
# Tomcat image brings Java and Oracle Linux automatically
LABEL maintainer="peeyush.rao@example.com"
COPY addressbook.war /usr/local/tomcat/webapps/
EXPOSE 8080
CMD ["catalina.sh", "run"]
```

### Example 3 — Python Flask Application

```dockerfile
FROM ubuntu
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install flask
COPY app.py /tmp/app.py
EXPOSE 80
CMD ["python3", "/tmp/app.py"]
```

### Choosing the Right Base Image

| Your application | Base image to use |
|---|---|
| Static HTML + nginx | `FROM ubuntu` (install nginx via RUN) or `FROM nginx` |
| Java WAR / embedded Tomcat | `FROM tomcat` |
| Node.js application | `FROM node` |
| Python application | `FROM python` or `FROM ubuntu` + install python3 |

> Using `FROM tomcat` automatically pulls Java and its underlying OS. You do not need to install Java manually. The same principle applies to all runtime-specific base images.

### `COPY` vs. `ADD`

Use `COPY` for regular files and directories.  
Use `ADD` when you need to copy and extract compressed archives (`.tar`, `.tar.gz`).

### `CMD` vs. Runtime Command Override

`CMD` defines the default container startup command. It can be replaced at runtime:

```bash
# Default CMD (bin/bash) runs
docker run -it ubuntu

# Override: sleep runs instead of bash
docker run ubuntu sleep 60
```

### Building the Image

```bash
# Build from Dockerfile in current directory
docker build -t my-image:v1 .

# Build from Dockerfile in a different path
docker build -t my-image:v1 -f /path/to/Dockerfile .
```

---

## Deploying Applications — End-to-End

The complete workflow from code to running container:

**Step 1 — Write the Dockerfile**

Create a file named `Dockerfile` in your project directory. Define: base image, package installation, code copy, expose port, startup command.

**Step 2 — Build the image**

```bash
docker build -t my-app:v1 .
```

Docker executes each instruction in order. If a step fails (e.g., the `COPY` source file doesn't exist), the build stops with an error at that step.

**Step 3 — Run the image**

```bash
docker run -d -P --name my-app my-app:v1
```

**Step 4 — Access the application**

```bash
docker ps   # note the host port in the Ports column
# Open: http://<VM-public-IP>:<host-port>
```

**Step 5 — Iterate if needed**

```bash
# Make ad-hoc changes inside the running container
docker exec -it my-app bash

# Or modify the Dockerfile, rebuild, and redeploy
docker build -t my-app:v2 .
docker run -d -P --name my-app-v2 my-app:v2
```

### Image, Dockerfile, and Container Independence

These three objects are independent:

- You can **delete the Dockerfile** — the image still exists.
- You can **delete the image** — running containers continue as independent processes.
- You can **modify a running container** and commit it to a new image with `docker commit`.

```bash
# Commit a modified container to a new image
docker commit <container-name> my-app:modified
```

---

## Quick-Check Questions

Test your understanding before Day 2.

**Q1.** What problem did virtualisation solve that physical servers couldn't, and what problems did it leave unsolved?

<details>
<summary>Answer</summary>

Virtualisation allowed multiple applications to share one physical server by partitioning resources via a hypervisor. Problems left unsolved: resources are fixed per VM whether used or not, VMs carry a full OS (heavyweight), and scaling hundreds of VMs is slow and often requires approvals.

</details>

---

**Q2.** What is the difference between `docker run` and `docker start`?

<details>
<summary>Answer</summary>

`docker run` creates a brand-new container from an image every time it is called. `docker start` restarts an existing, previously-stopped container without creating a new one.

</details>

---

**Q3.** When would you use `-itd` vs. `-d` when running a container?

<details>
<summary>Answer</summary>

Use `-itd` for OS or language images (Ubuntu, Python, Node) whose default `CMD` is a terminal (`/bin/bash`). The `-it` flags interact with the terminal process to keep it alive while `-d` keeps you on the host. Use plain `-d` for web app or database images (nginx, Tomcat) whose default `CMD` is an application process, not a terminal.

</details>

---

**Q4.** Why can't you access a container's application directly via the host machine's IP without port mapping?

<details>
<summary>Answer</summary>

Containers run inside Docker's private network namespace. Requests to the host machine stop at the host's network boundary and do not reach Docker's internal network. Port mapping creates a forwarding rule from a host port to the container port, bridging the two networks.

</details>

---

**Q5.** What is the difference between `COPY` and `ADD` in a Dockerfile?

<details>
<summary>Answer</summary>

Both copy files from the host into the container's filesystem. `COPY` handles regular files and directories. `ADD` additionally extracts compressed tar/archive files into the destination directory.

</details>

---

**Q6.** What does `CMD` do in a Dockerfile, and can it be overridden?

<details>
<summary>Answer</summary>

`CMD` defines the default command that runs when the container starts, keeping the container alive. Yes — it can be overridden at runtime by appending a new command to `docker run`. For example, `docker run ubuntu sleep 60` replaces the default `/bin/bash` with a sleep command.

</details>

---

> **Up next — Day 2:** Container orchestration. Comparing Docker Swarm and Kubernetes, Kubernetes architecture, setting up a cluster, and Pods (containers in Kubernetes). The `docker exec` pattern you learned today carries directly into `kubectl exec`.
