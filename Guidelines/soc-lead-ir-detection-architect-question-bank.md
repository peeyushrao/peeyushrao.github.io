# SOC Lead, IR, Detection Engineering and Architect Question Bank


---

## Part 1: Foundations (Q1 to Q50)

### SOC Foundations

- **Q1.** What is the primary mission of a Security Operations Center (SOC)?
- **Q2.** What is the difference between an alert, a detection, and an incident?
- **Q3.** Why is context more important than severity alone?
- **Q4.** Why should SOC decisions be risk-driven rather than severity-driven?
- **Q5.** What information should be gathered before escalating an alert?
- **Q6.** What is alert fatigue, and why is it dangerous?
- **Q7.** What is a false positive, and how do you confirm one?
- **Q8.** What is a true positive with low business risk?

### Telemetry, Timelines and Baselines

- **Q6b.** Why are accurate timestamps critical during investigations?
- **Q7b.** What is the difference between endpoint and network telemetry, and why do we need both?
- **Q8b.** Why is baselining normal behaviour important?
- **Q8c (unnumbered).** How do you build a baseline for a network you have never seen before?
- **Q33.** What data sources help build an attack timeline?

### Process and Execution

- **Q9a (unnumbered).** What is a process, and how is it different from a service?
- **Q9.** What role does explorer.exe play in user activity?
- **Q10.** Why is svchost.exe commonly abused by attackers?
- **Q11.** Why is execution from AppData often suspicious?
- **Q12.** What are LOLBins, and why are they dangerous?
- **Q13.** What is a parent-child process relationship?
- **Q14.** What makes a process tree suspicious?
- **Q15.** Why is command-line visibility important for SOC analysts?
- **Q16.** What is DLL sideloading at a high level?
- **Q16a (unnumbered).** Why do attackers prefer signed binaries?

### Identity, Access and Credentials

- **Q17.** What is the difference between authentication and authorisation?
- **Q18 [gap fill].** How do you distinguish a true positive from a benign administrative action that looks identical on the endpoint?
- **Q19.** What defines a privileged account?
- **Q19a (unnumbered).** Why are service accounts frequently targeted?
- **Q20.** What is credential dumping?
- **Q21.** Why is NTLM considered risky?
- **Q22.** What is pass-the-hash?
- **Q23.** Why does MFA not fully prevent compromise?
- **Q24.** Which logs help detect account compromise?
- **Q25.** What does least privilege mean in practice?

### Attacker Behaviour

- **Q25a (unnumbered).** What is lateral movement?

### Incident Response Basics

- **Q26.** What are the basic phases of incident response?
- **Q27.** Why is containment often prioritised over eradication?
- **Q28.** When should a host be isolated?
- **Q29.** What risks come with immediate isolation?
- **Q30.** What is scoping, and why is it critical?
- **Q31.** What is evidence preservation?
- **Q32.** Why should compromised systems not be rebooted immediately?

### Detection Basics and Indicators

- **Q34.** What is an IOC?
- **Q35.** Why are IOCs insufficient by themselves?
- **Q37.** What is a SIEM, and what problem does it solve?
- **Q38.** What is log normalisation?
- **Q39.** Why does missing telemetry create detection blind spots?
- **Q40.** What is a correlation rule?
- **Q41.** Why do static detections fail over time?
- **Q42.** What is behavioural detection?
- **Q43.** Why do attackers evade signature-based detection?
- **Q44.** What is a detection gap?
- **Q45.** Why map detections to MITRE ATT&CK?
- **Q46.** What is the difference between detection coverage and detection quality?

### Investigation Practice

- **Q47 [gap fill].** How do you decide when a detection needs a new rule versus tuning an existing one?
- **Q48 [gap fill].** What does a good detection ticket or runbook contain?
- **Q49 [gap fill].** How do you handle a detection that works in a lab but fires nothing in production?
- **Q50 [gap fill].** How do you decide whether a detection is worth its operational cost?

---

## Part 2: Intermediate (Q51 to Q100)

### Investigation and Triage

- **Q51.** How do you determine whether multiple alerts from one host are related?
- **Q52.** How do you decide whether an alert should become an incident?
- **Q53.** What factors influence alert prioritisation besides severity?
- **Q54.** How do you determine whether suspicious activity is user-driven or attacker-driven?
- **Q55.** How do you investigate when logs are missing or incomplete?
- **Q56.** What is dwell time, and why does it matter?
- **Q57.** How do you scope an incident when only one alert exists?
- **Q58.** Which data sources do you pivot to first during endpoint investigations?
- **Q59.** How do you identify the initial access vector?
- **Q60.** How do you confirm whether malware actually executed?
- **Q61.** What indicators suggest lateral movement has occurred?
- **Q62.** How do you differentiate ransomware precursors from legitimate admin behaviour?
- **Q63.** How do you identify persistence mechanisms?
- **Q64.** How do you investigate suspicious scheduled tasks?
- **Q65.** Why is registry-based persistence difficult to detect?
- **Q66.** How do you investigate suspicious service creation?
- **Q67.** What is the role of PowerShell logging in incident response?
- **Q68.** How do you determine whether PowerShell activity is malicious?
- **Q69.** What artifacts indicate credential dumping?
- **Q70.** How do you investigate LSASS access alerts?

### Incident Response in Practice

- **Q71.** When should legal or compliance teams be involved?
- **Q72.** What communication mistakes commonly occur during incidents?
- **Q73.** How do you manage executive pressure during a live incident?
- **Q74.** When is full network containment justified?
- **Q75.** What risks exist when isolating domain controllers?
- **Q76.** How do you manage incidents across multiple regions or time zones?
- **Q77.** How do you determine whether an incident is ongoing or historical?
- **Q78.** What criteria indicate an incident is contained?
- **Q79.** How do you validate successful eradication?
- **Q80.** What artifacts should always be reviewed post-incident?
- **Q81.** How do you prevent incident recurrence?
- **Q82.** What is the role of root cause analysis?
- **Q83.** How do you differentiate attacker tools from admin tools?
- **Q84.** What makes insider threat investigations unique?
- **Q85.** How do you handle incidents involving third-party vendors?
- **Q86.** How do you balance speed versus accuracy in incident response?
- **Q95.** What makes an investigation legally defensible?
- **Q96.** How do you handle false negatives discovered post-breach?
- **Q97.** What is your evidence retention strategy?
- **Q98.** How do you handle overlapping or cascading incidents?
- **Q99.** How do you assess business impact during incident response?

### SOC Program and Training

- **Q87.** What metrics define SOC effectiveness?
- **Q88.** How do you improve analyst decision-making quality?
- **Q89.** How do you tune detections after incidents?
- **Q90.** What lessons should always be documented?
- **Q91.** How do you identify detection blind spots?
- **Q92.** How do you test incident response readiness?
- **Q93.** Which tabletop exercises are most valuable?
- **Q94.** How do you train junior analysts effectively?
- **Q100.** What distinguishes a SOC Lead from a senior SOC analyst?

---

## Part 3: Advanced (Q101 to Q150)

### Evasion and Endpoint Visibility

- **Q101.** How do attackers evade EDR without exploiting vulnerabilities?
- **Q102.** What telemetry gaps exist in user-mode monitoring?
- **Q103.** How do kernel callbacks improve detection capability?
- **Q104.** Why does process injection detection create false positives?
- **Q105.** How do you detect living-off-the-land attacks?
- **Q106.** What are the limitations of hash-based detection?
- **Q130.** Why does EDR visibility differ by OS version?
- **Q135.** How do attackers blend into normal baseline behaviour?

### Behavioural Detection Engineering

- **Q109.** How do you detect malicious rundll32.exe usage?
- **Q110.** How do you identify abnormal DLL load behaviour?
- **Q111.** How do you design detections resilient to file renaming?
- **Q112.** What is behaviour chaining, and why is it effective?
- **Q113.** How do you reduce false positives in behavioural rules?
- **Q114.** Why is command-line based detection fragile?
- **Q129.** How do you detect LOLBin abuse at scale?
- **Q134.** How do you detect encoded or obfuscated scripts?

### Persistence and Services

- **Q115.** How do attackers abuse Windows services?
- **Q116.** How do you detect service-based persistence?
- **Q117.** What telemetry helps detect scheduled task abuse?
- **Q118.** How do you detect malicious registry modifications?
- **Q131.** How do attackers abuse WMI?
- **Q132.** How do you detect WMI-based persistence?
- **Q133.** Why is PowerShell v2 especially dangerous?

### Memory and Credential Attacks

- **Q119.** How do you detect memory-only attacks?
- **Q120.** What limitations exist in memory scanning?
- **Q121.** How do attackers bypass AMSI?
- **Q122.** How do you design detections assuming an AMSI bypass?
- **Q123.** What is the value of API-level telemetry?
- **Q124.** How do you detect credential theft without signatures?
- **Q125.** What behaviours indicate token manipulation?
- **Q126.** How do you detect suspicious handle access?
- **Q127.** How do you identify process hollowing?
- **Q128.** What telemetry is required to detect reflective DLL injection?

### Detection Program Management

- **Q136.** How do you measure detection coverage objectively?
- **Q137.** What is detection decay?
- **Q138.** How do you continuously validate detections?
- **Q139.** What is the role of threat modelling in detection design?
- **Q140.** How do you balance prevention and detection?
- **Q141.** How do you safely test detections in production?
- **Q142.** What is purple team methodology?
- **Q143.** How do red team results influence detection strategy?
- **Q144.** How do you prioritise detection engineering work?
- **Q145.** What makes a detection enterprise-grade?
- **Q146.** How do you manage detection versioning?
- **Q147.** How do you retire ineffective detections?
- **Q148.** How do you document detection logic?
- **Q149.** How do you measure detection success?
- **Q150.** What distinguishes a detection engineer from a SOC analyst?

---

## Part 4: Architect and Lead (Q151 to Q200)

- **Q151.** How do you design a SOC for a global enterprise?
- **Q152.** Which telemetry sources are mandatory versus optional?
- **Q153.** How do you architect detection across endpoint, cloud, and identity?
- **Q154.** How do you minimise vendor lock-in?
- **Q155.** How do you architect around EDR blind spots?
- **Q156.** How do you design for dwell-time reduction?
- **Q157.** How do you align SOC architecture with business risk?
- **Q158.** How do you architect ransomware defence holistically?
- **Q159.** How do you design incident escalation paths?
- **Q160.** How do you define SOC maturity?
- **Q161.** How do you handle incidents spanning on-prem and cloud environments?
- **Q162.** Which architectural decisions most affect incident response speed?
- **Q163.** How do you design resilient logging pipelines?
- **Q164.** How do you manage telemetry overload?
- **Q165.** Why is time synchronisation critical, and how do you enforce it?
- **Q166.** How do you design detection for encrypted traffic?
- **Q167.** How do you implement SOAR responsibly?
- **Q168.** When does automation become dangerous?
- **Q169.** How do you design effective human-in-the-loop workflows?
- **Q170.** How do you stress-test SOC architecture?
- **Q171.** How do you manage multiple simultaneous major incidents?
- **Q172.** How do you decide when systems must be shut down?
- **Q173.** How do you communicate uncertainty to executives?
- **Q174.** How do you handle incomplete attacker attribution?
- **Q175.** How do you lead during ransomware negotiations?
- **Q176.** How do you balance transparency and panic control?
- **Q177.** How do you manage cross-team coordination during crises?
- **Q178.** How do you prevent analyst burnout?
- **Q179.** How do you institutionalise lessons learned?
- **Q180.** How do you evolve SOC strategy year over year?
- **Q181.** How do you evaluate new security tools objectively?
- **Q182.** How do you sunset legacy security controls?
- **Q183.** What is detection debt, and how do you reduce it?
- **Q184.** How do you translate MITRE ATT&CK into business language?
- **Q185.** How do you justify SOC budget to leadership?
- **Q186.** How do you measure ROI for security controls?
- **Q187.** How do you assess organisational risk tolerance?
- **Q188.** How do you secure mergers and acquisitions?
- **Q189.** How do you maintain security during rapid growth?
- **Q190.** How do you implement zero trust pragmatically?
- **Q191.** How do you plan for unknown attacker techniques?
- **Q192.** How do you detect attacks without relying on IOCs?
- **Q193.** How do you build antifragile security systems?
- **Q194.** How do you design SOC KPIs that actually matter?
- **Q195.** How do you define the boundary between analyst and automation work?
- **Q196.** How do you mentor future SOC leaders?
- **Q197.** How do you transition from technical expert to strategic leader?
- **Q198.** How do you validate long-term detection effectiveness?
- **Q199.** How do you prepare for breaches you cannot prevent?
- **Q200.** What does good security look like at enterprise scale?

---

## Part 5: Added Interview Questions

### CrowdStrike Falcon [added]

- How would you use Falcon Insight to reconstruct an attack from a single detection on one host?
- What are the differences between a Custom IOA and a built-in detection, and when would you choose each?
- How do you validate a Custom IOA before rolling it out to a large fleet?
- How would you use Falcon Fusion to automate containment for a specific high-confidence detection, and what guardrails would you add?
- When would you use Real Time Response to collect evidence, and what must you avoid during a live RTR session?
- How do prevention policy settings like machine learning levels affect false positives on servers versus workstations?
- How would you handle a sensor performance issue on a critical server without weakening protection?
- How do you manage sensor update policies so a bad sensor version does not reach production at once?
- How does Falcon Flight Control work in a multi-CID environment, and what changes should be made only at the parent level?
- What operational risks arise when the same detection logic exists in several CIDs with different tuning?
- How would you use LogScale to hunt for a technique across the whole fleet when Event Search alone is too slow?
- What fields would you pivot on when hunting for LSASS access across thousands of hosts?
- How would you design a Falcon audit to confirm that policies, exclusions, and sensor versions are still compliant?
- How do you review exclusions to make sure they are not creating blind spots?
- How do you decide between prevention and detect-only mode when rolling out a new policy?
- What is the role of Falcon Identity Protection in investigating a compromised privileged account?
- How does Falcon Overwatch complement an internal SOC, and what would you expect from it?
- How would you use Falcon Discover or Falcon Surface to support investigation and scoping?
- Walk me through a time you used a Falcon feature to change a detection outcome. What did you change and why?
- How would you explain a high-CPU complaint on a critical server to a business owner while the investigation is still open?

### Zscaler, Cloud and Identity [added]

- How do ZIA and ZPA differ in what traffic they inspect and how they control access?
- How would you use ZDX data to separate an application problem from a security control problem?
- What telemetry from Zscaler would you use to detect data exfiltration through a sanctioned cloud application?
- How would you investigate a user who reports that a private application is suddenly unreachable: a policy change, a posture failure, or an attack?
- How does zero trust change the detection model compared with a perimeter-based model?
- What signals would you correlate across endpoint, proxy, and identity logs to detect an active session hijack?
- How would you detect an impossible-travel login and decide whether it is a true positive?
- Why are service principals and API tokens harder to monitor than user accounts, and how would you monitor them?
- How would you use cloud audit logs to scope a compromised cloud role?
- What are the detection risks of over-privileged cloud roles, and how do you find them?
- How would you detect a misconfigured storage bucket being made public?
- How do you secure a hybrid identity environment where on-premises AD syncs to a cloud directory?

### Scenario-Based Incident Response [added]

- An EDR alert shows a signed management tool spawning PowerShell on a finance server. Walk me through your first 15 minutes.
- Multiple users report MFA prompts they did not initiate. What do you check, and when do you escalate?
- A ransomware precursor is detected on one file server at 2 a.m. What do you isolate, and what do you leave running?
- During an investigation you discover the attacker has been in the environment for 90 days. How do you rescope the entire incident?
- A junior analyst closed an alert that later turned out to be an active intrusion. How do you handle the review without blaming the analyst?
- A business leader asks you to restore a server before forensics is complete. What do you say, and what do you offer instead?
- The attacker is still active, and your containment action will alert them. How do you decide whether to act immediately?
- You find a valid domain admin session on a workstation used by a help desk technician. What are your next three steps?
- A vendor's remote access tool is the likely entry point. How do you investigate without disrupting the vendor relationship?
- Logs for a critical system have a 40-minute gap. How do you decide whether it is an attacker or an outage?
- A third-party breach notification names your company, but your telemetry shows nothing. How do you investigate?
- You have confirmed a compromise but cannot identify the initial access vector. How do you present this to leadership?
- A detection fires on every host after a legitimate software rollout. How do you respond to the alert storm?
- An attacker used a legitimate admin tool your team uses daily. How do you find the difference?
- Your SOAR playbook isolated a production database server by mistake. What do you do first, and what do you change afterwards?

### Detection Engineering Craft [added]

- What is the difference between a detection hypothesis and a detection rule, and why does the hypothesis come first?
- How do you test a detection for false positives before deployment in a large environment?
- How do you measure a detection's true positive rate when you rarely see real attacks?
- How would you write a detection for a technique that only leaves evidence in memory?
- How do you balance detection depth against analyst workload when a rule is useful but noisy?
- How do you set severity for a detection, and who should own that decision?
- What does a detection lifecycle look like from idea to retirement?
- How do you use atomic tests or simulation frameworks to validate detections?
- What makes a detection resilient to attacker modification of the tool, path, or command line?
- How do you avoid writing detections that only match a single threat actor's tooling?
- What telemetry gaps would you look for first when a technique is not being detected?
- How do you document a detection so another engineer can tune it six months later?
- What metrics would you put on a detection engineering dashboard?
- How do you prioritise detection work using threat intelligence and your own incident history?
- What is the difference between a hunt that finds nothing and a hunt that proves nothing?
- How do you turn a successful hunt into a durable detection?
- What is the role of data quality in detection engineering, and how would you monitor it?
- How do you handle detection-as-code, version control, and peer review in a SOC?
- What is your approach to mapping detection coverage against MITRE ATT&CK?
- When would you accept a known gap in coverage and document it as risk?

### Leadership and Team Management [added]

- How do you structure a SOC shift rotation to avoid burnout while keeping coverage strong?
- How do you assess whether an analyst is ready to handle incidents independently?
- How do you give critical feedback to a senior analyst who is technically strong but misses documentation?
- How do you balance project work such as detection engineering against day-to-day alert queues?
- How would you build a training plan for a team that is strong on operations but weak on engineering?
- How do you handle a team member who disagrees with your decision during an active incident?
- How do you measure individual analyst performance without encouraging the wrong behaviour?
- How do you run a post-incident review that improves the process and does not feel like a trial?
- What do you do when two senior engineers disagree about the right detection approach?
- How do you onboard a new analyst into a complex multi-tool environment in their first month?
- How do you ensure knowledge is not concentrated in one person's head?
- How do you represent your team's work to non-technical leadership?
- How do you decide whether to hire for a skill gap or develop it internally?
- How do you manage a vendor relationship when the product is not meeting expectations?
- How do you set expectations with your team about on-call responsibilities and overtime?

### Behavioural and Experience-Based [added]

Prepare a STAR story (Situation, Task, Action, Result) for each.

- Tell me about a time you led an incident response under pressure. What did you do in the first hour?
- Describe a detection you tuned that reduced noise without reducing protection.
- Tell me about a time you were wrong about a technical decision. What did you learn?
- Describe a large-scale deployment you managed. What went wrong, and how did you recover?
- Tell me about a time you pushed back on a business request for security reasons.
- Describe a time you led a team through a difficult change.
- Tell me about the most complex investigation you have worked on and what made it difficult.
- Tell me about a time you improved a process that others had accepted for years.
- Describe how you have handled a conflict within a team.
- Tell me about a time you had to explain a technical risk to executives.
- Describe a mistake that caused an alert or outage and how you handled the follow-up.
- Tell me about a time you mentored someone who later outgrew your guidance.
- Why are you moving from operations toward detection engineering, and what have you done to prepare?
- What does your typical week look like when you are running a team?
- Why do you want this role, and what do you hope to change in the first six months?

### Architecture and Strategy [added]

- How would you design a SOC operating model for a company with three regions and two MSSP partners?
- How do you decide between building detection in-house and buying a managed service?
- What does a good endpoint, identity, and cloud telemetry strategy look like for a company moving cloud-first?
- How do you design log retention so you can investigate a 12-month-old incident?
- How do you design a SOC that scales without linearly increasing headcount?
- What is your approach to a security data lake versus a SIEM-centric model?
- How do you build a detection strategy when the organisation has several EDR products after an acquisition?
- What role should automation play in tier-one triage, and where should it stop?
- How would you prepare a SOC for a regulatory audit that asks for incident evidence?
- How do you structure a multi-year SOC maturity roadmap that leadership will fund?

### Rapid Knowledge Checks [added]

- What does a process hollowing attack look like in a process tree?
- Name three signs that a scheduled task is malicious.
- What is the difference between Kerberoasting and AS-REP roasting?
- What event IDs would you check for successful and failed logons on Windows?
- What is the difference between a DLL hijack and a DLL sideload?
- Why can a signed binary still be malicious?
- What does a beacon look like in network telemetry?
- What is DNS tunnelling, and what would you monitor to detect it?
- How does a Golden Ticket differ from a Silver Ticket?
- What is the purpose of a canary token?
- What is the difference between containment and isolation?
- What is a honeypot, and what does it tell you that a SIEM alert does not?
- What does a successful pass-the-ticket attack leave behind?
- What is the difference between a vulnerability scan and a threat hunt?
- What is a service account, and how do you tell it apart from a human account in logs?
- Why is timestamp drift a problem during correlation?
- What does a live memory capture help you find that disk forensics cannot?
- What is the difference between an attack surface and an attack path?
- Why is a clean antivirus scan not proof that a host is clean?
- What is an ATT&CK sub-technique, and why does it matter for coverage?

---
