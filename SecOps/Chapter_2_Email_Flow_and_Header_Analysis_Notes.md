# Chapter 2: Email Flow and Header Analysis (Deep-Dive Study Notes)

## 1. Chapter Overview & Core Objectives
Due to the rise in email-based threats and domain spoofing, SOC analysts cannot rely solely on high-level gateway summaries. Analysts must understand how emails travel across the internet, how authentication protocols validate sender identity, and how to dissect raw email headers to uncover spoofing and collect forensic artifacts.

* **Key Learning Objectives:**
  1. Understand the end-to-end **Email Flow** and the 5 server/agent hops involved.
  2. Master **Email Header Analysis** (reading bottom-to-top) across content metadata, custom `X-headers`, and `Received:` hop headers.
  3. Understand **Email Authentication Protocols** (**SPF, DKIM, DMARC**), their DNS TXT record syntax, and their cryptographic/validation workflows.
  4. Investigate a real-world **Spoofed Email Header** to prove domain impersonation.

---

## 2. Email Flow (Hops & Architecture)
An **email flow** is the exact path and sequence of servers ("hops") an email traverses from the moment a sender clicks "Send" until it arrives in the recipient's inbox. Most of these hops communicate using **SMTP (Simple Mail Transfer Protocol)**.

### The 5 Architectural Components of Email Flow
1. **Mail User Agent (MUA):**
   * **Role:** The client application or web interface used by the sender to compose/send the email and by the recipient to read it.
   * **Examples:** Microsoft Outlook, Mozilla Thunderbird, or webmail accessed via Google Chrome / Mozilla Firefox.
2. **Mail Submission Agent (MSA):**
   * **Role:** The initial server that receives the outgoing email submitted from the sender's MUA (often via Microsoft Exchange Server or an outbound gateway).
3. **Mail Transfer Agent (MTA):**
   * **Role:** Also known as an **SMTP relay server**. It receives the email from the MSA and routes/relays it across one or more intermediate MTA servers until it reaches the recipient domain's Mail Exchange (MX) server.
4. **Mail Exchange (MX):**
   * **Role:** The border email server responsible for accepting incoming messages destined for a specific domain.
   * **DNS Link:** Identified publicly via the recipient domain's **DNS MX records**. Organizations often deploy multiple MX servers for load balancing and failover.
5. **Mail Delivery Agent (MDA):**
   * **Role:** The internal mail server (e.g., recipient's MS Exchange Server) that receives the email from the MX server, stores it in the user's mailbox, and provides access to the recipient's MUA once the user successfully authenticates.

---

### Diagram Recreation: Figure 2.1 – Email Flow
```text
+-------------------------------------------------------------------+
| SENDER ENVIRONMENT                                                |
|                                                                   |
|   [ MUA - MS Outlook ]                                            |
|            |                                                      |
|            v                                                      |
|   [ MS Exchange Server ]                                          |
|            |                                                      |
|            v                                                      |
|     [ MSA Server ]                                                |
+------------|------------------------------------------------------+
             |
             v
+-------------------------------------------------------------------+
| INTERNET / TRANSIT RELAYS                                         |
|                                                                   |
|     [ MTA Server 1 ]                                              |
|            |          (Several MTA / SMTP Relay Servers)          |
|     [ MTA Server 2 ]                                              |
+------------|------------------------------------------------------+
             |
             v
+-------------------------------------------------------------------+
| RECIPIENT ENVIRONMENT                                             |
|                                                                   |
|      [ MX Server ]        <-- Identified via DNS MX Record        |
|            |                                                      |
|            v                                                      |
|      [ MDA Server ]       <-- (MS Exchange Server)                |
|            |                                                      |
|            v              <-- Recipient Authenticates             |
|   [ MUA - MS Outlook ]                                            |
+-------------------------------------------------------------------+
```

### Why Email Flow Matters to SOC Analysts
Every single hop that processes the email prepends a **`Received:`** header to the email message header. Each `Received:` entry logs at least three critical forensic artifacts:
1. **The email server's hostname** (`from ... by ...`)
2. **The email server's IP address**
3. **The exact date and time (timestamp) of email processing** (along with the encryption cipher/protocol used, such as `ESMTPS` and `TLSv1.2`).

#### Figure 2.2 – Example of an Email Header Added by a Hop Server
```text
Received: from mail.footballticketnet.com (mailserver.footballticketnet.com [95.211.214.81])
        by mx0b-0000da01.pphosted.com (PPS) with ESMTPS id 3jgssdsqx7-1
        (version=TLSv1.2 cipher=ECDHE-RSA-AES256-GCM-SHA384 bits=256 verify=NO)
        for <mia7ia@yahoo.com>; Mon, 12 Sep 2022 03:39:09 -0400
```
* **Breakdown of Figure 2.2:**
  * **Sending Hop:** `mail.footballticketnet.com` (`mailserver.footballticketnet.com` at IP `95.211.214.81`)
  * **Receiving Hop:** `mx0b-0000da01.pphosted.com` (Proofpoint Protection Server) using `ESMTPS`
  * **TLS Details:** `TLSv1.2` with cipher `ECDHE-RSA-AES256-GCM-SHA384`
  * **Target Recipient:** `<mia7ia@yahoo.com>`
  * **Timestamp:** `Mon, 12 Sep 2022 03:39:09 -0400`

---

## 3. Email Header Analysis

**Email header analysis** is the forensic examination of every field in the raw header to identify the true sender, originating IP, traversed hops, subject, recipient, timestamps, and authentication verdicts.

### How to Extract Raw Email Headers
* **Microsoft Outlook (Desktop):** Open the email -> click **File** -> **Info** -> **Properties** (inspect the *Internet headers* box).
* **Gmail (Web Application):** Open the email -> click **More** (three vertical dots icon) -> select **Show original**.
* **Secure Email Gateway (SEG):** Retrieve directly from the email security appliance's message tracking/quarantine console.

### The Golden Rule: Read from Bottom to Top
Because each server prepends its header information to the **top** of the existing file as the message travels forward, email headers are structured in **reverse chronological order**:
* **Bottom of the Header:** Contains the initial message body and metadata created by the sender's MUA, followed immediately above by the first hop (MSA).
* **Top of the Header:** Contains the final delivery headers (`Delivered-To:`) added by the recipient's MDA/MX server.

```text
▲  [ TOP OF HEADER ]     6. Final Delivery (`Delivered-To:`) & ARC Seals
│                        5. Recipient MX Hop (`Received: by mx.google.com`) & Auth Results
│  READ IN THIS          4. Sender MSA/MTA Hop (`Received: from sonic.gate.mail...`)
│  DIRECTION             3. Custom X-Headers (`X-Mailer`, `X-YMail-OSG`, `DKIM-Signature`)
│  (Chronological)       2. Message Metadata (`Date`, `From`, `To`, `Message-ID`, `Subject`)
█  [ BOTTOM OF HEADER ]  1. Email Message Body ("Hi Mostafa, This is to inform you...")
```

---

### Figure 2.3 – Full Legitimate Email Header Example
In this chapter's primary case study, a legitimate email is sent from **`mia7ia@yahoo.com`** to **`mostafayahia753@gmail.com`**. Below is the complete header hierarchy:

```text
---- The Start of the Email Message Header ----
Delivered-To: mostafayahia753@gmail.com
Received: by 2002:a59:a510:0:b0:304:497a:47cb with SMTP id u16csp1808417vqo;
        Fri, 30 Sep 2022 05:04:34 -0700 (PDT)
X-Google-Smtp-Source: AMsMyM43vWzx9Y3d/QKH9VL9RDH/4MQM3Y/5khBz0z/58DjjOTeKwmTbZFwU/3iNpGSxyvJx8sl4
X-Received: by 2002:a05:6122:a04:b0:3a2:bfed:602f with SMTP id 4-20020a05...;
        Fri, 30 Sep 2022 05:04:34 -0700 (PDT)
ARC-Seal: i=1; a=rsa-sha256; t=1664539474; cv=none; d=google.com; s=arc-20160816; b=a1XEs896...
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;
        h=references:content-transfer-encoding:mime-version:subject:message-id:to:from:date:dkim-signature;
        bh=1Ttd55RGpBC1Cevt3Xgw1XO9lBgWZj04bmslL5Urark=; b=PggFXj7Nh...
ARC-Authentication-Results: i=1; mx.google.com;
       dkim=pass header.i=@yahoo.com header.s=s2048 header.b=kRlmdNKB;
       spf=pass (google.com: domain of mia7ia@yahoo.com designates 66.163.188.147 as permitted sender) smtp.mailfrom=mia7ia@yahoo.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=yahoo.com
Return-Path: <mia7ia@yahoo.com>
Received: from sonic303-21.consmr.mail.ne1.yahoo.com (sonic303-21.consmr.mail.ne1.yahoo.com. [66.163.188.147])
        by mx.google.com with ESMTPS id l184-20020a6770c1000000b0039ad4f386c5si231512vsc.685.2022.09.30.05.04.33
        for <mostafayahia753@gmail.com>
        (version=TLS1_3 cipher=TLS_AES_128_GCM_SHA256 bits=128/128);
        Fri, 30 Sep 2022 05:04:34 -0700 (PDT)
Received-SPF: pass (google.com: domain of mia7ia@yahoo.com designates 66.163.188.147 as permitted sender) client-ip=66.163.188.147;
Authentication-Results: mx.google.com;
       dkim=pass header.i=@yahoo.com header.s=s2048 header.b=kRlmdNKB;
       spf=pass (google.com: domain of mia7ia@yahoo.com designates 66.163.188.147 as permitted sender) smtp.mailfrom=mia7ia@yahoo.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=yahoo.com
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=yahoo.com; s=s2048; t=1664539473;
        bh=1Ttd55RGpBC1Cevt3Xgw1XO9lBgWZj04bmslL5Urark=;
        h=Date:From:To:Subject:References:From:Subject:Reply-To;
        b=kRlmdNKBXBZsJLZvTpVqlfojnQL2aqxmliyWmE0bFLOdjgQXhpwAKF4p...
X-SONIC-DKIM-SIGN: v=1; a=rsa-sha256; c=relaxed/relaxed; d=yahoo.com; s=s2048; t=1664539473; ...
X-YMail-OSG: 02HCCH0VM1mihG5MLJQiTFXiFlNk32D5p7Kzas0agmKnAqfFh...
X-Sonic-MF: <mia7ia@yahoo.com>
Received: from sonic.gate.mail.ne1.yahoo.com by sonic303.consmr.mail.ne1.yahoo.com with HTTP;
        Fri, 30 Sep 2022 12:04:33 +0000
Date: Fri, 30 Sep 2022 12:04:29 +0000 (UTC)
From: Mostafa Mostafa <mia7ia@yahoo.com>
To: mostafayahia753@gmail.com
Message-ID: <1527240602.2832961.1664539469282@mail.yahoo.com>
Subject: SOC Investigation
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit
References: <1527240602.2832961.1664539469282.ref@mail.yahoo.com>
X-Mailer: WebService/1.1.20702 YMailNodin
Content-Length: 69

Hi Mostafa,
This is to inform you that the course will start soon.
---- The End of the Email Message Header ----
```

---

### Subsection 3.1: Email Message Content and Metadata

#### Figure 2.4 – Email Message Content and Metadata
```text
Date: Fri, 30 Sep 2022 12:04:29 +0000 (UTC)
From: Mostafa Mostafa <mia7ia@yahoo.com>
To: mostafayahia753@gmail.com
Message-ID: <1527240602.2832961.1664539469282@mail.yahoo.com>
Subject: SOC Investigation
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit
References: <1527240602.2832961.1664539469282.ref@mail.yahoo.com>
X-Mailer: WebService/1.1.20702 YMailNodin
Content-Length: 69

Hi Mostafa,

This is to inform you that the course will start soon.
```

* **Detailed Field Breakdown:**
  * **`Date`:** The date and timestamp when the email was sent by the sender's MUA (`Fri, 30 Sep 2022 12:04:29 +0000 (UTC)`). The time zone reflects the MUA's configuration.
  * **`From`:** Displays the sender's display name (`Mostafa Mostafa`) and email address (`<mia7ia@yahoo.com>`). **Security Note:** This field is easily manipulated by attackers to spoof trusted domains.
  * **`Return-Path` *(Found higher up in the full header)*:** Specifies the bounce/error address where undeliverable mail reports are sent (`<mia7ia@yahoo.com>`). It represents the actual sender's mailbox address (`smtp.mailfrom`). **Spoofing Check:** When an email arrives, compare `From:` with `Return-Path:`. A mismatch is a strong indicator of a spoofed email.
  * **`To`:** The recipient's email address(es) (`mostafayahia753@gmail.com`).
  * **`Message-ID`:** A unique string identifier generated by the sending mail server, ending with the sending server's FQDN (`<1527240602.2832961.1664539469282@mail.yahoo.com>`). Analysts use `Message-ID` to track a specific email across enterprise SMTP servers and SEG logs.
  * **`Subject`:** The subject line composed by the sender (`SOC Investigation`).
  * **`MIME-Version`:** **Multipurpose Internet Mail Extensions (MIME)** extends SMTP so users can exchange audio, video, images, and application files over email. Always `1.0` (the only defined standard).
  * **`Content-Type`:** Specifies the media type/format of the content in the message (e.g., `text/plain; charset=UTF-8`, audio, documents).
  * **`Content-Transfer-Encoding`:** Specifies how the MIME message and body are encoded for transit between sender and recipient (`7bit`) so the recipient's client can decode it properly.
  * **`References`:** Derived from the `Message-ID`. In an email thread (e.g., Mostafa emails Omar, and Omar replies), `References` stores the list of *every* `Message-ID` from the original email and all subsequent replies, allowing analysts to track an entire conversation chain.
  * **`Content-Length`:** A non-standard header added by certain providers (like Yahoo) indicating the exact size of the email body in bytes (`69`).

---

### Subsection 3.2: Email X-Headers

**Email X-headers** are custom headers (`X-...`) added by mailbox providers, email clients, or security gateways on top of standard RFC headers (`To`, `From`, `Subject`, `MIME-Version`).

#### Figure 2.5 – Examples of X-Headers Added by the Yahoo Email-Sending Server
```text
[HIGHLIGHTED] X-SONIC-DKIM-SIGN: v=1; a=rsa-sha256; c=relaxed/relaxed; d=yahoo.com; s=s2048; t=1664539473; bh=ofJrvFr25zSMo3B8CdUUTvJys6jnuqF/rq8mLrdGAbS=; h=X-Sonic-MF:Date:From:To:Subject:From:Subject; b=NBmU1UyaJWfDovWmXtGuVFxk1T4v0cyBmL1ct+SMygMfxuP37lCnBn...
[HIGHLIGHTED] X-YMail-OSG: 02HCCH0VM1mihG5MLJQiTFXiFlNk32D5p7Kzas0agmKnAqfFhPWsADicE1LNaIY...
[HIGHLIGHTED] X-Sonic-MF: <mia7ia@yahoo.com>
Received: from sonic.gate.mail.ne1.yahoo.com by sonic303.consmr.mail.ne1.yahoo.com with HTTP; Fri, 30 Sep 2022 12:04:33 +0000
...
[HIGHLIGHTED] X-Mailer: WebService/1.1.20702 YMailNodin
```

* **Analysis of the Custom X-Headers:**
  * **`X-Mailer`:** Identifies the email client used to send the message (`WebService/1.1.20702 YMailNodin`). Mailbox providers use this to detect and block messages sent via suspicious clients, script interpreters, or hacking tools.
  * **`X-YMail-OSG`:** Breaks down into **YMail** (*Yahoo Mail*) + **OSG** (*Outbound Spam Guard*). It holds metadata for Yahoo's outbound spam protection engine.
  * **`X-Sonic-MF`:** Refers to the sending email address (`<mia7ia@yahoo.com>`) and is referenced in the `h=` tag of Yahoo's custom `X-SONIC-DKIM-SIGN` header.
  * **`X-SONIC-DKIM-SIGN`:** Holds a custom DKIM digital signature generated by Yahoo's Sonic mail infrastructure.
  * **`X-Originating-IP` *(Important General X-Header)*:** A widely used X-header that records the **IP address of the client device** that originated the email—critical for tracking the true sender IP and spam filtering.

---

### Subsection 3.3: The Header Added by the Hop Servers (`Received:`)

Tracing the `Received:` headers from **bottom to top** shows every server the email touched and when:

#### 1. First Hop (Sender's MSA Server) — Figure 2.6
```text
Received: from sonic.gate.mail.ne1.yahoo.com by sonic303.consmr.mail.ne1.yahoo.com with HTTP; Fri, 30 Sep 2022 12:04:33 +0000
```
* **Analysis:** The email was received from `sonic.gate.mail.ne1.yahoo.com` by Yahoo's MSA server `sonic303.consmr.mail.ne1.yahoo.com` over the **HTTP** protocol on **9/30/2022 at 12:04:33 PM UTC** (4 seconds after the user clicked send at `12:04:29 UTC`).

#### 2. Second Hop (Recipient's MX Server) — Figure 2.7
```text
Received: from sonic303-21.consmr.mail.ne1.yahoo.com (sonic303-21.consmr.mail.ne1.yahoo.com. [66.163.188.147])
        by mx.google.com with ESMTPS id l184-20020a6770c1000000b0039ad4f386c5si231512vsc.685.2022.09.30.05.04.33
        for <mostafayahia753@gmail.com>
        (version=TLS1_3 cipher=TLS_AES_128_GCM_SHA256 bits=128/128);
        Fri, 30 Sep 2022 05:04:34 -0700 (PDT)
```
* **Analysis:** Yahoo's outbound SMTP server `sonic303-21.consmr.mail.ne1.yahoo.com` (IP **`66.163.188.147`**) transmitted the message to the recipient's MX server (`mx.google.com`) via **ESMTPS** (`TLS1_3`) for `<mostafayahia753@gmail.com>`.
* **Timestamp Normalization:** Logged as `05:04:34 -0700 (PDT)`. Adding 7 hours converts it to **12:04:34 PM UTC** (1 second after the first hop).

#### 3. Third & Final Hop (Recipient's MDA Server) — Figure 2.8
```text
Received: by 2002:a59:a510:0:b0:304:497a:47cb with SMTP id u16csp1808417vqo;
        Fri, 30 Sep 2022 05:04:34 -0700 (PDT)
```
* **Analysis:** Google's internal MDA server (`2002:a59:a510:0:b0:304:497a:47cb`) confirmed final delivery to the mailbox of `mostafayahia753@gmail.com` at `05:04:34 -0700 (PDT)` (**12:04:34 PM UTC**).

---

## 4. Email Authentication Protocols (SPF, DKIM, DMARC)

**Email authentication** verifies that an email genuinely comes from the domain it claims, preventing attackers from spoofing trusted brands to deliver phishing or malware.

### How Email Authentication Works (General 3-Step Process)
Using `Microsoft.com` as an example sender domain:
1. **Define & Publish Rules:** The domain owner (`Microsoft.com`) defines authentication rules/keys for emails sent on its behalf and publishes them as **DNS TXT records**.
2. **Authenticate Incoming Mail:** When a receiving mail server receives an email claiming to be from `Microsoft.com`, it queries `Microsoft.com`'s DNS records and validates the email against those published rules.
3. **Policy Enforcement:** Based on the authentication verdict and published policy, the receiving server delivers the message to the inbox, quarantines it to spam, or drops/rejects it.

---

### Protocol 1: Sender Policy Framework (SPF)
**SPF** allows a domain owner to publish a **DNS TXT record** specifying exactly which IP addresses or hostnames are authorized to send emails on behalf of their domain.

#### Diagram Recreation: Figure 2.9 – SPF Authentication Process
```text
                   +-------------------------------+
                   |   Email Sender Domain DNS     |
                   |         ("SPF" Records)       |
                   +-------------------------------+
                                   ^
                                   | 2. Queries Sender Domain's
                                   |    SPF DNS TXT Record
+--------------+     Email     +---------------+          Matching           +---------------------------+
| Email Sender | ------------> |Receiving Email| --------------------------> |  Deliver to the Recipient |
|   (Client)   |   1. Sends    |    Server     |   3a. Sending IP Matches    |          Mail Box         |
+--------------+               +---------------+       SPF Record            +---------------------------+
                                       |
                                       |           Not Matching              +---------------------------+
                                       +-----------------------------------> |           Block           |
                                           3b. Sending IP Does Not Match     +---------------------------+
```

#### SPF Record Syntax & Qualifiers
```text
v=spf1 ip4:192.168.1.0/24 -all
```
* **`v=spf1`:** Defines SPF version 1.
* **`ip4:192.168.1.0/24`:** Authorizes any IPv4 address in the subnet `192.168.1.0` – `192.168.1.255` to send mail for the domain.
* **The `all` Enforcement Mechanism (How to handle non-matching IPs):**
  * **`-all` (Hard Fail):** Emails failing the SPF check must be **rejected outright**.
  * **`~all` (Soft Fail):** Emails failing the SPF check are accepted but **marked as potential spam**.
  * **`?all` (Neutral):** The domain owner specifies no preference on how failing emails are handled (treated neutrally).
  * **`+all` (Allow All):** Authorizes *any* IP address on the internet to send mail on behalf of the domain (least secure; never recommended).
  * **`-` (Hyphen alone):** Indicates no policy is defined and should be treated as a "neutral" result.

#### Figure 2.10 – SPF Authentication Result (From Our Legitimate Header)
```text
Received-SPF: pass (google.com: domain of mia7ia@yahoo.com designates 66.163.188.147 as permitted sender) client-ip=66.163.188.147;
```
* **Verdict:** `pass` — `google.com` checked `yahoo.com`'s SPF record and confirmed that `66.163.188.147` is an authorized outbound server for `mia7ia@yahoo.com`.

---

### Protocol 2: DomainKeys Identified Mail (DKIM)
**DKIM** provides a cryptographic digital signature (`DKIM-Signature`) added to the email header. It ensures **sender authenticity** and **message integrity** (proving the body and signed headers were not tampered with in transit).

#### Diagram Recreation: Figure 2.11 – DKIM Authentication Process
```text
+--------------+       +----------+       +-------------------+     Signature Verified (✓)     +---------+
|  DKIM Email  | ----> | Internet | ----> |   Receiving Mail  | -----------------------------> |  Inbox  |
|   is sent    |       |  (Hops)  |       |       Server      |                                +---------+
| (Signed with |       +----------+       +-------------------+
| Private Key) |                                 |     ^            Invalid Signature (✗)      +---------+
+--------------+                                 |     |        -----------------------------> |  Spam   |
                                    1. Queries   |     | 2. Returns                            +---------+
                                       DNS       v     |    DKIM Public Key
                                          +-------------------+
                                          |    DNS Server     |
                                          | (Sender's Domain) |
                                          +-------------------+
```

#### Anatomy of the `DKIM-Signature` Header
```text
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=yahoo.com; s=s2048; t=1664539473; 
bh=1Ttd55RGpBC1Cevt3Xgw1XO9lBgWZj04bmslL5Urark=; 
h=Date:From:To:Subject:References:From:Subject:Reply-To; 
b=kRlmdNKBXBZsJLZvTpVqlfojnQL2aqxmliyWmE0bFLOdjgQXhpwAKF4pwYYsaWSDfy...==
```

| Tag | Value in Example | Meaning & Technical Function |
| :--- | :--- | :--- |
| **`v`** | `1` | DKIM version (always `1`). |
| **`a`** | `rsa-sha256` | Cryptographic algorithms used for encryption (`RSA`) and hashing (`SHA256`). |
| **`c`** | `relaxed/relaxed` | **Canonicalization algorithm** (`header/body`) defining how headers and body are standardized before hashing:<br>• **`relaxed/relaxed`:** Allows minor transit modifications (ignores trailing whitespace and non-essential header changes) while preserving core content.<br>• **`simple/simple`:** Only removes trailing whitespace from header fields and allows zero modification to the message body (strictest). |
| **`d`** | `yahoo.com` | The signing domain claiming authorization. The receiving server queries this domain's DNS for the public key. |
| **`s`** | `s2048` | **Selector** value used to construct the DNS TXT lookup query: `s2048._domainkey.yahoo.com`. |
| **`t`** | `1664539473` | Epoch timestamp indicating exactly when the email was signed. |
| **`bh`** | `1Ttd55...=` | **Body Hash:** Base64-encoded hash of the email body after canonicalization (`c`) and hashing (`a`). |
| **`h`** | `Date:From:To:...` | Colon-separated list of specific header fields bound into the digital signature calculation. |
| **`b`** | `kRlmdN...==` | **Digital Signature:** Base64-encoded encrypted hash of the selected headers (`h`), body hash (`bh`), and DKIM parameters, signed with the sender domain's **Private Key**. |

#### Step-by-Step: How the Sending Server Calculates `b` (Signing)
1. **Canonicalize (`c`):** Parses the email headers and body into standardized canonical forms (`relaxed/relaxed` or `simple/simple`).
2. **Hash Headers (`h` & `a`):** Selects the header fields listed in `h=` and hashes them (along with the body hash) using the algorithm in `a=` (`SHA256`).
3. **Sign & Encrypt:** Encrypts the resulting hash using the sender domain's **Private Key** (`RSA`).
4. **Encode (`b`):** Base64-encodes the encrypted signature and places it in the `b=` field.

#### Step-by-Step: How the Receiving Server Verifies DKIM
1. **Verify Body Hash (`bh`):** Hashes the received email body using the algorithm in `a=`, Base64-encodes it, and compares it to `bh=`. If they match, it proceeds to Step 2.
2. **Retrieve Public Key (`d` & `s`):** Performs a DNS TXT lookup using `s` and `d` (e.g., `s2048._domainkey.yahoo.com`) to fetch the sender domain's **Public Key**.
3. **Decrypt Signature (`b`):** Uses the Public Key to decrypt the value in `b=`, revealing the original signed hash of the headers.
4. **Compare Header Hashes:** Computes a fresh hash of the received header fields listed in `h=` (excluding `b=`) and compares it to the decrypted hash from Step 3.
   * **Match:** DKIM signature is valid (`dkim=pass`).
   * **Mismatch:** DKIM signature is invalid (`dkim=fail`), and the message is rejected or flagged as spam.

---

### Protocol 3: Domain-Based Message Authentication, Reporting, and Conformance (DMARC)
**DMARC** is a policy and reporting protocol that sits on top of **SPF and DKIM**. If an email fails SPF, DKIM, or both, DMARC tells the receiving server what action to take (`NONE`, `Quarantine`, or `REJECT`) and where to send violation reports.

#### Diagram Recreation: Figure 2.12 – How a DMARC Policy is Applied
```text
                                +-----------------------+   OR   +-----------------------+
                         +----> | SPF Authorised Sender | -----> |  Valid DKIM Signature | ---------+
                         |      |          (✓)          |        |          (✓)          |          |
                         |      +-----------------------+        +-----------------------+          |
+------------+     +-------------+                                                                  v
| Email sent | --> | Mail Server |                                                             +---------+
+------------+     +-------------+                                          None               |  Inbox  |
                         |                                        +--------------------------> |   (✓)   |
                         |      +-----------------------+   AND  +-----------------------+     +---------+
                         +----> |   SPF Unauthorised    | -----> |     Invalid DKIM      |          ^
                                |      Sender (✗)       |        |     Signature (✗)     |          |
                                +-----------------------+        +-----------------------+          |
                                                                             |                      |
                                                                             v                      |
                                                                   +-------------------+   None     |
                                                                   |   DMARC Policy    | -----------+
                                                                   | (DNS TXT Record)  |
                                                                   +-------------------+
                                                                      |      |       |
                                                                      |      |       | Quarantine  +----------+
                                                                      |      |       +-----------> |   Spam   |
                                                                      |      |                     +----------+
                                                                      |      | Reject              +----------+
                                                                      |      +-------------------> | Dropped  |
                                                                      v                            +----------+
                                                             +-----------------+
                                                             | Reports sent to |
                                                             |  Domain Owner   |
                                                             +-----------------+
```

#### Anatomy of a DMARC DNS TXT Record
```text
"v=DMARC1;p=reject;pct=100;rua=mailto:postmaster@test.com"
```
* **`v`:** DMARC version (`DMARC1`).
* **`p`:** Policy to apply when authentication fails:
  * **`Quarantine`:** Accept the message but route it to the Junk/Spam folder for further investigation.
  * **`REJECT`:** Block/drop the email completely; do not deliver to any folder.
  * **`NONE`:** Take no enforcement action and deliver normally (used to collect visibility reports without impacting mail flow).
* **`pct`:** Percentage (`1` to `100`) of failing messages subjected to the policy in `p=`.
  * *Fallback Rule:* If `p=reject;pct=50`, **50%** of failing emails are rejected, and the remaining **50%** fall back to the next lower policy in the sequence (**`Quarantine`**).
* **`rua`:** Specifies the mailbox URI (`mailto:postmaster@test.com`) that receives aggregate DMARC XML reports of authentication failures/violations.

#### Figure 2.13 – Email Authentication Result (From Our Legitimate Header)
```text
Authentication-Results: mx.google.com;
       dkim=pass header.i=@yahoo.com header.s=s2048 header.b=kRlmdNKB;
       spf=pass (google.com: domain of mia7ia@yahoo.com designates 66.163.188.147 as permitted sender) smtp.mailfrom=mia7ia@yahoo.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=yahoo.com
```
* **Analysis:** The email passed **DKIM** (`dkim=pass`), **SPF** (`spf=pass`), and **DMARC** (`dmarc=pass`), confirming 100% that the message was legitimately sent by `mia7ia@yahoo.com` and was not spoofed.

---

## 5. Investigating the Email Header of a Spoofed Message

In Chapter 1, we examined a suspicious email purporting to be from **`"FedEx Express" <replyfedex@fedex.com>`** with a malicious `.rar` attachment (`NMXCBIDFJHSDHK754.rar`). Two hypotheses existed:
1. **Compromised Account:** A legitimate `fedex.com` mailbox was compromised by an attacker.
2. **Domain Spoofing:** An external attacker spoofed the `fedex.com` domain from an unauthorized server.

To test these hypotheses, we extract and analyze the email's header (from bottom to top):

#### Figure 2.14 – Spoofing Email Authentication Result
```text
Authentication-Results: mx.google.com;
       spf=fail smtp.mailfrom=replyfedex@fedex.com;
       dmarc=fail header.from=fedex.com
Received: from mail.footballticketnet.com (mailserver.footballticketnet.com [95.211.214.81])
        by mx.google.com with ESMTPS id 3jgssdsqx7-1
        (version=TLSv1.2 cipher=ECDHE-RSA-AES256-GCM-SHA384 bits=256 verify=NO)
        for <mostafayahia753@gmail.com>; Mon, 12 Sep 2022 03:39:09 -0400
Received: from [45.147.230.116] (unknown [45.147.230.116])
        by mail.footballticketnet.com (Postfix) with ESMTPSA id B727E850130
        for <mostafayahia753@gmail.com>; Mon, 12 Sep 2022 05:30:04 +0000 (UTC)
Content-Type: multipart/mixed; boundary="===============0929829974=="
To: mostafayahia753@gmail.com
From: "FedEx Express" <replyfedex@fedex.com>
Date: Sun, 11 Sep 2022 22:30:04 -0700
Message-ID: <3jgssdsqx7-1@m0045517.ppops.net>
```

### Step-by-Step Forensic Walkthrough (Bottom-to-Top)

| Step | Header Section Inspected | Forensic Finding |
| :--- | :--- | :--- |
| **1. Metadata Check** | `From: "FedEx Express" <replyfedex@fedex.com>`<br>`To: mostafayahia753@gmail.com` | The sender claims to be from the `fedex.com` domain. |
| **2. First Hop (Origin)** | `Received: from [45.147.230.116] ... by mail.footballticketnet.com (Postfix)` | The email originated from an unknown host `[45.147.230.116]` and was submitted to a Postfix server named `mail.footballticketnet.com`. |
| **3. Second Hop (Last Sender Hop)** | `Received: from mail.footballticketnet.com (mailserver.footballticketnet.com [95.211.214.81]) by mx.google.com` | `mailserver.footballticketnet.com` (IP **`95.211.214.81`**) relayed the message to Google's MX server (`mx.google.com`). **Note:** In your organization's SMTP or SEG logs, `95.211.214.81` will appear as the Sender SMTP Server IP. |
| **4. Authentication Verification** | `Authentication-Results: mx.google.com;` | • **`spf=fail`:** `95.211.214.81` is **not** in `fedex.com`'s SPF record.<br>• **No DKIM Signature:** The attacker did not include a `DKIM-Signature` header.<br>• **`dmarc=fail`:** Because SPF failed and DKIM is missing, DMARC validation failed. |

* **Final Verdict:** Hypothesis 2 is proven. An attacker used an unauthorized external mail server (`mailserver.footballticketnet.com` / `95.211.214.81`) to **spoof** the `fedex.com` domain.

---

## 6. Quick-Reference Summary Cheat Sheet for SOC Analysts

* **Hops Order:** `MUA (Client)` -> `MSA (Submission)` -> `MTA (Relay)` -> `MX (Recipient Gateway)` -> `MDA (Mailbox Delivery)` -> `MUA (Recipient Client)`.
* **Reading Direction:** Always read headers **Bottom-to-Top**.
* **Key Spoofing Indicators in Headers:**
  1. `From:` address does not match `Return-Path:` (`smtp.mailfrom`).
  2. Last external hop in `Received:` (`from <server> [<IP>] by <your_mx>`) does not belong to the sender domain's authorized servers.
  3. `spf=fail` or `spf=softfail` in `Authentication-Results`.
  4. Missing `DKIM-Signature` or `dkim=fail`.
  5. `dmarc=fail` in `Authentication-Results`.
