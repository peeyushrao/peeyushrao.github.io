# Kubernetes Training – Day 1 Study Guide
Based on the Day 1 transcript (Docker & Containerization Foundations)

## Learning Objectives
By the end of Day 1 you should understand:

- SDLC deployment concepts
- Physical servers vs Virtual Machines vs Containers
- Why Docker exists
- Docker Images vs Containers
- Docker Hub and Registries
- Dockerfile fundamentals
- Common Docker commands
- Port Mapping
- Building and running applications in containers
- Foundation for Kubernetes

---

# 1. Application Deployment Evolution

```text
Developer Code
      |
      v
    Build
      |
      v
  Artifact (.war/.jar/.apk/.msi)
      |
      v
   Deployment
      |
      v
 Application Available to Users
```

## Deployment
Deployment means moving a built application to a server and making it available to users.

Examples:
- .war
- .jar
- .apk
- .msi

---

# 2. Three Generations of Deployment

## Generation 1: Physical Servers

```text
+--------------------------------+
| Physical Server                |
| Ubuntu                         |
| Java                           |
| Tomcat                         |
| Application                    |
+--------------------------------+
```

Problems:
- Resource wastage
- Difficult scaling
- Expensive hardware
- Low utilization

---

## Generation 2: Virtual Machines

```text
+----------------------------------+
| Physical Host                    |
|                                  |
|  Hypervisor                      |
|   |       |       |              |
|  VM1     VM2     VM3             |
| Ubuntu  RHEL   Windows           |
+----------------------------------+
```

Advantages:
- Better utilization
- Multiple workloads

Problems:
- Heavyweight
- Full OS per VM
- Fixed resources
- Slower scaling

---

## Generation 3: Containers

```text
+-----------------------------------+
| Host Machine                      |
|                                   |
| Docker / Container Runtime        |
|   |       |       |               |
| Container Container Container     |
+-----------------------------------+
```

Advantages:
- Lightweight
- Fast startup
- Easy scaling
- Lower cost
- Application portability

---

# 3. VM vs Container

## Virtual Machine

```text
Application
Runtime
Full Guest OS
Hypervisor
Host OS
Hardware
```

## Container

```text
Application
Required Libraries
Container Runtime
Host OS
Hardware
```

### Key Difference

| VM | Container |
|----|------------|
| Full OS | Shared Host Kernel |
| Heavyweight | Lightweight |
| Slower | Faster |
| Fixed Resources | Dynamic |
| Minutes to Start | Seconds to Start |

---

# 4. The Dependency Problem

Developer Machine:

```text
Ubuntu
Java 21
Tomcat 11
Application
```

Production Machine:

```text
RHEL
Java 8
Tomcat 8
Application
```

Result:

❌ Application fails

Reason:

Dependencies differ.

---

# Docker Solution

Package everything together.

```text
+-------------------------+
| Application             |
| Java 21                 |
| Tomcat 11               |
| Required Libraries      |
+-------------------------+
```

Run anywhere Docker exists.

---

# 5. What is Docker?

Docker is a container runtime that packages:

- Application
- Libraries
- Dependencies
- Configuration

into a portable unit.

---

# 6. Docker Architecture

```text
Dockerfile
    |
    v
 Build
    |
    v
 Image
    |
    v
 Run
    |
    v
 Container
```

Golden Rule:

**Build → Ship → Run**

---

# 7. Image vs Container

## Docker Image

Think:

📦 Blueprint

Properties:
- Read-only
- Executable package
- Contains dependencies

## Docker Container

Think:

🚀 Running instance of an image

Formula:

```text
Image + Run = Container
```

---

# 8. Docker Hub

Docker Hub is a public registry.

Examples:

- ubuntu
- nginx
- python
- mysql
- node
- tomcat

```text
Docker Hub
     |
     v
 Pull Image
     |
     v
 Local Machine
```

---

# 9. Docker Image Types

## Base Images

Examples:

- Ubuntu
- Alpine
- Python
- Node
- Tomcat

Provided by Docker/community.

## Custom Images

Created by you.

Example:

```text
Ubuntu
 + Python
 + Flask
 + Application Code
---------------------
 Custom Image
```

---

# 10. Essential Docker Commands

## Pull an Image

```bash
docker pull ubuntu
```

Specific Version:

```bash
docker pull ubuntu:22.04
```

---

## View Images

```bash
docker images
```

---

## Run Container

```bash
docker run ubuntu
```

---

## Run Interactive Container

```bash
docker run -it ubuntu
```

### Meaning

- i = interactive
- t = terminal

---

## Detached Mode

```bash
docker run -itd ubuntu
```

Container runs in background.

---

## List Containers

```bash
docker ps
```

All Containers:

```bash
docker ps -a
```

---

## Remove Container

```bash
docker rm -f <container>
```

---

# 11. Foreground vs Detached Mode

## Foreground

```bash
docker run -it ubuntu
```

```text
User ---> Container Terminal
```

Use for:
- Linux practice
- Troubleshooting

---

## Detached

```bash
docker run -d nginx
```

```text
User
 |
 v
Host

Container runs in background
```

Use for:
- Web apps
- Databases
- Production workloads

---

# 12. Port Mapping

Problem:

```text
Browser
   |
   X
Container
```

Cannot directly reach container.

Solution:

```text
Browser
   |
Host:8080
   |
Docker Mapping
   |
Container:80
```

Command:

```bash
docker run -d -p 8080:80 nginx
```

Meaning:

```text
Host Port 8080
      |
      v
Container Port 80
```

---

# 13. Accessing Containers

## Attach

```bash
docker attach container1
```

## Execute Command

```bash
docker exec -it container1 bash
```

Most commonly used in production.

---

# 14. Dockerfile

Dockerfile = Recipe

Example:

```Dockerfile
FROM ubuntu

RUN apt-get update
RUN apt-get install nginx -y

COPY index.html /var/www/html/

EXPOSE 80

CMD ["nginx","-g","daemon off;"]
```

---

# 15. Important Dockerfile Keywords

| Keyword | Purpose |
|-----------|----------|
| FROM | Base image |
| RUN | Execute commands |
| COPY | Copy files |
| ADD | Copy/extract archives |
| EXPOSE | Open port |
| ENV | Environment variables |
| LABEL | Metadata |
| CMD | Default command |
| ENTRYPOINT | Main executable |

---

# 16. Sample Python Container

```Dockerfile
FROM ubuntu

RUN apt-get update && \
    apt-get install python3 -y

COPY app.py /tmp/

EXPOSE 80

CMD ["python3","/tmp/app.py"]
```

---

# 17. Sample Java Web Application

```Dockerfile
FROM tomcat

COPY app.war \
/usr/local/tomcat/webapps/

EXPOSE 8080
```

---

# 18. Container Lifecycle

```text
Dockerfile
    |
 Build
    |
 Image
    |
 Run
    |
 Container Running
    |
 Stop
    |
 Start
    |
 Delete
```

---

# 19. Docker Interview Questions

1. Difference between Image and Container?
2. Difference between VM and Container?
3. What problem does Docker solve?
4. What is Docker Hub?
5. Explain Dockerfile.
6. What is Port Mapping?
7. What does docker exec do?
8. What is detached mode?
9. What is CMD in Dockerfile?
10. Explain Build → Ship → Run.

---

# 20. Kubernetes Preview

Docker creates containers.

```text
Docker
   |
1 Container
```

Kubernetes manages containers at scale.

```text
Kubernetes
     |
Thousands of Containers
```

Docker = Container Runtime

Kubernetes = Container Orchestration

This is the bridge to Day 2.
