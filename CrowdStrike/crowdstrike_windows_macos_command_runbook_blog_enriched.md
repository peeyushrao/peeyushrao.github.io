# CrowdStrike Falcon Windows and macOS Command Runbook

A practical host-side runbook for validating, troubleshooting, and maintaining CrowdStrike Falcon sensors on Windows and macOS.

> **Scope:** These commands are intended for authorized administrators and responders. Some operations require local administrator/root privileges, a Falcon maintenance token, or specific Real Time Response (RTR) permissions.

---

## Quick reference

| Task | Windows | macOS |
|---|---|---|
| Confirm sensor is running | `sc.exe query csagent` | `sudo /Applications/Falcon.app/Contents/Resources/falconctl stats` |
| Check cloud connectivity | `netstat.exe -f` | `falconctl stats` → `Cloud Info` → `State: connected` |
| Review sensor logs | Windows System log / `CSAgent` | Apple unified log |
| Collect diagnostics | `CSWinDiag`, ProcMon, or Xperf depending on the issue | `falconctl diagnose` |
| Verify system extension | N/A | `systemextensionsctl list` |
| View sensor grouping tags | Falcon console / configured tooling | `falconctl grouping-tags get` |
| Restart sensor | Use documented maintenance workflow | `falconctl unload` then `falconctl load` |
| Uninstall sensor | Installer `/uninstall` workflow | `falconctl uninstall` |

---

# Windows

## 1. Confirm the Falcon sensor is running

Open an **elevated Command Prompt** and run:

```cmd
sc.exe query csagent
```

A healthy running sensor reports:

```text
STATE : 4 RUNNING
```

This is a better first check than relying only on Add/Remove Programs because it verifies that the Falcon driver is actually running.

---

## 2. Check the installed CrowdStrike version

You can query the Windows uninstall inventory with PowerShell:

```powershell
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' |
  Where-Object { $_.DisplayName -like '*CrowdStrike*' } |
  Select-Object DisplayName, DisplayVersion, InstallDate
```

For 32-bit application inventory on a 64-bit host, it can also be useful to check:

```powershell
Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' |
  Where-Object { $_.DisplayName -like '*CrowdStrike*' } |
  Select-Object DisplayName, DisplayVersion, InstallDate
```

---

## 3. Verify cloud connectivity

From an elevated Command Prompt:

```cmd
netstat.exe -f
```

Look for established outbound connections associated with the Falcon sensor path to the CrowdStrike cloud.

If the host uses a proxy, the remote address may show the proxy rather than a CrowdStrike cloud hostname.

When troubleshooting connectivity, also validate:

```powershell
# PowerShell version
$PSVersionTable

# Current PowerShell language mode
$ExecutionContext.SessionState.LanguageMode

# Basic operating-system details
systeminfo
```

For RTR on Windows, PowerShell Constrained Language Mode must not be enabled.

> Avoid treating a single hard-coded CrowdStrike hostname as universal. Cloud endpoints vary by Falcon cloud and configuration. Use the current CrowdStrike cloud IP/FQDN guidance for your environment.

---

## 4. Review Falcon sensor events

Falcon sensor operational events can appear in the Windows **System** event log under the `CSAgent` provider.

```powershell
Get-WinEvent -LogName System |
  Where-Object { $_.ProviderName -eq 'CSAgent' } |
  Select-Object -First 50 TimeCreated, Id, LevelDisplayName, Message
```

For a narrower time window:

```powershell
$start = (Get-Date).AddHours(-4)

Get-WinEvent -FilterHashtable @{
  LogName   = 'System'
  StartTime = $start
} |
  Where-Object { $_.ProviderName -eq 'CSAgent' } |
  Select-Object TimeCreated, Id, LevelDisplayName, Message
```

Sensor operational logging is not necessarily enabled in every environment, so an empty result does not by itself prove that the sensor is unhealthy.

---

## 5. Useful host checks

These are useful supporting checks when diagnosing installation, RTR, or host-readiness issues.

```powershell
# BitLocker status
manage-bde -status

# Logon/Logoff audit policy
auditpol /get /category:Logon/Logoff

# PowerShell version
$PSVersionTable

# RTR-relevant PowerShell language mode
$ExecutionContext.SessionState.LanguageMode

# OS details
systeminfo
```

---

## 6. Collect Windows diagnostics with CSWinDiag

CrowdStrike provides **CSWinDiag** as the standard Windows sensor diagnostic collection tool. Use it when you need a broad snapshot of sensor state, installation data, Windows errors, network configuration, cloud connectivity, TLS/certificate checks, proxy configuration, running processes, installed patches, and other host information.

### Local collection

Download the latest CSWinDiag package from Falcon, extract it to a directory under `%PROGRAMFILES%`, and run it with local administrator privileges.

Example:

```cmd
mkdir "C:\Program Files\AdminTools"
```

Extract `cswindiag.exe` into that directory, then either double-click the executable or use an elevated Command Prompt:

```cmd
cd /d "C:\Program Files\AdminTools"
cswindiag
```

> **Important:** CrowdStrike's collection guidance says to run CSWinDiag from a folder inside `C:\Program Files`. Running it from another location can produce an error asking you to run it from the Program Files directory.

The tool does **not** install software or make system changes; it collects diagnostic information.

A typical collection averages about **3–4 minutes**, but slower hosts or heavily loaded systems can take **20–30 minutes or longer**. Allow it to finish without interruption.

Typical progress includes:

```text
basic host details
network connectivity tests
additional host details
Windows errors/warnings
msinfo32 data
sensor and Windows logs
finalizing collection
```

When collection is complete, CSWinDiag prints the path to the generated ZIP file. Use the path reported by the tool rather than assuming a fixed output directory.

Example filename:

```text
CSWinDiag-<hostname>-<unique-id>.zip
```

### CSWinDiag through RTR

If you have the required Falcon RTR permissions, run:

```text
cswindiag
```

The RTR `cswindiag` command is Windows-only and packages the diagnostic data into a ZIP that can be retrieved from the RTR working directory.

For sensor versions **before 6.38**:

```text
cd c:\windows\system32\drivers\crowdstrike\rtr\putrun
ls
get CSWinDiag_<hostname>_<unique-id>.zip
```

For sensor versions **6.38 and later**:

```text
cd c:\"program files"\crowdstrike\rtr\putrun
ls
get CSWinDiag_<hostname>_<unique-id>.zip
```

Wait for the collection to finish before retrieving the newest ZIP. CrowdStrike notes that RTR does not display a completion notification for this command, so allow roughly 3–4 minutes under normal conditions before checking the working directory.

---

## 7. Capture a ProcMon trace for application compatibility issues

Use **Microsoft Sysinternals Process Monitor (ProcMon)** when CrowdStrike Support requests detailed process activity for a Windows application compatibility issue.

### Prepare the capture

1. Download the latest ProcMon from Microsoft Sysinternals.
2. Extract it on the affected host.
3. Get the application as close as possible to the point where the issue can be reproduced, but **do not reproduce it yet**.
4. Start the executable that matches the host architecture:

```text
32-bit Windows: procmon.exe
64-bit Windows: procmon64.exe
```

ProcMon begins capturing automatically when it opens. Confirm that capture activity is visible in the status bar.

### Reproduce and stop the capture

1. Reproduce the application compatibility symptom.
2. Return to ProcMon immediately after the behavior is captured.
3. Click **Capture** to stop collection.

Keep the trace focused on the reproduction window so the resulting file is easier to handle and analyze.

### Save the capture

Use **File > Save** and select:

```text
Events to save: All events
Format: Native Process Monitor Format (PML)
```

Include the affected hostname in the filename when practical:

```text
C:\Users\<username>\Desktop\<hostname>-Logfile.pml
```

Compress the `.pml` before submitting it:

```text
<hostname>-Logfile.pml
        ↓
<hostname>-Logfile.zip
```

ProcMon captures can become large, so use the file-transfer method provided for your CrowdStrike Support case.

---

## 8. Capture Xperf logs for performance or compatibility issues

Use **Xperf** when CrowdStrike Support requests a performance trace for a Windows sensor application compatibility or performance investigation.

CrowdStrike's procedure uses an attached `xperf_capture.bat` script together with the **Windows Performance Toolkit** component of the Microsoft Windows Assessment and Deployment Kit (ADK).

### Prerequisites

1. Download the Xperf script ZIP supplied with the CrowdStrike Support article.
2. Extract the ZIP.
3. Review the included `.rtf` instructions for version-specific notes.
4. Install the Windows ADK that matches the affected Windows build.
5. Ensure **Windows Performance Toolkit** is selected during ADK installation.

For Windows Server, use the ADK corresponding to the workstation platform on which that server release is based.

### Run the capture

Navigate to the extracted files, right-click:

```text
xperf_capture.bat
```

and select **Run as administrator**.

Choose the appropriate trace option from the script menu.

The scripted trace runs for **90 seconds**.

1. Start the capture.
2. Reproduce the issue immediately.
3. For performance investigations, allow the full 90-second trace to complete.
4. Record the output path displayed by the script.
5. Attach the generated log to the relevant CrowdStrike Support case.

> **Do not use `Ctrl+C` to terminate the capture early.** CrowdStrike warns that this can stop only the batch script while Xperf continues logging in the background, potentially creating a very large trace that can consume the `C:` drive.

---

## 9. Useful RTR commands on Windows

These are **Falcon RTR commands**, not commands to paste directly into a normal Windows shell:

```text
help
ps
ipconfig
netstat
eventlog list
eventlog view
filehash
get
reg query
cswindiag
```

Availability depends on the user's RTR role, custom permissions, response policy settings, and command prerequisites.

For example, `cswindiag` is a high-privilege RTR command, while read-only commands such as `ps`, `ipconfig`, and `netstat` are available to broader RTR roles.

---

## 10. Windows VM template / golden image

For a Windows VM template, CrowdStrike documents using `NO_START=1` so the sensor does not start before the image is cloned.

Example:

```cmd
<installer_filename> /install CID=<CID> NO_START=1
```

If installation tokens are required:

```cmd
<installer_filename> /install CID=<CID> NO_START=1 ProvToken=<TOKEN>
```

Do not boot the prepared template before converting it into the final image, because the sensor can start and obtain an AID.

---

# macOS

## 1. Main Falcon CLI path

The Falcon sensor CLI is:

```bash
/Applications/Falcon.app/Contents/Resources/falconctl
```

Most administrative operations require `sudo`.

---

## 2. License the sensor

License the sensor with your CID:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID>
```

If your CID requires an installation token, you can provide it separately:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl provisioning-token <TOKEN>
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID>
```

Or provide the token with the license operation:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID> <TOKEN>
```

---

## 3. Confirm the sensor is running

Run:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl stats
```

The output includes sensor information such as:

- Agent ID (AID)
- Sensor version
- Customer ID (CID)
- Cloud information
- Event counters

This is the primary host-side validation command on macOS.

---

## 4. Verify cloud connectivity

Run:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl stats
```

In the output, locate:

```text
Cloud Info
...
State: connected
```

`State: connected` confirms that the sensor has established its CrowdStrike cloud connection.

For deeper validation, review the heartbeat and event counters in the same `stats` output.

---

## 5. Verify the Falcon system extension

Run:

```bash
systemextensionsctl list
```

Look for the Falcon endpoint security extension:

```text
com.crowdstrike.falcon.Agent
```

It should show as enabled and active.

---

## 6. View Falcon logs

Falcon for macOS uses Apple's unified logging interface.

To review recent Falcon Agent logs:

```bash
log show \
  --predicate 'process == "com.crowdstrike.falcon.Agent"' \
  --last 20h
```

For live troubleshooting, use the macOS `log` command's streaming options as appropriate for your investigation.

---

## 7. Collect macOS diagnostics

Run:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl diagnose
```

When the collection completes, `falconctl` reports the path to a `.tgz` diagnostic archive, typically under `/private/tmp`.

You can inspect the temporary directory with:

```bash
ls -lh /private/tmp/falconctl_diagnose_*.tgz
```

Do not retrieve a partially written archive. Confirm that the final `.tgz` file exists before copying or uploading it.

---

## 8. View sensor grouping tags

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags get
```

Set tags:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags set Production,MacFleet
```

When uninstall and maintenance protection is enabled:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags set Production,MacFleet --maintenance-token
```

Clear tags:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags clear
```

With maintenance protection enabled:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags clear --maintenance-token
```

Tag changes take effect after the sensor restarts.

---

## 9. Restart the macOS sensor

Without uninstall and maintenance protection:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload
sudo /Applications/Falcon.app/Contents/Resources/falconctl load
```

With uninstall and maintenance protection enabled:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload --maintenance-token
sudo /Applications/Falcon.app/Contents/Resources/falconctl load
```

The maintenance token is entered when prompted.

---

## 10. Prepare a macOS VM template

To avoid cloned systems sharing the same AID, stop the sensor before converting the VM into a template.

Without maintenance protection:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload
```

With maintenance protection:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload --maintenance-token
```

Remove the file used to associate the host with its AID:

```bash
sudo rm "/Library/Application Support/CrowdStrike/Falcon/registry.base"
```

Then shut down the VM and convert it into the template.

---

## 11. Uninstall the macOS sensor

Without uninstall and maintenance protection:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl uninstall
```

With uninstall and maintenance protection:

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl uninstall --maintenance-token
```

Administrative privileges are required.

---

# Troubleshooting flow

When a host appears unhealthy, work from the simplest validation to the deepest collection.

## Windows

1. Confirm the sensor is running:

   ```cmd
   sc.exe query csagent
   ```

2. Check active connections:

   ```cmd
   netstat.exe -f
   ```

3. Review `CSAgent` events in the Windows System log.
4. Use **CSWinDiag** for a broad sensor/host diagnostic package.
5. Use **ProcMon** when the issue is a reproducible application compatibility interaction and Support needs detailed process activity.
6. Use **Xperf** when the issue is performance-related or Support specifically requests a timed performance trace.

4. Validate PowerShell/RTR prerequisites.

5. Run CSWinDiag if the problem is not obvious.

### Which Windows collector should I use?

| Symptom / request | Preferred collection |
|---|---|
| General sensor health, connectivity, installation, TLS, proxy, Windows errors | **CSWinDiag** |
| Application compatibility problem with a reproducible process interaction | **ProcMon** |
| CPU/performance degradation or a Support-requested performance trace | **Xperf** |

## macOS

1. Check sensor state:

   ```bash
   sudo /Applications/Falcon.app/Contents/Resources/falconctl stats
   ```

2. Confirm `Cloud Info` reports `State: connected`.

3. Verify the system extension:

   ```bash
   systemextensionsctl list
   ```

4. Review Falcon unified logs.

5. Run:

   ```bash
   sudo /Applications/Falcon.app/Contents/Resources/falconctl diagnose
   ```

---

# Final notes

- Use `sc.exe query csagent` as the direct Windows sensor-running check.
- Use `netstat.exe -f` as a documented host-side Windows cloud-connectivity check.
- Use `falconctl stats` as the primary macOS health and cloud-connectivity command.
- Use `systemextensionsctl list` to verify the Falcon macOS system extension.
- Use CSWinDiag on Windows and `falconctl diagnose` on macOS for support-ready diagnostic collections.
- Treat RTR commands separately from native operating-system commands; RTR command availability depends on Falcon roles, permissions, policies, and prerequisites.
- Maintenance-protected macOS operations require a maintenance token.
- Golden-image workflows must prevent the source template from obtaining or retaining an AID that will be duplicated across clones.

---

# Source notes

This runbook was enriched from CrowdStrike documentation covering:

- Falcon Sensor for Windows diagnostics and CSWinDiag collection
- ProcMon capture for Falcon Windows sensor application compatibility investigations
- Xperf capture for Falcon Windows sensor application compatibility and performance investigations
- Falcon sensor deployment, maintenance, RTR, and macOS `falconctl` operations

Operational procedures can change. Validate destructive or support-directed workflows against the current CrowdStrike documentation for your Falcon cloud and sensor version.
