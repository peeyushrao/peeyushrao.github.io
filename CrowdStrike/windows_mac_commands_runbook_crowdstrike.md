# CrowdStrike Falcon Windows and Mac Command Runbooks

This post collects practical CrowdStrike Falcon commands and host-side checks for Windows and Mac. It focuses on installation validation troubleshooting connectivity checks diagnostics and maintenance tasks.

## Windows

### Installation and version

Use the Windows installer with the appropriate parameters and confirm the installed version from Add Remove Programs or other host validation methods.

```powershell
# Check installed version in registry / uninstall inventory
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' |
  Where-Object { $_.DisplayName -like '*CrowdStrike*' } |
  Select-Object DisplayName, DisplayVersion, InstallDate
```

### Connectivity and cloud reachability

The Windows communications checklist uses PowerShell and native utilities to validate TLS network access and active connections to CrowdStrike cloud endpoints.

```powershell
# Basic HTTPS connectivity test
Invoke-RestMethod -Uri https://ts01-b.cloudsink.net:443

# TCP connectivity test
New-Object System.Net.Sockets.TcpClient("ts01-b.cloudsink.net", 443)

# Force TLS 1.2 then test connectivity
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-RestMethod -Uri https://ts01-b.cloudsink.net:443

# View active connections
C:\WINDOWS\system32\netstat.exe -f
```

### Host and policy checks

These commands appear in the Windows communications troubleshooting checklist and help validate host state, logging prerequisites, and network readiness.

```powershell
# BitLocker status
manage-bde -status

# Audit policy
auditpol /get /category:Logon/Logoff

# PowerShell version
$PSVersionTable

# Real Time Response language mode
$ExecutionContext.SessionState.LanguageMode

# OS architecture and system details
wmic os get osarchitecture
systeminfo
```

### Sensor communication logs

The troubleshooting checklist shows successful communication events under the System log with source `CSAgent`. Use Event Viewer or PowerShell to inspect them.

```powershell
# Query recent CSAgent events from the System log
Get-WinEvent -LogName System | Where-Object { $_.ProviderName -eq 'CSAgent' } | Select-Object -First 50 TimeCreated, Id, LevelDisplayName, Message
```

### Diagnostics

CrowdStrike documents CSWinDiag as the main Windows troubleshooting collection tool. Download it from Falcon tool downloads, unzip it, and run the collection on the host.

```powershell
# Run CSWinDiag from an elevated shell after extracting it
CSWinDiag
```

### Notes for Windows

- CSWinDiag is the primary documented Windows diagnostic collection tool.
- The checklist explicitly validates TLS 1.2 connectivity and active connections to CrowdStrike endpoints.
- Installed version can be confirmed from uninstall inventory where the sensor appears as CrowdStrike Sensor Platform.

## Mac

### Installation and licensing

For Mac, `falconctl` under the Falcon app resources path is the main CLI used for licensing, provisioning token handling, running checks, and maintenance operations.

```bash
# License the sensor with CID
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID>

# If installation tokens are required, either use a separate token command
sudo /Applications/Falcon.app/Contents/Resources/falconctl provisioning-token <TOKEN>
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID>

# Or provide the token inline
sudo /Applications/Falcon.app/Contents/Resources/falconctl license <CID> <TOKEN>
```

### Validation

The Mac deployment guide documents `falconctl stats` as the main validation command. It shows AID version CID cloud connection state and additional sensor details.

```bash
# Validate sensor is running and view AID version CID and more
sudo /Applications/Falcon.app/Contents/Resources/falconctl stats

# Verify the Falcon system extension is installed and active
systemextensionsctl list
```

### Cloud connectivity

The documented way to confirm cloud connectivity on Mac is through `falconctl stats`. Look for `Cloud Info` and confirm `State: connected`.

```bash
sudo /Applications/Falcon.app/Contents/Resources/falconctl stats
```

### Diagnostics and log collection

CrowdStrike documents `falconctl diagnose` for Mac diagnostics, including remote collection via RTR. The RTR article recommends a 600 second timeout so the collection can complete and include the sysdiagnose folder.

```bash
# Local diagnostic collection
sudo /Applications/Falcon.app/Contents/Resources/falconctl diagnose

# RTR script example from CrowdStrike guidance
sudo /Applications/Falcon.app/Contents/Resources/falconctl diagnose
# RTR argument field
-Timeout=600
```

After the RTR collection runs, CrowdStrike recommends checking `/tmp` for a file named similar to `falconctl_diagnose_*****.tgz` and waiting until the filename ends in `.tgz` before downloading it.

```bash
cd /tmp
ls
```

### Maintenance and grouping tags

The Mac deployment guide documents grouping tag removal and sensor restart operations using `falconctl`, with or without maintenance token requirements depending on uninstall protection.

```bash
# Clear grouping tags when maintenance protection is enabled
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags clear --maintenance-token

# Clear grouping tags when maintenance protection is disabled
sudo /Applications/Falcon.app/Contents/Resources/falconctl grouping-tags clear

# Restart sensor when maintenance protection is enabled
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload --maintenance-token
sudo /Applications/Falcon.app/Contents/Resources/falconctl load

# Restart sensor when maintenance protection is disabled
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload
sudo /Applications/Falcon.app/Contents/Resources/falconctl load
```

### VM template workflow

For Mac VM templates, CrowdStrike documents unloading the sensor and removing the registry base file before converting the VM into a template so cloned systems receive unique AIDs.

```bash
# Stop the sensor
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload

# If maintenance protection is enabled
sudo /Applications/Falcon.app/Contents/Resources/falconctl unload --maintenance-token

# Remove AID association file before templating
sudo rm /Library/Application\ Support/CrowdStrike/Falcon/registry.base
```

### Uninstall

The uninstall command differs depending on whether uninstall and maintenance protection is enabled.

```bash
# Uninstall without maintenance protection
sudo /Applications/Falcon.app/Contents/Resources/falconctl uninstall

# Uninstall with maintenance protection
sudo /Applications/Falcon.app/Contents/Resources/falconctl uninstall --maintenance-token
```

## Quick notes

- On Mac, `falconctl stats` is the most useful all-in-one validation command because it shows AID version CID and cloud state.
- On Mac, `systemextensionsctl list` is the documented way to verify the Falcon system extension is enabled and active.
- On Windows, CSWinDiag is the primary documented diagnostic collection tool.
- On Windows, the communications checklist relies heavily on `Invoke-RestMethod`, `netstat`, PowerShell TLS 1.2 checks, and System log entries from `CSAgent`.
