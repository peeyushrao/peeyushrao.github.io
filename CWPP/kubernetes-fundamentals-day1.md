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


The classic problem in software development is: **"The code works on my machine but not in the production environment."**

One solution is to create a package that contains not only the application code but also all its dependent libraries and runtime requirements, such as Java, Tomcat, Ubuntu, configuration files, and other dependencies. We package everything together and ship it to the production environment. Once this package is available, the user simply runs it. The application gets an environment that already contains all the required libraries and dependencies, so it behaves exactly the same way as it did during development. Anyone accessing the application over the internet is interacting with this packaged environment.

We can use Docker to create this package. Docker is a container runtime engine and is also required in the production environment. Using Docker, a developer creates a package consisting of the application code, configuration, frameworks, tools, and dependencies required for the application to run. This package is then shipped to production. The production environment only needs to run the package, and the application starts with all its dependencies already available. This is how Docker helps ensure that the application works consistently across different environments.

Docker is designed to package and run applications on any server. It bundles the application together with its libraries, frameworks, and dependencies into a single deployable unit. This process is known as **containerization**. There is technically no term called "dockerization"; Docker is simply one of the tools used to perform containerization.

A container is essentially a packaged unit that contains the application along with everything it needs to run. When the package is executed, the application runs inside the container. You can think of the container as the environment where the application lives.

Many people confuse containers with virtual machines, but they are not the same. Virtual machines are heavyweight because they contain a complete operating system and their own kernel. Containers are lightweight because they share the host operating system's kernel. A container uses resources from the host machine, whereas a virtual machine has dedicated resources and its own operating system stack. This difference makes containers much more efficient and faster to start.

When we talk about Docker and Kubernetes, the concept of a container remains the same. Docker gives us the ability to build images and run containers. An image is the packaged blueprint, and when an image is executed, it creates a container. Docker is generally focused on creating and running containers.

Kubernetes operates at a higher level. Instead of creating one container at a time, Kubernetes allows us to create and manage many containers using a single command. In Kubernetes, containers are usually grouped inside an object called a **Pod**. The concept of the container remains the same, but Kubernetes adds orchestration capabilities around it.

The term **orchestration** is very important. Orchestration means automatically managing the lifecycle of containers. It includes creating containers, deleting them, scaling them up and down, scheduling them across machines, and ensuring they remain healthy. Docker gives us the mechanism to build images and run containers, while Kubernetes provides an automated way to manage containers at scale.

Suppose I build a web application and want to run it in ten containers. Ten is actually a very small number. Imagine I want to run five hundred containers. As more users access my application, I want additional containers to be created automatically. When traffic decreases, I want the number of containers to reduce automatically. This is where clusters become important.

A cluster is simply a collection of machines, often virtual machines, working together. I might start with a cluster containing three virtual machines. Each virtual machine provides CPU and memory resources where containers can run. As user demand increases, more containers are scheduled onto these machines.

Eventually, the virtual machines themselves may run out of resources. In that case, I can scale the infrastructure. I can either increase resources on existing virtual machines (vertical scaling) or add more virtual machines to the cluster (horizontal scaling). In cloud environments, this process can even happen automatically through autoscaling.

At this point, managing everything manually becomes impossible. Who will monitor resource usage? Who will decide when to create containers or add new virtual machines? This is exactly why Kubernetes exists. Kubernetes continuously watches the state of the cluster and automatically performs these actions based on rules that we define.

Another important capability is resource management. By default, a container could potentially consume all available resources on a machine. We generally don't want that. Kubernetes allows us to define limits for CPU and memory usage. For example, we can specify that a container should use only 500 millicores of CPU or a specific amount of memory. This ensures that one application does not consume all resources and affect other workloads running on the same infrastructure.

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


# Docker — Day 1 Lab Notes

> **Official instructor notes** — companion reference to the Day 1 training session.

---

## Table of Contents

1. [Install Docker](#install-docker)
2. [Docker Images](#docker-images)
3. [Running Containers](#running-containers)
4. [Foreground Mode (`-it`)](#foreground-mode--it)
5. [Detached Mode (`-d`)](#detached-mode--d)
6. [Container Management Commands](#container-management-commands)
7. [Port Mapping](#port-mapping)
8. [Commit a Container to an Image](#commit-a-container-to-an-image)
9. [Dockerfile](#dockerfile)
10. [Jenkins CI/CD Pipeline with Docker](#jenkins-cicd-pipeline-with-docker)
11. [GitHub Actions — Build & Push Docker Image](#github-actions--build--push-docker-image)
12. [Docker Swarm — Container Orchestration](#docker-swarm--container-orchestration)
13. [Docker Stack — Multi-Service Deployment](#docker-stack--multi-service-deployment)
14. [Docker Swarm vs. Kubernetes — Quick Comparison](#docker-swarm-vs-kubernetes--quick-comparison)

---

## Install Docker

### Ubuntu 22.04

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

# Install Docker
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl start docker
```

### Amazon Linux 2023

```bash
sudo yum install -y docker
sudo yum update -y
sudo systemctl enable docker
sudo systemctl start docker
docker --version
```

---

## Docker Images

By default, no images exist on the Docker host. All images are pulled from Docker Hub.

```bash
# List images on the Docker host
docker images

# Pull an image (latest tag)
docker pull ubuntu

# Pull a specific tag
docker pull ubuntu:20.04

# View image build history and layers
docker history ubuntu
docker history ubuntu:20.04

# Delete an image
docker rmi ubuntu
docker rmi ubuntu:20.04
```

### Image Naming Format

```
registrypath/reponame/imagename:tagname
```

Examples:

```bash
docker pull ubuntu                              # docker.io/library/ubuntu:latest
docker pull sonal04/myimage:01                  # Docker Hub user image
docker pull awsRegistry/reponame/imagename      # Private registry
docker pull 172.34.56:5000/repo1/imagename      # Self-hosted registry with IP:port
```

---

## Running Containers

```bash
# Pull image and run a container (exits immediately for OS images)
docker pull ubuntu
docker run ubuntu

# List all containers (running + exited)
docker ps -a

# Run a container with a custom name
docker run --name cont1 ubuntu
```

> **Note:** When containers are in exited state, Docker allocates no CPU or memory to them.

```bash
# Check resource usage of running containers
docker stats
# Press Ctrl+C to return to terminal
```

---

## Foreground Mode (`-it`)

`-i` = interactive, `-t` = terminal. The container starts running and your terminal is attached to it.

```bash
# Run Ubuntu in foreground (interactive terminal)
docker run --name u1 -it ubuntu

# Exit the container WITHOUT stopping it
# Press: Ctrl + P, then Q

# Check status (container should still be Running)
docker ps -a

# Re-attach to a running container
docker attach <containername_or_id>
# Example:
docker attach 525ee7990ca0

# Exit the container and stop it
exit
# You return to the VM; container status becomes Exited.
```

> **Note:** `docker attach` only works on running containers. You cannot attach to an exited container.

```bash
# Start an exited container
docker start <containername_or_id>
```

---

## Detached Mode (`-d`)

The container runs in the background. You remain on the host machine.

```bash
# Run nginx in detached mode
docker run --name web -d nginx

# Run a command on a detached container (without entering it)
docker exec web uname

# Open an interactive shell inside a detached container
docker exec -it web bash
# Type exit to leave — the container keeps running

# Check running containers
docker ps

# Check container logs
docker logs <containername>

# Inspect full container details (JSON)
docker inspect <containername_or_id>
```

---

## Container Management Commands

```bash
# Stop a running container (graceful)
docker stop <containername>

# Kill a running container (immediate)
docker kill <containername>

# Delete all containers (running + stopped) forcefully
docker rm -f $(docker ps -aq)

# Delete all stopped containers AND dangling images
docker system prune --all
# Enter y to confirm
```

---

## Port Mapping

By default, a container is only accessible on its internal target port. Browsers and external users cannot reach it without port mapping.

**Rules:**
- Port mapping must be specified at `docker run` time — it cannot be added to an existing container.
- To change port mapping: delete the container and recreate it with the new `-p` flag.
- `-p` = explicit mapping; `-P` = Docker picks a random available host port.

```bash
# Explicit mapping: host port 8989 → container port 80
docker run -d -p 8989:80 --name web1 nginx

# Auto mapping: Docker assigns a free host port
docker run -d -P --name web2 httpd

# Check which host port was assigned
docker ps -a   # See the Ports column
```

Access the app in the browser:

```
http://<publicIP>:<host-port>
```

### Demo — Deploy a Custom HTML Page on nginx

```bash
# Start nginx with port mapping
docker run -d -p 8989:80 --name web1 nginx

# Enter the container
docker exec -it web1 bash

# Replace the default nginx page
cd /usr/share/nginx/html
echo "This is docker session by Sonal Mittal" > index.html
exit

# Refresh the browser — new page is live
```

---

## Commit a Container to an Image

Use `docker commit` to snapshot a customised container as a reusable image.

```bash
# Start Ubuntu and customise it
docker run -it --name cont1 ubuntu

# Inside the container:
apt-get update && apt-get install git -y
apt-get install tree -y

# Exit without stopping
# Ctrl + P, Q

# Commit the container to a new image
docker commit cont1 myimage01

docker images   # myimage01 appears in the list

# Clean up old containers
docker rm -f $(docker ps -aq)

# Run a new container from your custom image
docker run -it --name cont02 myimage01

# Verify customisations are present
git --version
tree --version

exit
```

---

## Dockerfile

A Dockerfile is a plain text file (named `Dockerfile` or `dockerfile`) containing build instructions.

```
Dockerfile → docker build → Image → docker run → Container
```

Each line is: `KEYWORD argument`  
Keywords are always UPPERCASE. Use `#` for comments.

### Dockerfile Keywords

| Keyword | Purpose | Repeatable? |
|---|---|---|
| `FROM` | Sets the base image. Always the first line. | No |
| `RUN` | Executes Linux commands during build (install packages, create dirs, run scripts). Commands run and complete before the container starts. | Yes |
| `COPY` | Copies files from the host into the container's filesystem. Cannot handle tar files. | Yes |
| `ADD` | Like `COPY` but also extracts `.tar` archives into the container. | Yes |
| `EXPOSE` | Declares the port the container application listens on. Used during port mapping. | Yes |
| `CMD` | The final command executed when the container starts. Can be overridden at runtime by passing a new command to `docker run`. | No (last wins) |

### Demo 1 — nginx Serving a Custom HTML Page

**File structure:**

```
mydockerfiles/
├── Dockerfile
└── index.html
```

```bash
sudo su -
mkdir mydockerfiles
cd mydockerfiles
vim dockerfile
```

**Dockerfile:**

```dockerfile
# Dockerfile to deploy an HTML page via nginx
FROM ubuntu
RUN apt-get update
RUN apt-get install nginx -y
COPY index.html /var/www/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**index.html:**

```html
This file is from docker
```

**Build and run:**

```bash
# Clean up first
docker rm -f $(docker ps -aq)
docker system prune --all   # enter y

# Build the image
docker build -t myimage03 .

docker images

# Run with auto port mapping
docker run -d -P myimage03
```

### Demo 2 — Python Flask Application

```bash
cd
mkdir mydockerfile1
cd mydockerfile1
vim app.py
```

**app.py:**

```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return ('\nHello from Container World! \n\n')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
```

**Dockerfile:**

```dockerfile
FROM ubuntu:20.04
RUN apt update && apt install python3 -y && apt install python3-flask -y
COPY app.py /tmp
EXPOSE 8080
CMD ["python3", "/tmp/app.py"]
```

```bash
docker build -t myimage01 .
docker run -d -P myimage01
```

---

## Jenkins CI/CD Pipeline with Docker

Before running the pipeline, grant Jenkins permission to run Docker commands:

```bash
chmod 777 /var/run/docker.sock
```

**Jenkinsfile:**

```groovy
pipeline {
    tools {
        maven 'mymaven'
    }
    agent any
    stages {
        stage('clone repo') {
            steps {
                git 'https://github.com/Sonal0409/DevOpsCodeDemo.git'
            }
        }
        stage('Build Code') {
            steps {
                sh 'mvn package'
            }
        }
        stage('build Image') {
            steps {
                sh 'cp /var/lib/jenkins/workspace/CICDpipeline/target/addressbook.war .'
                sh 'docker build -t myaddressbook .'
            }
        }
        stage('push Image') {
            steps {
                withCredentials([string(credentialsId: 'DOCKER_HUB_PASWD', variable: 'DOCKER_HUB_PASWD')]) {
                    sh 'docker login -u edu123 -p ${DOCKER_HUB_PASWD}'
                }
                sh 'docker tag myaddressbook edu123/myaddressbook'
                sh 'docker push edu123/myaddressbook'
            }
        }
        stage('Deploy container') {
            steps {
                sh 'docker run -d -P edu123/myaddressbook'
            }
        }
    }
}
```

---

## GitHub Actions — Build & Push Docker Image

Reference repo: [MavenBuild-Docker-GitHubActions](https://github.com/SkillfymeOrganization/MavenBuild-Docker-GitHubActions.git)

```yaml
name: Code build and Deploy
on: push

env:
  imageName: "myjavaapp"

jobs:
  CICDjob:
    runs-on: ubuntu-latest
    steps:
      - name: Clone the current repository on the runner
        uses: actions/checkout@v4

      - name: Setup Java 17 and maven
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
          cache: 'maven'

      - name: Build with Maven
        run: mvn package

      - name: Install docker
        uses: docker/setup-docker-action@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.imageName }}:latest

  DeployJob:
    needs: CICDjob
    runs-on: self-hosted
    steps:
      - name: Deploy the Image
        run: |
          docker run -d -P ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.imageName }}:latest
          docker ps -a
```

> **Push Docker Image to ECR:** [Video guide](https://vimeo.com/781458714/3c31cf3073)

---

## Docker Swarm — Container Orchestration

Docker Swarm is Docker's built-in orchestration tool. No separate installation required.

### Cluster Setup

**On the Manager node:**

```bash
# Clean up existing containers and images
docker rm -f $(docker ps -aq)
docker system prune --all   # enter y

# Set hostname
hostname MANAGER
sudo su -

# Initialise swarm — this generates a join token
docker swarm init
# Copy the generated token
```

**On each Worker node (repeat for WORKER1, WORKER2, ...):**

```bash
sudo hostname WORKER1
sudo su -

# Install Docker
yum install docker -y
systemctl start docker

# Join the swarm (paste the token from the manager)
# If you lost the token, regenerate it on the manager:
docker swarm join-token worker
# Then paste the output command on the worker
```

### Swarm Service Commands

```bash
# Create a service with 4 replicas
docker service create --name mysvc --replicas 4 -p 8989:80 nginx

# List services
docker service ls

# List tasks (which node each replica runs on)
docker service ps mysvc

# Scale up
docker service scale mysvc=6

# Scale down
docker service scale mysvc=2

# Rolling update (new image version)
docker service update --image sonal04/samplepyapp:v2 mysvc

# Rollback to previous version
docker service rollback mysvc

# Delete a service
docker service rm mysvc
```

### Global Mode Service

Creates exactly 1 replica on every node in the cluster. Auto-deploys to new nodes when they join.

```bash
docker service create --name mysvc --mode global nginx
```

> Cannot scale up or down — always 1 replica per node.

---

## Docker Stack — Multi-Service Deployment

Docker Stack = Docker Compose + Docker Swarm. Deploys multiple microservices across the cluster with a single command.

**myapp.yml:**

```yaml
version: '3'
services:
  redis:
    image: redis:alpine
    networks:
      - frontend
    deploy:
      replicas: 1

  db:
    image: postgres:9.4
    networks:
      - backend
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: "db"
      POSTGRES_HOST_AUTH_METHOD: "trust"
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager]

  vote:
    image: dockersamples/examplevotingapp_vote:before
    ports:
      - 5000:80
    networks:
      - frontend
    depends_on:
      - redis
    deploy:
      replicas: 2

  result:
    image: dockersamples/examplevotingapp_result:before
    ports:
      - 5001:80
    networks:
      - backend
    depends_on:
      - db
    deploy:
      replicas: 1

  worker:
    image: dockersamples/examplevotingapp_worker
    networks:
      - frontend
      - backend
    depends_on:
      - db
      - redis
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager]

networks:
  frontend:
  backend:

volumes:
  db_data:
```

```bash
# Deploy the stack
docker stack deploy -c myapp.yml myvotingapp

# List all services in the stack
docker service ls
```

Reference app: [example-voting-app](https://github.com/dockersamples/example-voting-app.git)

---

## Docker Swarm vs. Kubernetes — Quick Comparison

| Feature | Docker Swarm | Kubernetes (K8s) |
|---|---|---|
| Installation | Built into Docker — no extra install | Must be installed; available as managed service (EKS, GKE, AKS, DOKS) |
| Container runtime | Docker only | Any CRI-compatible runtime (Docker, containerd, CRI-O) |
| Roles | Manager + Worker nodes | Master + Worker nodes |
| Scheduling | Manager and Worker nodes both | Worker nodes only (by default) |
| Auto-scaling | Not supported | Horizontal Pod Autoscaler (HPA); cluster autoscaling on cloud |
| Storage | No external storage support | Persistent Volumes, Persistent Volume Claims, external storage |
| Object model | Single object type: Service | Multiple objects: Pod, ReplicaSet, Deployment, Service, Job, CronJob, etc. |
| Scheduling techniques | Basic deployment constraints | Rich scheduling (affinity, taints, tolerations, node selectors) |
| GUI dashboard | Not available in community edition | Built-in dashboard available |
| GitOps integration | Limited | Integrates with ArgoCD, FluxCD for multi-cluster management |
| Jobs / CronJobs | Not supported | Natively supported |
