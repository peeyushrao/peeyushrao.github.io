# Chapter 1: Investigating Email Threats

## 1. Overview & Objectives
Email threats are among the most frequent attacks encountered by Security Operations Center (SOC) analysts during a shift and are often the primary initial access vector for threat actors. 
* **Core Objectives:** Understand why attackers favor phishing, identify common email threat types, recognize evasion and social engineering techniques, learn the anatomy of Secure Email Gateway (SEG) logs, and master the methodology for investigating suspicious emails.

---

## 2. Top Infection Vectors & Why Attackers Prefer Phishing
Once reconnaissance and weaponization are complete, attackers choose an **initial access** method:
* Sending phishing emails (**41% of attacks** per the *IBM Security X-Force Threat Intelligence Index 2022*, followed by vulnerability exploitation at 34% and stolen credentials at 9%).
* Exploiting public-facing applications.
* Drive-by compromises (luring users to compromised websites).
* Stealing valid remote credentials (e.g., VPN, RDP).

### Figure 1.1 – Top Infection Vectors (IBM Security X-Force Threat Intelligence Index 2022)
| Infection Vector | 2021 (%) | 2020 (%) |
| :--- | :--- | :--- |
| **Phishing** | **41%** | 33% |
| **Vulnerability exploitation** | **34%** | 35% |
| **Stolen credentials** | **9%** | 18% |
| **Brute force** | **6%** | 4% |
| **Remote desktop** | **4%** | 7% |
| **Removable media** | **4%** | 0% |
| **Password spraying** | **1%** | 0% |

### Why Attackers Prefer Phishing Emails
1. **Easy Target Acquisition During Reconnaissance:** Attackers easily harvest target email addresses via job postings, LinkedIn/social media, third-party subscriptions, dark web data leaks, Wayback Machine (`Archive.org`), and marketing databases (`ZoomInfo.com`).
2. **Simple Weaponization:** It is relatively easy to upload malware to legitimate cloud platforms and share links, embed malicious **Visual Basic for Applications (VBA)** macros into Office documents, or send password-protected compressed executables.
3. **Lack of User Security Awareness:** Attackers exploit human vulnerability and insufficient security awareness training through social engineering.

---

## 3. Email Threat Types
External email threats generally fall into four main categories:

| Threat Type | Description | Common Variants / Methods |
| :--- | :--- | :--- |
| **1. Spearphishing Attachments** | Targeted emails containing malicious attachments to gain initial access or harvest credentials. *(Note: Phishing is mass/random; Spearphishing is targeted/personalized).* | • **Malicious MS Office Docs:** Word/Excel/PowerPoint with VBA macros or Office vulnerability exploits.<br>• **Malicious PDFs:** Embedded JavaScript or PDF reader exploits.<br>• **Compressed Files (`.rar`, `.7z`, `.zip`):** Contain malware executables.<br>• **ISO Images (`.iso`):** Disc images used to bypass file filters and evade AV.<br>• **HTML Files (`.html`):** Local files impersonating login pages (e.g., Microsoft, DHL, banks) to harvest credentials. |
| **2. Spearphishing Links** | Targeted emails with malicious URLs to steal credentials or trigger malware downloads. | • **Credential Harvesting Links:** Direct victims to fake login portals (hosted on attacker domains or abused cloud domains like `appspot.com` / `web.app`).<br>• **Malware Download Links:** Links to malware hosted on attacker servers or legitimate cloud storage (MEGA, OneDrive, Dropbox). |
| **3. Blackmail Emails ("Sextortion")** | Scam emails claiming the victim's machine was compromised and sensitive/sexual content was exfiltrated, demanding Bitcoin ransom. | • **Screenshots of Breached Data:** Real screenshots obtained via Infostealer malware or dark web data leaks.<br>• **Spoofing Victim's Email Address:** Scammers spoof the victim's own address (`From:` matches `To:`) to trick them into believing their account/machine is controlled by the attacker. |
| **4. Business Email Compromise (BEC)** | Targeted scams against executives or finance staff to trick them into authorizing fraudulent wire transfers or financial transactions. | • **Email Thread Hijacking:** Compromising an account, intercepting an ongoing business/invoice conversation, and replying from a lookalike domain to redirect payment (e.g., *Gold Galleon* maritime shipping attacks).<br>• **Executive/Partner Spoofing:** Spoofing a trusted executive or vendor email address. |

---

## 4. Attacker Techniques to Evade Email Security Detection
To bypass Secure Email Gateways (SEGs) and threat intelligence feeds, attackers use:
* **Newly Created Domains:** Registering fresh domains with no prior malicious history to bypass domain reputation filters.
* **Clean (Non-Blacklisted) SMTP Servers:** Sending phishing emails from SMTP server IPs that are not listed on threat intelligence blocklists.
* **Trusted Cloud Domains Hosting Phishing Pages:** Hosting phishing login pages on legitimate cloud app domains (e.g., `appspot.com`, `web.app`) that have valid reputations and SSL certificates.
* **Sandbox Analysis Evasion:**
  * **Malware Sleep:** Delaying malicious execution (e.g., sleeping for 3+ minutes) until real-time sandbox analysis times out.
  * **Password-Protected / Encrypted Files:** Sending password-protected archives or documents with the password in the email body; non-interactive gateway sandboxes cannot decrypt and inspect the file.
  * **Sandbox Discovery:** Checking for VM artifacts, analysis tools, or lack of human user activity (mouse movement/keystrokes) and halting or altering execution if detected.
  * **IP-Specific Responses:** Configuring malicious servers to respond only to requests originating from the target organization's public IP range (gathered during reconnaissance).

---

## 5. Social Engineering Techniques to Trick the Victim
Once an email bypasses technical controls, attackers use psychological manipulation to prompt user interaction:
1. **Email Spoofing:** Forging the sender address/domain (e.g., spoofing a partner bank or `irs.gov`) so the recipient trusts the message.
2. **Email Thread Hijacking (Figure 1.6):**
   * **Step 1:** The attacker has access to a compromised mailbox (`victim1@organization.com`).
   * **Step 2:** The attacker searches for an attractive email thread to hijack.
   * **Step 3:** The attacker finds an attractive email thread to `target@targetorg.com`.
   * **Step 4:** The attacker creates a new similar domain to the compromised mailbox domain named `victim1@organization.co`.
   * **Step 5:** The attacker copies the email thread to their server and replies to the email thread using the newly created domain email address.
   * **Step 6:** The email thread is hijacked; the new targeted victim doesn't notice and replies to the email thread and interacts with the attacker's mail contents.
3. **Abusing SSL Certificates (Green Padlock):** Hosting phishing sites on dynamic DNS or cloud providers that issue valid SSL/TLS certificates, exploiting users' assumption that the padlock icon means a site is legitimate.

---

## 6. The Anatomy of Secure Email Gateway (SEG) Logs
Positioned inline, SEGs inspect all inbound and outbound emails.

### Types of SEG Logs
* **SMTP Logs:** Delivery details (sender IP, recipient address, timestamps).
* **Message Tracking Logs:** Metadata for messages passing through (Message ID, sender, recipient, subject, date/time).
* **Content Filtering Logs:** Content rules triggered and whether the message was allowed or blocked.
* **Spam and Malware Logs:** Emails flagged as spam or matching malware signatures.
* **Quarantine Logs:** Metadata and reasons for quarantined emails.

### Key SEG Log Fields for SOC Analysts
* **SMTP Server IP:** The sending server's IP address (used for blacklist checks and spoofing validation).
* **Sender Email Address:** The `From` address (check against blacklisted domains; keep in mind it can be spoofed).
* **Recipient Email Address:** The target user(s) (essential for scoping potentially compromised users/machines during an incident).
* **Email Subject:** Used to spot social engineering urgency keywords (e.g., *Urgent Action Required*, *Confirm your Account Details*, *Unauthorized Access Attempt*) or subjects irrelevant to the recipient's job role (e.g., an accountant receiving an IT course email).
* **Attached Filename:** Correlate common phishing file extensions (`.docm`, `.xls`, `.pdf`, `.zip`, `.iso`, `.html`) with lure names (*Purchase order*, *Important note*, *Invoice*).
* **Attached File Hash:** MD5/SHA1/SHA256 hash of attachments (can be batch-queried against threat intelligence like VirusTotal).
* **Malware Category:** Populated when an attachment matches a signature (e.g., *ZLoader*, *RedLine Infostealer*).
* **Attached URL:** URLs extracted from the email body.
* **Device Action:** Action taken by the SEG (*Allowed*, *Delivered*, *Blocked*, *Quarantined*)—crucial for determining whether the threat reached the user's inbox.
* **Block Reason:** Why a blocked/quarantined email was stopped.

---

## 7. Methodology for Investigating Suspicious Emails
> **Golden Rule:** Follow **all** investigation steps to confirm whether an email is malicious or benign, even if an early step makes the classification seem obvious.

### Step 1: Sender Domain & SMTP Server Reputation
* **OSINT / Search Engines:** Query the sender domain on Google to check for legitimate business presence vs. threat reports/tweets flagging it in active campaigns.
* **Newly Created Domains & Free Webmail:** Lack of search results or a very recent registration date is a strong indicator of a phishing domain. Also watch out for spearphishing sent from free providers (Gmail, Yahoo).
* **Blacklist Verification:** Check the sender domain and SMTP server IP on **MxToolbox** (`https://mxtoolbox.com/`) against 82+ known blacklists.

### Step 2: Spoofing Validation (via Logs & DNS)
When an email appears to come from a legitimate organization (e.g., `fedex.com`), verify it wasn't spoofed:
1. Extract the **Sender SMTP Server IP** from the SEG logs (e.g., `95.211.214.81`).
2. Query the sender domain's authorized servers using **MxToolbox MX Lookup** (`https://mxtoolbox.com/MXLookup.aspx`). *(Note: Lowest preference number = highest priority server).*
3. Check the **WHOIS record** of the sending SMTP IP using **DomainTools** (`https://whois.domaintools.com/`).
4. **Compare:** If the sending SMTP IP belongs to an unrelated entity (e.g., `mailserver.footballticketnet.com` instead of FedEx's authorized servers), the domain was **spoofed**.

### Step 3: Email Sender Behavior
If the domain/IP is clean, not spoofed, and belongs to a known business partner, check for **compromised partner mailbox** indicators or spam behavior:
* **Communication History:** Has the recipient communicated with this sender/domain before?
* **Mass Distribution:** Did the sender send the exact same subject line to multiple recipients across different departments?
* **Role Relevance:** Does the subject align with the recipient's actual job duties?

### Step 4: Email Subject & Attached Filename Analysis
Look for high-risk social engineering keywords:
* **Common Phishing Subject Keywords:** `RE:`, `FW:`, `Invoice`, `Missing Inv`, `New Message from`, `New scanned`, `You have a New Message`, `Verification Required`, `Action Required`.
* **Common Phishing Filename Keywords:** `invoice`, `order`, `contract`, `payment`, `offer`, `planning`, `SWIFT`.

### Step 5: Investigating Suspicious Email Content (URLs & Files)
> **OPSEC Warning:** Never submit files containing sensitive or confidential corporate data to public/cloud sandboxes to avoid unintentional data leakage!

#### A. URL Analysis with urlscan.io (`https://urlscan.io/`)
* **Capabilities:** Scans URLs in **Public** or **Private** mode (use the *Options* button to switch to Private mode) and provides a searchable history of public scans.
* **What to Look For:**
  * Overall **Verdict** (e.g., *Potentially Malicious* / *Google Safe Browsing* status).
  * **Targeted Brands** (e.g., Microsoft, SharePoint, or your own organization's brand/logo).
  * **Page Screenshot** (renders the destination page safely without exposing your host).
  * **HTTP Transactions, Redirects, & Contacted IPs/Domains.**

#### B. File Analysis with ANY.RUN (`https://app.any.run/`)
* **Capabilities:** Interactive online malware sandbox allowing real-time interaction with a VM (e.g., entering a password from an email body to open an encrypted attachment).
* **Case Study Example (`VISA PAYMENT (1).xls`):**
  1. Opening `VISA PAYMENT (1).xls` in `excel.exe` drops a batch file (`UkMes.bat`) into the user profile directory.
  2. `excel.exe` spawns `cmd.exe` to execute `UkMes.bat`.
  3. `cmd.exe` spawns `powershell.exe` with a base64-encoded command-line argument.
* **Key ANY.RUN Analysis Tabs:**
  * **Process Tree (Right Pane):** Shows parent-child process relationships, threat scores (e.g., 100/100 Malicious), command-line arguments, and behavioral warnings (e.g., querying computer name, language, and install date for host discovery).
  * **HTTP Requests:** Shows processes (like `powershell.exe`) reaching out to external malicious URLs to download stage-2 binaries.
  * **Connections & DNS Requests:** Details all external IP connections and DNS queries made during detonation.
  * **Threats:** Displays matched IDS signatures on network traffic.
* **Decoding Obfuscated Commands:** Copy base64-encoded PowerShell arguments into **CyberChef** (`https://gchq.github.io/CyberChef/`) to decode and inspect the payload.
