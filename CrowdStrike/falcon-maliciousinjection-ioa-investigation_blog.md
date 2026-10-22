# Investigating a CrowdStrike Falcon MaliciousInjection IOA False Positive
### A worked case: legitimate dev service installs killed by a behavioral detection, from first alert to minimum-scope exclusion

> **Redaction note:** this article contains a real hostname, user path and process IDs from the case. Redact them before sharing outside your team.

---

## 1. Why this article exists

A developer was reinstalling a local dev build of an IIS web application. A PowerShell script removed old Windows services and installed new ones. Falcon repeatedly killed the PowerShell session with a **MaliciousInjection** behavioral IOA (MITRE T1055, Process Injection, severity Medium). The same install had worked months earlier.

This article records:

- the full investigation path, including the dead ends and my own wrong turns,
- every LogScale / Advanced Event Search query used, with what worked and what did not,
- how to read the evidence and decide it is legitimate,
- how to build the narrowest possible IOA exclusion,
- the corrections made along the way, because they teach as much as the final answer.

**Final status at the time of writing:** the exclusion (GSOC-HSTGRP) is saved and the developer's re-test worked. It was then extended so other approved users can run the same script, with one shared host group controlling who is covered. Section 15 walks through the whole resolution as steps: what was first suggested, and what was agreed with the end user. Pending items are in section 12.

---

## 2. The case in one page

| Item | Detail |
|---|---|
| Host | UK-HOSTNAME (developer workstation) |
| Detection | IOA name `MaliciousInjection`, tactic Defense Evasion, technique Process Injection (T1055), severity Medium |
| Action | "Process killed" (PowerShell terminated, install aborted) |
| Flagged process | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| Script behavior | `install_classic_dev.ps1` calls other scripts (for example `write_header.ps1`), runs `sc.exe delete` against 23 existing application services, then runs `InstallUtil.exe /unattended` for the new service binaries |
| Binaries | All unsigned (internal dev build), under `C:\Program Files\Company\CMS Background\` |
| Earlier failures | 18 Sep 2026, 13:55:14 UTC (14:55:14 BST) and several earlier times that day |
| Console detection | 16 Oct 2026, 19:10:03 to 19:13:27 IST (13:40:03 to 13:43:27 UTC) |
| Re-test detection | 21 Oct 2026, 15:50:04 UTC, `PatternId` 10133, "Prevention, process killed" |
| Exclusion | IOA exclusion **GSOC-HSTGRP** (MaliciousInjection), host group GSOC-HSTGRP, parent `cmd.exe`, grandparent `explorer.exe`, command line ending in `\gitdirname\classic-dev\install_classic_dev.ps1"` |
| Outcome | Activity judged legitimate; narrow IOA exclusion created; the developer's re-test worked; more approved users to be added through the host group |

---

## 3. Background concepts you need first

### 3.1 Three different exclusion types

| Type | What it affects | Good for | Risk |
|---|---|---|---|
| **IOA exclusion** | A specific behavioral IOA (for example MaliciousInjection) when process, command line and optionally ancestors match | Behavioral false positives such as this case | Broad patterns create blind spots for that behavior |
| **ML exclusion** | Machine-learning / cloud file detection and prevention for a path or hash | Unsigned internal executables blocked on file reputation | Anyone who can write to the path gets a pass from ML |
| **Sensor Visibility Exclusion (SVE)** | Hides files or processes in a path from the sensor entirely: no detections, no prevention, little or no telemetry | Last resort, usually performance problems | Total blind spot, including loss of the events used to investigate |

For this case only the IOA exclusion fits. The flagged process is the System32 `powershell.exe`, not a file in the dev folder, so a folder-level ML exclusion or SVE would not change this behavioral detection. It would also create a blind spot in a user-writable folder.

### 3.2 Behavioral IOA versus file-based detection

How to tell which one you have:

- **File ML / quarantine:** the binary is quarantined or blocked from running, and you see a quarantine entry.
- **Behavioral IOA:** the binary runs, but a process is killed or an operation is blocked because of what it did. In this case the service binary installed fine and PowerShell itself was killed.

### 3.3 Injector versus injectee

A process-injection detection has two roles:

- **Injector:** the process doing the injecting.
- **Injectee (target):** the process being injected into.

In this case the flagged and killed process (`powershell.exe`) was the **injector**. The injectee was `sc.exe`. This matters for reading the exclusion form (section 10).

### 3.4 What the exclusion form actually matches

The "Create IOA exclusion" form has three groups of patterns, all describing the **detected process** and its lineage:

- **Primary patterns:** image file name and command line of the detected process.
- **Parent patterns:** its parent's image and command line.
- **Grandparent patterns:** its grandparent's image and command line.

There is **no field for the injectee**. So you cannot scope an exclusion to "PowerShell injecting into `sc.exe` only". You can only narrow by who the detected process is, what it was launched with, who launched it, and which hosts the exclusion applies to.

Patterns are regular expressions. "Include ancestor exclusion patterns" requires newer sensors; older sensors ignore such exclusions.

---

## 4. Timeline of the investigation

1. **Question from a team thread:** how to handle unsigned internal executables that Falcon blocks. Layered answer in section 11.
2. **First exclusion form seen:** pre-filled with `powershell.exe` and 6 broad host groups (about 90,000 hosts). Not saved.
3. **Parent patterns seen:** `explorer.exe` and `userinit.exe`, meaning an interactive user launch. Not saved.
4. **Chat with the developer and the incident text:** failure after the first service install, every time; unsigned dev binaries; worked in March/April.
5. **Vendor case logged:** template reply received. A tailored message was drafted.
6. **LogScale queries:** several rounds (section 6), including failures.
7. **Injector found:** `powershell.exe` injecting into 10 `sc.exe` processes (section 7).
8. **Script behavior confirmed:** 23 `sc.exe delete` calls on application services, none touching Falcon.
9. **Decision:** legitimate, allow at minimum scope.
10. **Launch method changed** so the command line names the script (section 9).
11. **Re-test detection captured** with the real command line, and the exclusion form built from it (section 10).

---

## 5. Lessons that cost time (read these first)

1. **Check the console time zone.** The console showed IST (UTC+5:30) while Advanced Event Search used UTC. A detection at 19:10:03 IST is 13:40:03 UTC. I first guessed BST, which was wrong, and an hour-long query window missed the event entirely.
2. **Event names differ by repo.** `#event_simpleName=EppDetectionSummaryEvent` returned nothing. In this tenant the detections repo uses **`Event_EppDetectionSummaryEvent`**, and the host field is `Hostname`, not `ComputerName`.
3. **Exports are capped at 200 rows.** An early query returned exactly 200 rows and stopped at 16:55 UTC, well before the event. If a result count is a round number, assume truncation and narrow the filter or the time range.
4. **Filter out the noise.** On a busy dev laptop, broad PowerShell queries return mostly background activity (an AI coding agent running `pwsh.exe`, Intune `AgentExecutor.exe` scripts, an app launching an encoded command for a notification sound). Narrow by command line, parent or process ID.
5. **Pivot on process IDs, not names.** Once you have one ID, chain outward: detection → `ProcessRollup2` → children → other events.
6. **Look at the telemetry, not just the detection page.** The detection page showed only the killed PowerShell. The `ProcessInjection` events revealed the injectee and the detect name.

---

## 6. The queries

Notation: AES is Advanced Event Search (LogScale syntax). Set the time range with the picker, in UTC. Field names can differ by tenant and sensor version. **Status** tells you whether the query was confirmed in this case.

### 6.1 Detection summary for a host (works)

Wrong version, returned nothing:

```
#event_simpleName=EppDetectionSummaryEvent ComputerName="UK-HOSTNAME"
| Technique=/Injection/i OR PatternDispositionDescription=*
| table([...])
```

Two problems: the event name lacks the `Event_` prefix, and the `OR` line was malformed.

Working version:

```
#event_simpleName=Event_EppDetectionSummaryEvent Hostname=/UK-HOSTNAME/i
| table([@timestamp, Name, Tactic, Technique, SeverityName, PatternId, PatternDispositionDescription, FileName, CommandLine, ParentImageFileName, ParentCommandLine, GrandParentImageFileName, ProcessId, HostGroups])
| sort(@timestamp, order=desc)
```

- **Status:** confirmed. It returned the 21 Oct detection (`PatternId` 10133, command line, parent `cmd.exe`, grandparent `explorer.exe`).
- Use `Hostname=/.../i` (case-insensitive regex) because hostnames are stored in upper case.
- The `PatternId` is what the vendor needs to say exactly which logic fired.
- Other fields visible in the raw event: `FalconHostLink`, `AgentId`, `ProcessStartTime` (epoch seconds), `PatternDispositionDescription`, `MitreAttack[]`, `RiskScore`.

### 6.2 Find the interesting processes around the incident (works)

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME"
| ImageFileName=/(InstallUtil|dcsmSplitMerge)/i OR CommandLine=/^"?C:\\Windows\\System32\\WindowsPowerShell\\v1\.0\\powershell\.exe"?\s*$/i
| table([@timestamp, ImageFileName, CommandLine, SHA256HashData, ParentBaseFileName, ParentProcessId, TargetProcessId])
| sort(@timestamp, order=asc)
```

- **Status:** confirmed. It returned two rows for 16 Oct: the bare PowerShell started by `explorer.exe` at 13:40:03 UTC (process ID 14601368193453) and one `InstallUtil.exe` at 13:43:28 UTC whose parent was that PowerShell.
- The regex matches the detection's command line exactly: the quoted path and nothing else.
- Use `TargetProcessId` as the process's own ID and `ParentProcessId` for its parent.

### 6.3 First attempt, too broad (lesson)

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME"
| ImageFileName=/(powershell|InstallUtil|dcsmSplitMerge)/i
| table([...])
| sort(@timestamp, order=asc)
```

- **Status:** ran, but returned 200 rows of noise ending at 16:55 UTC, before the event. Useful only as a lesson in section 5.

### 6.4 Inventory of event types touching two process IDs (works)

```
ComputerName="UK-HOSTNAME"
| ContextProcessId=14601886500230 or ContextProcessId=14601368193453 or TargetProcessId=14601886500230
| groupBy([#event_simpleName], function=count())
```

(14601368193453 is PowerShell; 14601886500230 is the `InstallUtil` run.)

- **Status:** confirmed. Result included `ProcessInjection` (10), `ClassifiedModuleLoad` (1), `RansomwareOpenFile` (1), `EndOfProcess` (2), `ProcessAncestryInformation` (1) and many file-written events.
- Some counts sat at exactly 50, which looks like a cap, so treat them as "at least".
- The `OR` between field filters works when written lower case `or` between separate field tests.
- `groupBy` on `#event_simpleName` is the quickest way to find out what telemetry exists for an unfamiliar window or process.

### 6.5 Read the interesting events themselves (works)

```
ComputerName="UK-HOSTNAME"
| ContextProcessId=14601886500230 or ContextProcessId=14601368193453 or TargetProcessId=14601886500230
| in(#event_simpleName, values=[ProcessInjection, ClassifiedModuleLoad, RansomwareOpenFile, EndOfProcess, ProcessAncestryInformation])
| sort(@timestamp, order=asc)
```

- **Status:** confirmed (export contained the injection fields).
- Switch to the **Source Events** tab to see all fields, or end with `| table(*)`.
- Key fields in `ProcessInjection` were the injector and injectee image names, the injectee process ID, `DetectName`, `MemoryDescriptionFlags` and `ThreadExecutionControlType`.

### 6.6 What did the script launch? (works, the most useful query)

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME" ParentProcessId=14601368193453
| table([@timestamp, ImageFileName, CommandLine, ParentBaseFileName, TargetProcessId])
| sort(@timestamp, order=asc)
```

- **Status:** confirmed. It listed the script's children: 23 `sc.exe delete <service>` commands for application services, then `InstallUtil.exe`.
- Always check this for anything that mentions the security product (`CSFalconService`, `CSAgent`, "Falcon"). Here none did. That check is what separates "legitimate cleanup" from "tampering".

### 6.7 Estate-wide recurrence check (fixed version, not yet run)

```
#event_simpleName=Event_EppDetectionSummaryEvent Technique=/Process Injection/i
| groupBy([Hostname, UserName, FileName, PatternId], function=count())
| sort(_count, order=desc)
```

- **Status:** not yet run. Run it over as long a range as retention allows.
- If only the dev host appears, a one-host exclusion is easy to justify. If other hosts show the same `PatternId`, scoping needs rethinking.

### 6.8 Other queries suggested but not run

Sensor version, for the vendor case:

```
#event_simpleName=AgentOnline ComputerName="UK-HOSTNAME"
| tail(1)
```

`InstallUtil` hashes and command lines:

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME" ImageFileName=/InstallUtil/i
| groupBy([SHA256HashData, CommandLine], function=count())
```

Generic injection-related telemetry (event names depend on your sensor version):

```
ComputerName="UK-HOSTNAME" #event_simpleName=/(Inject|RemoteThread|AssemblyLoad|ProcessInjection)/i
| table([@timestamp, #event_simpleName, ContextProcessId, TargetProcessId, ImageFileName, FileName])
| sort(@timestamp, order=asc)
```

### 6.9 LogScale syntax cheat sheet (from this case)

| Need | Syntax |
|---|---|
| Exact event type | `#event_simpleName=ProcessRollup2` |
| Case-insensitive regex on a field | `Field=/pattern/i` |
| Either of two conditions | `Field1=/a/i OR Field2=/b/i` or `A=1 or B=2` |
| Multiple values for one field | `in(#event_simpleName, values=[A, B, C])` |
| Choose and order columns | `table([f1, f2, f3])` |
| Sort | `sort(@timestamp, order=asc)` |
| Count per group | `groupBy([f1, f2], function=count())` |
| Last row | `tail(1)` |
| See every field | `table(*)` or the Source Events tab |

If a function is rejected, copy the exact error text. Function availability can differ by tenant and version, and the error usually shows what to change.

### 6.10 The pivot recipe

1. Detection page or `Event_EppDetectionSummaryEvent` gives host, time and `ProcessId`.
2. `ProcessRollup2` with that ID as `TargetProcessId` gives image, command line, parent and hash.
3. `ProcessRollup2` with `ParentProcessId=<that ID>` lists what it launched.
4. `ContextProcessId` or `TargetProcessId` on any event type shows file writes, module loads, injections and so on.
5. `ProcessAncestryInformation` gives the lineage.

### 6.11 Verification queries after the exclusion

Confirm the run happened and which parent launched it:

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME" CommandLine=/install_classic_dev\.ps1/i
| table([@timestamp, CommandLine, ParentBaseFileName, TargetProcessId])
| sort(@timestamp, order=desc)
```

Check for any new detection on the host:

```
#event_simpleName=Event_EppDetectionSummaryEvent Hostname=/UK-HOSTNAME/i
| table([@timestamp, Technique, PatternId, PatternDispositionDescription, CommandLine, ParentImageFileName])
| sort(@timestamp, order=desc)
```

Check that the install got past the first service:

```
#event_simpleName=ProcessRollup2 ComputerName="UK-HOSTNAME" ImageFileName=/InstallUtil/i
| table([@timestamp, CommandLine])
| sort(@timestamp, order=desc)
```

- **Status:** suggested for the re-test; the developer reported the install worked.
- The exclusion has worked if the first query shows the run, the second shows no new detection after it, and the third shows more than one `InstallUtil` launch (the earlier failures stopped after one).
- For another user's host, replace the hostname in each query.

---

## 7. Reading the evidence

### 7.1 The injection events

Ten `ProcessInjection` events were recorded between 13:41:16 and 13:42:27 UTC:

| Field | Value |
|---|---|
| Injector | `powershell.exe` (process ID 14601368193453), the developer's session |
| Injectee | `sc.exe`, a different process for each event |
| `DetectName` | `WmiUninstallFalcon` |
| Scenario / technique | Evade Detection / Disable or Modify Tools |
| `MemoryDescriptionFlags` | 1576 |
| `ThreadExecutionControlType` | 5 |

How to treat the `DetectName`: it is Falcon's internal label for the logic that fired. It is worth asking the vendor what it matches, but it should not be read as proof of an attack. The `sc.exe` command lines (query 6.6) are the real test.

### 7.2 What the script was actually doing

- 23 `sc.exe delete <service>` calls on application services (for example the async-jobs and Word-conversion services and a numbered set of ID-control services), launched in quick bursts from the PowerShell process.
- Then `InstallUtil.exe /unattended "C:\Program Files\Company\CMS Background\dcsmSplitMergeService.exe"`.
- `InstallUtil.exe` exited with code 0 (success), and PowerShell was terminated at the same moment.
- Ten of the 23 `sc.exe` launches were the flagged injection targets. A burst of many rapid `sc.exe` launches is the likely trigger, which also matches the developer's observation that Falcon dislikes the script doing "lots" of service operations.

### 7.3 Benign signals

- `InstallUtil.exe` was the genuine .NET Framework64 v4.0.30319 binary. Its hash matched what the developer reported.
- `ClassifiedModuleLoad`: `InstallUtil` loading `Microsoft.VisualBasic.ni.dll`, a Windows .NET native image. Routine.
- `RansomwareOpenFile`: one event, PowerShell opening a `.jpg` in the web application's image folder under `inetpub\wwwroot`. That is consistent with the script copying web app files, not with encryption (one event, nothing else).
- PowerShell and `InstallUtil` both ended at 13:43:30 UTC. PowerShell's exit code was 3758096423 (0xE0000027), which as far as I know is a forced-termination code, but treat that as unconfirmed.
- `RemediationMonitorQuarantineFile` appeared 565 times. This looks like Falcon's own tracking of files written during the activity rather than 565 quarantines, but it is unverified. Check before telling anyone.

### 7.4 Why it was not simply rubber-stamped

`InstallUtil.exe` running unsigned assemblies from PowerShell is also a classic defense-evasion technique (T1218.004). Before excluding, the checks were:

1. The `sc.exe` commands target application services only, not the security product.
2. The binaries and hashes match what the developer reported.
3. The activity is one host and one user, with repeated identical behavior.
4. The script purpose was confirmed with the developer and its output matched.

Still outstanding: the 90-day recurrence query (6.7) and comparing the service binaries against the other team's build pipeline.

---

## 8. Mistakes made along the way (and corrections)

| # | What I got wrong | What was true | Lesson |
|---|---|---|---|
| 1 | Used `EppDetectionSummaryEvent` and `ComputerName` | The tenant uses `Event_EppDetectionSummaryEvent` and `Hostname` | Test one tiny query first and inspect a raw event for field names |
| 2 | Assumed the console was on BST | It was on IST (UTC+5:30) | Compare a known process start with the detection's start time |
| 3 | Guessed `InstallUtil.exe` was the injector | The injector was `powershell.exe`; the injectee was `sc.exe` | Do not name the injector until the `ProcessInjection` event shows it |
| 4 | Said the form's primary patterns describe the injectee | They describe the detected process, which here is the injector | Read the form as "the detected process and its ancestors" |
| 5 | Said nothing on the form identifies the injector | The detected process is the injector, but the injectee still can't be scoped | The form can narrow by injector, command line, ancestors and hosts, but not by target |
| 6 | Said detection `ProcessId` could not be matched to `TargetProcessId` | On Windows both use the same format and can be joined (my claim came from a Mac sample) | Check a sample from the right platform |
| 7 | Suggested ancestors could pin the injector | They only describe the lineage of the detected process | Ancestors narrow who launched it, nothing more |
| 8 | Gave the `-File` launch command without saying to change directory first | The child started in the wrong folder and `./write_header.ps1` failed | Child shells inherit the working directory; change directory first in the same window |

---

## 9. Making the exclusion narrow enough

### 9.1 The problem with the original launch method

The developer opened an admin shell, changed directory, and typed `.\install_classic_dev.ps1`. The script then ran **inside** that already-running `powershell.exe`, so the process's command line was just the bare quoted path of PowerShell. Any exclusion built on it would cover every interactive PowerShell on the host.

### 9.2 Fix: name the script in the command line

Launch the installer as a child `powershell.exe` with the full script path:

```
powershell.exe -NoProfile -File "C:\Users\username\Projects\gitdirname\classic-dev\install_classic_dev.ps1"
```

Now the command line itself identifies the script, and the exclusion can be tied to it.

### 9.3 Gotcha: working directory

The scripts call each other with relative paths (`./write_header.ps1`) and expect to run from their own folder. The first attempt failed with:

```
./write_header.ps1 : The term './write_header.ps1' is not recognized as the name of a cmdlet, function, script file...
At ...\install_classic_dev.ps1:6 char:1
```

Cause: the child process did not start in the script's folder. Fix, in the same admin window:

```
cd /d "C:\Users\username\Projects\gitdirname\classic-dev"
powershell.exe -NoProfile -File "C:\Users\username\Projects\gitdirname\classic-dev\install_classic_dev.ps1"
```

Alternatives, if needed (each changes the command line, so the exclusion pattern would need rebuilding):

```
powershell.exe -NoProfile -Command "Set-Location 'C:\Users\username\Projects\gitdirname\classic-dev'; & '.\install_classic_dev.ps1'"
```

or add `Set-Location $PSScriptRoot` to the top of the script.

### 9.4 Rules for keeping the exclusion valid

- Agree one exact launch form and do not change it.
- Do not add parameters, because they become part of the command line.
- Launch from the same parent (here `cmd.exe`).
- If a sub-script starts its own `powershell.exe`, that child has its own command line and may need separate coverage. The `sc.exe` calls here all came from one process, so this probably does not apply.

### 9.5 Can the user go back to running it from inside PowerShell?

No, not without changing the exclusion. The exclusion matches a process record: the System32 `powershell.exe`, the `-File` command line, a `cmd.exe` parent and an `explorer.exe` grandparent. Typing `.\install_classic_dev.ps1` in an open PowerShell creates no such process, so the old detection returns. Running the `-File` command from inside PowerShell changes the parent to `powershell.exe`, which does not match either.

Options if someone insists:

1. Add a second exclusion for the new parent chain, built from a real detection.
2. Turn off the ancestor patterns. That is simple and also helps on older sensors, but it is broader.

What was agreed: keep the two-step `cmd.exe` method.

### 9.6 Why the launch method changes what EDR records

- **Script run inside an open shell:** no new process starts. The process record is the bare `powershell.exe`, and nothing in it says which script is running.
- **`powershell.exe -NoProfile -File "<path>"`:** a new process starts with its own ID, its own start and end time, the script path in its command line, and a recorded parent.
- The sensor sees the same behavior in both cases and the detection fires in both. The difference is that an exclusion can only match properties recorded on the process, so the second method is the only one that lets you exclude one script instead of every interactive PowerShell.
- Sub-scripts called with `&` or dot-sourcing run in the same child process. Only a script that starts another `powershell.exe` creates a new process with its own command line.
- A killed child leaves the user's `cmd.exe` window alive, whereas a killed interactive shell loses the session.
- Windows also has an interface (AMSI) that lets security tools inspect script content, and PowerShell can log script blocks. I could not confirm what Falcon collects from these in this tenant, so do not assume the shell route is invisible.

---

## 10. Building the IOA exclusion, step by step

### 10.1 Prepare

1. Create a **static host group** containing only the dev host (plus any other host formally approved for this install).
2. Have the developer run the launch command once. It will be killed, which produces a detection with the real command line.
3. Run query 6.1 to get the detection time, `PatternId` and command line.

### 10.2 Create from the detection

Open the new detection and choose **Create IOA exclusion**, so the form pre-fills from this exact process. Then edit.

### 10.3 Final field values

| Field | Value |
|---|---|
| Host groups | Remove all six pre-filled groups (they covered tens of thousands of hosts). Add only the new group (saved as GSOC-HSTGRP, initially one host) |
| Image filename | Keep the pre-filled System32 `powershell.exe` pattern (SysWOW64 is not covered) |
| Command line | See below |
| Parent | `cmd.exe` pattern (pre-filled) |
| Grandparent | `explorer.exe` pattern (pre-filled) |
| Name | GSOC-HSTGRP (the exclusion was saved under the ticket-style name, with UK-HOSTNAME in the description) |
| Description | Why, script path, host, requester, ticket, review date, removal condition |
| Audit comment | Scope summary, vendor case number, `PatternId` 10133 |

The auto-generated command line pattern was roughly the following. This is my reconstruction from a screenshot, so compare it with what your console shows:

```
.*powershell\.exe\s+-NoProfile\s+-File\s+.*\\Users\\username\\Projects\\gitdirname\\classic-dev\\install_classic_dev\.ps1.*
```

(with a drive-letter wildcard and a trailing wildcard). The test string matched. A tighter version is:

```
.*powershell\.exe\s+-NoProfile\s+-File\s+"C:\\Users\\username\\Projects\\gitdirname\\classic-dev\\install_classic_dev\.ps1"
```

This removes the drive wildcard and the trailing wildcard, so other drives and extra arguments no longer match. Always re-run **Test pattern** after editing. If the test string no longer matches, restore the original.

### 10.4 Checks before saving

1. Scroll to the top of the form and confirm host groups. This is the most important setting.
2. Click **Expand** on any "suggestion" shown under a pattern and accept it only if it does not broaden the match.
3. Fill in the name, description and audit comment.

### 10.5 After saving

1. Wait a few minutes for the sensor to receive the exclusion.
2. Re-run the install from the same admin `cmd.exe` window, with the same command.
3. Confirm PowerShell is no longer killed and no new MaliciousInjection detection appears.
4. Set a calendar review reminder. To my knowledge IOA exclusions do not expire on their own, so removal has to be tracked manually.
5. Update the vendor case with the result.

### 10.6 What an exclusion does not do

Only MaliciousInjection is relaxed, and only when all of these match: the host group, the PowerShell image, the exact command line and the ancestor chain. All other Falcon detections stay active.

### 10.7 Risks you accept

- Anyone who can edit the script file can change what runs under the exclusion. Name an owner.
- The ancestor option does not apply on older sensors, so the exclusion will not take effect there.
- If the launch method changes, the exclusion stops matching.
- The folder is user-writable, which is another reason not to use a folder wildcard.

### 10.8 Extending the exclusion to more users

A second requirement came up: other developers run the same script, each from their own user profile, so a path containing one username would not match them.

**What was agreed:** the command line pattern was changed to

```
.*\\gitdirname\\classic-dev\\install_classic_dev\.ps1"
```

This matches any command line that ends in `\gitdirname\classic-dev\install_classic_dev.ps1"` with the closing quote, whatever the drive or username before it. Other hosts are added to the same host group.

**What this pattern restricts, and what it does not:**

- It does not check the drive, the user folder, `-NoProfile` or `-File`. It also does not check any arguments that appear before the path.
- The closing quote means arguments after the path should not match, provided the form matches the whole command line. That is an assumption, so test it (below).
- The real limits are the host group, the System32 `powershell.exe` image, the `cmd.exe` then `explorer.exe` chain and the exact script name.
- The tighter alternative I suggested was `.*powershell\.exe\s+-NoProfile\s+-File\s+"C:\\Users\\[^\\]+\\Projects\\gitdirname\\classic-dev\\install_classic_dev\.ps1"`. The looser pattern was chosen for simplicity.

**Test the pattern with full command lines, not just the path.** A green "Test string matches" on a path-only string proves little.

- Should match: `powershell.exe -NoProfile -File "C:\Users\username\Projects\gitdirname\classic-dev\install_classic_dev.ps1"`
- Should match: the same with another username.
- Should not match: the same line with an extra argument after the closing quote.
- If the last one still matches, the form is not anchoring and the exclusion is wider than intended.

**Host group management** (the group is now the main control):

1. Check where the group is used (policies, other exclusions) before adding hosts.
2. Update the exclusion name, description and group name to say what the group is for, and list owners and ticket numbers.
3. Add each host through a short approval step: owner, ticket, date added, review date.
4. Check each new host's sensor version, because older sensors ignore ancestor exclusions and the run will still be killed.
5. Have the user do a first run and check the host for new detections (6.11).

**What users are told to do** (same admin Command Prompt window, plain quotes and hyphens, no extra parameters):

```
cd /d "C:\Users\<user>\Projects\gitdirname\classic-dev"
powershell.exe -NoProfile -File "C:\Users\<user>\Projects\gitdirname\classic-dev\install_classic_dev.ps1"
```

Things that stop it matching: opening cmd from Windows Terminal or with arguments (the ancestors change), curly quotes or long dashes from copied text, extra parameters, a missing closing quote, a different script name, or an old sensor.

---

## 11. The broader question: unsigned internal executables

The original team question: Falcon blocks unsigned, packed or high-entropy internal executables that look like malware, and the builds change quickly. A layered approach:

1. **Sign the binaries.** The real fix. Use an internal or commercial code-signing certificate in the CI/CD pipeline. Trust then follows the signer, not the file hash.
2. **Certificate-based allowlisting**, where your Falcon version and license support it. Check the current console options. It survives rebuilds.
3. **Scoped path exclusions as an interim measure.** ML only, specific dev or build hosts, a dedicated output folder, never fleet-wide.
4. **A dedicated host group and policy for developer and build machines.** Tune prevention there without weakening production policy. This is the sanctioned alternative to scattered exclusions.
5. **Submit false positives to the vendor** for stable, widely distributed software. This does not help for constantly changing builds.
6. **Governance.** Every exclusion needs an owner, justification, ticket and review date.
7. **Push back on obfuscation and packing.** Removing them often removes the detection.
8. **Track volume.** If these cases recur, that is the business case for mandatory signing.

How this case maps to it:

- **Release from quarantine** is a one-off and does not scale.
- **Hash exclusions** break on every rebuild.
- **This case is behavioral, not ML.** The signing argument still helps, but the durable control is the managed dev host group plus a single narrow exclusion with an owner.

---

## 12. Status and open items

| Item | State |
|---|---|
| IOA exclusion form built and pattern tested | Done |
| Exclusion saved as GSOC-HSTGRP, host group GSOC-HSTGRP | Done |
| Developer re-test after saving | Worked |
| Command line pattern made username-independent | Edited to the `\gitdirname\classic-dev\install_classic_dev.ps1"` form; run the "should not match" test and confirm it is saved |
| Host group renamed and documented for multiple hosts | Pending |
| Each additional host: sensor version check and first-run test | Per host |
| Vendor case updated with `sc.exe` evidence, `PatternId` 10133, detection times and exclusion scope | Pending |
| 90-day recurrence query (6.7) | Not yet run |
| Sensor version captured (6.8) | Not yet run |
| Service binaries compared with the other team's build output | Not yet done |
| Review reminder set | Pending |

Questions for the vendor:

1. What behavior does `DetectName` `WmiUninstallFalcon` (pattern 10133) match?
2. Which event actually triggered the kill? The `sc.exe` injection events were 1 to 2 minutes before PowerShell was terminated.
3. Has IOA logic or the sensor changed since March/April?
4. Is there a narrower supported exclusion, including whether it can be scoped to the injectee?
5. Is a dedicated host group with its own prevention policy preferred?

---

## 13. Reusable checklist: investigating any behavioral IOA false positive

1. **Classify the detection:** file-based (quarantine) or behavioral (process killed, operation blocked).
2. **Capture the essentials:** host, user, time, `PatternId`, IOA name, command line, parent, grandparent, process ID, action taken.
3. **Fix the time zone** before querying.
4. **Pull the detection event** (`Event_EppDetectionSummaryEvent`) and confirm field names on one raw row.
5. **Rebuild the process tree** with `ProcessRollup2`: the process, its parent, its children.
6. **Inventory the telemetry** with `groupBy([#event_simpleName])` on the relevant process IDs.
7. **Read the specialized events** (`ProcessInjection`, module loads, file writes) to find the injector and injectee.
8. **Inspect what it launched** and check for any reference to the security product.
9. **Decide legitimacy**, with evidence: owner confirmation, hash comparison, scope of activity.
10. **Check recurrence** across the estate.
11. **Choose the narrowest control**: host group, exact command line, ancestors, ML-only where applicable.
12. **Make the activity identifiable**: for example launch scripts with `-File` and a full path.
13. **Test and verify:** re-run, confirm no detection, confirm nothing else changed.
14. **Document:** owner, ticket, review date, removal condition.
15. **Tell the vendor** what you found and ask what the logic matches.

---

## 14. Claims to treat with caution

These were my best understanding but were not verified in this case:

- The meaning of PowerShell's exit code 0xE0000027.
- The nature of the 565 `RemediationMonitorQuarantineFile` events.
- What `WmiUninstallFalcon` matches beyond being an internal detect label.
- That IOA exclusions do not expire automatically.
- That exclusions take only a few minutes to reach sensors.
- Exact field names in `ProcessInjection` across sensor versions.

When in doubt, confirm in the console or ask the vendor.

---

## 15. Resolution, step by step: what we first suggested and what was agreed

This section replays the case in order. For each step it shows the first suggestion, then what was agreed with the end user (the developer) and why it changed.

### Step 1: The pre-filled exclusion form
- **First suggested:** do not save it. It matched any bare `powershell.exe`, interactive parents (`explorer.exe`, `userinit.exe`) and about 90,000 hosts.
- **Agreed:** not saved. Build the exclusion from a fresh detection, with a new, small host group.
- **Why:** the pre-fill amounted to a fleet-wide blind spot for a common attacker technique.

### Step 2: Find out who was injecting
- **First suggested:** open the process tree and identify the injector. Later I guessed `InstallUtil.exe`.
- **Agreed:** Advanced Event Search showed the injector was `powershell.exe` itself, injecting into ten `sc.exe` processes.
- **Why it changed:** the `ProcessInjection` telemetry showed what the detection page did not. The guess was wrong, which is why queries come before conclusions.

### Step 3: Judge whether it was legitimate
- **First suggested:** check for Falcon references in the script's activity, recurrence on other hosts, and the binaries against the other team's pipeline.
- **Agreed:** the script deletes 23 old application services with `sc.exe delete` and installs new ones with `InstallUtil.exe`. Nothing touched Falcon. The user confirmed this is what the script is designed to do.
- **Open:** recurrence across the estate and the build-pipeline comparison.

### Step 4: Which exclusion type
- **First suggested:** an IOA exclusion, scoped as narrowly as possible.
- **User question:** could a sensor visibility exclusion for the dev folder do it?
- **Agreed:** no. The flagged process is the System32 `powershell.exe`, not a file in that folder, and an SVE would hide the whole folder from the sensor.

### Step 5: How to make the exclusion narrow
- **First suggested:** keep the ancestor patterns (I wrongly said they might pin the injector), then correct: they only describe the lineage of the detected process, so the only real narrowing is host group plus command line.
- **Agreed:** make the command line identify the script by launching it as a child `powershell.exe -NoProfile -File "<full path>"`.
- **Why:** run inside an open shell, the process command line is the bare PowerShell path and no exclusion can name the script (see 9.6).

### Step 6: Make the launch work for the user
- **First suggested:** `powershell.exe -NoProfile -File "<path>"`.
- **What happened:** the script failed with `./write_header.ps1 is not recognized` because the child process did not start in the script's folder.
- **Agreed:** a two-step method in one admin `cmd.exe` window:
  `cd /d "C:\Users\<user>\Projects\gitdirname\classic-dev"`
  `powershell.exe -NoProfile -File "C:\Users\<user>\Projects\gitdirname\classic-dev\install_classic_dev.ps1"`
- **Why:** a child process inherits the working directory of the shell that starts it.

### Step 7: Build the exclusion from a real detection
- **First suggested:** run it once, let it be killed, then use "Create IOA exclusion" on the new detection so the patterns pre-fill (image, command line, parent `cmd.exe`, grandparent `explorer.exe`).
- **Agreed:** done. Saved as GSOC-HSTGRP for MaliciousInjection, host group GSOC-HSTGRP, with the System32 `powershell.exe`, the script command line, `cmd.exe` parent and `explorer.exe` grandparent.
- **Console message:** the console said no existing detections were affected. My reading, not confirmed against the console wording: an exclusion applies to new events once the sensor receives it, so it says nothing about future runs. The real test is step 8.

### Step 8: Verify
- **First suggested:** re-run after a few minutes and check for new detections with queries 6.1 and 6.11.
- **Agreed result:** the re-test worked. The install ran without PowerShell being killed.

### Step 9: Can the user return to running it from PowerShell?
- **First suggested (when asked):** no, that would be killed again; options were a second exclusion or turning off ancestors.
- **Agreed:** keep the two-step `cmd.exe` method (see 9.5).

### Step 10: More users with different usernames
- **First suggested:** replace the username with a single-folder wildcard (`[^\\]+`), keep `-NoProfile -File` and the closing quote, and treat the host group as the main control. Alternatives were one exclusion per user, a shared standard path, or the looser "ends in the script name" pattern.
- **Agreed:** the looser pattern `.*\\gitdirname\\classic-dev\\install_classic_dev\.ps1"`, with other hosts added to the same group.
- **Trade-off accepted:** the pattern no longer checks the drive, user folder or flags. Safety rests on the host group, image, parent chain and script name, so each added host needs an owner, ticket, sensor check and first-run test.

### Step 11: Close out
- **Still to do:** update the vendor case, run the 90-day recurrence query, set a review date, document each host in the group, and retire the exclusion when the binaries are signed.
- **What was agreed with the user:** they keep the two-step process, copy commands from a code block, add no parameters and open Command Prompt as administrator directly.

### Summary table

| Step | First suggested | Agreed |
|---|---|---|
| 1. Pre-filled form | Do not save | Not saved; rebuilt from a fresh detection |
| 2. Injector | `InstallUtil.exe` (guess) | `powershell.exe` into `sc.exe`, from telemetry |
| 3. Legitimacy | Verify no Falcon references, recurrence, hashes | Confirmed script purpose; recurrence still to run |
| 4. Exclusion type | IOA exclusion | IOA; folder SVE rejected |
| 5. Narrowing | Ancestors (corrected later) | Launch with `-File` so the command line names the script |
| 6. Launch | `-File` only | `cd /d` then `-File` in one `cmd.exe` window |
| 7. Build | From a fresh detection | GSOC-HSTGRP saved |
| 8. Verify | Re-run and query | Worked |
| 9. From PowerShell | Not covered | Stay with `cmd.exe` |
| 10. Many users | Username wildcard or per-user | Looser script-path pattern plus managed host group |
| 11. Close out | Vendor, recurrence, review date | Pending |

---

## 16. Glossary

| Term | Meaning |
|---|---|
| AES | Advanced Event Search in the Falcon console, using LogScale query syntax |
| IOA | Indicator of Attack, a behavior-based detection |
| IOA exclusion | An exception that stops a specific IOA firing for matching processes and hosts |
| ML exclusion | An exception for machine-learning file detections on a path or hash |
| SVE | Sensor visibility exclusion, which hides a path from the sensor entirely |
| Injector / injectee | The process doing the injecting / the process being injected into |
| `ProcessRollup2` | Process-creation event with image, command line, parent and hash |
| `TargetProcessId` | The process's own ID in `ProcessRollup2` |
| `ParentProcessId` | The ID of the process's parent |
| `ContextProcessId` | The process that performed an action in other event types |
| `Event_EppDetectionSummaryEvent` | The detection summary event in this tenant's detections repo |
| `PatternId` | The ID of the detection logic that fired |
| `InstallUtil.exe` | .NET tool for installing Windows services, also a known evasion technique (T1218.004) |
| `sc.exe` | Windows Service Control command-line tool |
| IST / BST / UTC | India Standard Time (UTC+5:30), British Summer Time (UTC+1), Coordinated Universal Time |
| T1055 | MITRE ATT&CK Process Injection |

---

*End of article.*
