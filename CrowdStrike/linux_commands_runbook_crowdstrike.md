---
layout: post
title: "CrowdStrike Falcon Linux Agent Commands Runbook"
date: 2026-06-13
categories: [crowdstrike, falcon, linux, edr]
tags: [crowdstrike, falconctl, linux, sensor, troubleshooting, runbook]
description: "A practical Linux runbook for CrowdStrike Falcon agent installation, validation, troubleshooting, and maintenance commands."
---

# CrowdStrike Falcon Linux Agent Commands Runbook

This post is a practical Linux command reference for CrowdStrike Falcon Sensor deployments on hosts. It covers installation, validation, troubleshooting, log collection, maintenance tasks, and useful `falconctl` queries that are handy during day-to-day support work.

## Installation

Install the package with the correct package manager, set the CID, optionally specify the cloud, and then start the sensor.

```bash
# Ubuntu / Debian
sudo dpkg -i <installerfilename>

# RHEL / CentOS / Amazon Linux
sudo yum install <installerfilename>
sudo dnf install <installerfilename>

# SLES
sudo zypper install <installerfilename>

# Set CID
sudo /opt/CrowdStrike/falconctl -s --cid=<CID>

# If installation tokens are required
sudo /opt/CrowdStrike/falconctl -s --cid=<CID> --provisioning-token=<TOKEN>

# Optional: specify cloud explicitly
sudo /opt/CrowdStrike/falconctl -s --cloud=us-1
sudo /opt/CrowdStrike/falconctl -s --cloud=us-2
sudo /opt/CrowdStrike/falconctl -s --cloud=eu-1
sudo /opt/CrowdStrike/falconctl -s --cloud=us-gov-1
sudo /opt/CrowdStrike/falconctl -s --cloud=us-gov-2

# Start sensor
sudo service falcon-sensor start
sudo systemctl start falcon-sensor
```

## Validation

Use these commands to confirm that the sensor is installed, running, provisioned, and reporting its version.

```bash
# Confirm sensor process is running
ps -e | grep falcon-sensor
ps -aef | grep falcon-sensor

# Confirm AID / Host ID
sudo /opt/CrowdStrike/falconctl -g --aid

# Confirm CID
sudo /opt/CrowdStrike/falconctl -g --cid

# Confirm running sensor version
sudo /opt/CrowdStrike/falconctl -g --version

# Fallback package-based version checks
rpm -qi falcon-sensor
dpkg -s falcon-sensor
```

## falconctl queries

These are useful host-side query commands exposed through `falconctl --help`.

```bash
# Basic configuration
sudo /opt/CrowdStrike/falconctl -g --cloud
sudo /opt/CrowdStrike/falconctl -g --backend
sudo /opt/CrowdStrike/falconctl -g --billing
sudo /opt/CrowdStrike/falconctl -g --tags
sudo /opt/CrowdStrike/falconctl -g --systags
sudo /opt/CrowdStrike/falconctl -g --provisioning-token

# Proxy configuration
sudo /opt/CrowdStrike/falconctl -g --apd
sudo /opt/CrowdStrike/falconctl -g --aph
sudo /opt/CrowdStrike/falconctl -g --app

# Logging / feature / protocol / metadata
sudo /opt/CrowdStrike/falconctl -g --trace
sudo /opt/CrowdStrike/falconctl -g --pcpt
sudo /opt/CrowdStrike/falconctl -g --feature
sudo /opt/CrowdStrike/falconctl -g --metadata-query
sudo /opt/CrowdStrike/falconctl -g --logcounters
sudo /opt/CrowdStrike/falconctl -g --loginterval
sudo /opt/CrowdStrike/falconctl -g --logduration

# Sensor state / compatibility / protection
sudo /opt/CrowdStrike/falconctl -g --rfm-state
sudo /opt/CrowdStrike/falconctl -g --rfm-reason
sudo /opt/CrowdStrike/falconctl -g --rfm-history
sudo /opt/CrowdStrike/falconctl -g --sfm-state
sudo /opt/CrowdStrike/falconctl -g --sfm-reason
sudo /opt/CrowdStrike/falconctl -g --protection-status
sudo /opt/CrowdStrike/falconctl -g --hbfw-state

# Kubernetes-related
sudo /opt/CrowdStrike/falconctl -g --k8s-cluster-id
sudo /opt/CrowdStrike/falconctl -g --k8s-node-uid
```

## falconctl set commands

These set operations are useful during deployment, maintenance, and troubleshooting.

```bash
# Core configuration
sudo /opt/CrowdStrike/falconctl -s --cid=<CID>
sudo /opt/CrowdStrike/falconctl -s --cid=<CID> --provisioning-token=<TOKEN>
sudo /opt/CrowdStrike/falconctl -s --cloud=auto
sudo /opt/CrowdStrike/falconctl -s --cloud=none
sudo /opt/CrowdStrike/falconctl -s --cloud=us-1
sudo /opt/CrowdStrike/falconctl -s --backend=auto
sudo /opt/CrowdStrike/falconctl -s --backend=bpf
sudo /opt/CrowdStrike/falconctl -s --backend=kernel
sudo /opt/CrowdStrike/falconctl -s --billing=default
sudo /opt/CrowdStrike/falconctl -s --billing=metered
sudo /opt/CrowdStrike/falconctl -s --tags=<tag1,tag2>

# Proxy configuration
sudo /opt/CrowdStrike/falconctl -s --apd=true
sudo /opt/CrowdStrike/falconctl -s --apd=false
sudo /opt/CrowdStrike/falconctl -s --aph=<proxy-host>
sudo /opt/CrowdStrike/falconctl -s --app=<proxy-port>

# Logging / feature / metadata
sudo /opt/CrowdStrike/falconctl -s --trace=none
sudo /opt/CrowdStrike/falconctl -s --trace=err
sudo /opt/CrowdStrike/falconctl -s --trace=warn
sudo /opt/CrowdStrike/falconctl -s --trace=info
sudo /opt/CrowdStrike/falconctl -s --trace=debug
sudo /opt/CrowdStrike/falconctl -s --pcpt=auto
sudo /opt/CrowdStrike/falconctl -s --pcpt=ipv4
sudo /opt/CrowdStrike/falconctl -s --pcpt=ipv6
sudo /opt/CrowdStrike/falconctl -s --logcounters=true
sudo /opt/CrowdStrike/falconctl -s --logcounters=false
sudo /opt/CrowdStrike/falconctl -s --loginterval=<seconds>
sudo /opt/CrowdStrike/falconctl -s --logduration=<seconds>
sudo /opt/CrowdStrike/falconctl -s --maintenance-token=<TOKEN>

# Kubernetes-related
sudo /opt/CrowdStrike/falconctl -s --k8s-cluster-id="<cluster-id>"
sudo /opt/CrowdStrike/falconctl -s --k8s-node-uid="<node-uid>"
```

## falconctl delete commands

These are useful when resetting configuration values or preparing special deployment scenarios.

```bash
sudo /opt/CrowdStrike/falconctl -d --cid
sudo /opt/CrowdStrike/falconctl -d --aid
sudo /opt/CrowdStrike/falconctl -d --apd
sudo /opt/CrowdStrike/falconctl -d --aph
sudo /opt/CrowdStrike/falconctl -d --app
sudo /opt/CrowdStrike/falconctl -d --trace
sudo /opt/CrowdStrike/falconctl -d --billing
sudo /opt/CrowdStrike/falconctl -d --tags
sudo /opt/CrowdStrike/falconctl -d --provisioning-token
sudo /opt/CrowdStrike/falconctl -d --cloud
sudo /opt/CrowdStrike/falconctl -d --backend
sudo /opt/CrowdStrike/falconctl -d --loginterval
sudo /opt/CrowdStrike/falconctl -d --logduration
sudo /opt/CrowdStrike/falconctl -d --k8s-cluster-id
sudo /opt/CrowdStrike/falconctl -d --k8s-node-uid
```

## Kernel compatibility

Before installation, or while investigating reduced functionality and sensor binding issues, validate kernel compatibility.

```bash
falcon-kernel-check
uname -r
```

## Install troubleshooting

Use these commands when installation fails because of missing dependencies or repository issues.

```bash
# Ubuntu dependency repair
sudo apt-get -f install

# RPM-based dependency repair
sudo yum install

# SLES dependency repair
sudo zypper install

# SLES OpenSSL repo enablement
sudo zypper mr --enable SLE11-Security-Module
```

## Service troubleshooting

Use these commands when the sensor does not start or looks unhealthy after installation.

```bash
# Process validation
ps -e | grep falcon-sensor
ps -aef | grep falcon-sensor

# Systemd logs
journalctl --short-full | grep falcon

# Syslog / messages
less /var/log/syslog | grep falcon
less /var/log/messages | grep falcon
```

## Diagnostic collection

CrowdStrike provides two useful scripts for Linux troubleshooting. The general diagnostic script is best for most support cases, while the performance script is better for CPU, IO, or memory investigations.

```bash
# General diagnostic collection
chmod +x falcon_diagnostic.sh
./falcon_diagnostic.sh

# Performance collection
sudo bash perf_measurement.sh
sudo chmod u+x perf_measurement.sh
sudo ./perf_measurement.sh

# From root shell
./perf_measurement.sh
```

## Maintenance and imaging

Use these commands when preparing a master image, handling token-related operations, or performing protected maintenance tasks.

```bash
# Verify AID before image prep
sudo /opt/CrowdStrike/falconctl -g --aid

# Remove AID from a master image template
sudo /opt/CrowdStrike/falconctl -d -f --aid

# Reset or force token settings
sudo /opt/CrowdStrike/falconctl -s -f --provisioning-token=<TOKEN>

# Set maintenance token when required
sudo /opt/CrowdStrike/falconctl -s --maintenance-token=<TOKEN>
```

## Kubernetes troubleshooting

These commands are useful when Falcon Sensor for Linux is deployed as a DaemonSet and maintenance protection affects sensor pod changes.

```bash
# Set maintenance token in sensor pod
kubectl -n falcon-system exec <pod-name> -c falcon-node-sensor -- /opt/CrowdStrike/falconctl -s --maintenance-token=<MAINTENANCE_TOKEN>

# Inspect pods
kubectl get pods -n falcon-system

# Delete stuck pod if required by maintenance workflow
kubectl delete pod <pod-name> -n falcon-system
```

## Quick notes

- Prefer `sudo /opt/CrowdStrike/falconctl -g --version` as the Falcon-native version query when it is available on the host.
- Keep `rpm -qi falcon-sensor` or `dpkg -s falcon-sensor` as fallback package-manager validation.
- Run `falcon_diagnostic.sh` as soon as possible after an installation failure because useful `dmesg` details may rotate out.
- Keep hostnames in diagnostic archive names before sharing them with support.