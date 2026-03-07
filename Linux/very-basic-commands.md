# 🐧 Master Linux Commands For Beginners: The Ultimate Handbook

This guide is a collection of the most essential Linux commands, organized by their real-world usage. Whether you are navigating the file system, managing permissions, or monitoring system health, these commands are your daily tools.

---

## 🗂️ 1. Navigation Commands

*The foundation of moving around the Linux file system.*

| Command | Description | Example |
| --- | --- | --- |
| **`pwd`** | **P**rint **W**orking **D**irectory — shows where you are. | `pwd` |
| **`ls`** | **L**i**s**t directory contents. | `ls -la` (Long list + hidden files) |
| **`cd`** | **C**hange **D**irectory. | `cd /var/log` |
| **`cd ..`** | Move **UP** one level in the directory tree. | `cd ..` |
| **`cd ~`** | Jump directly to your **Home** directory. | `cd ~` |
| **`cd -`** | Switch back to the **previous** directory. | `cd -` |
| **`clear`** | Clear the terminal screen. | `clear` |

---

## 📄 2. File & Directory Management

*Creating, copying, and deleting data.*

* **`mkdir`**: Create a new directory.
* `mkdir projects`


* **`touch`**: Create an empty file or update timestamps.
* `touch notes.txt`


* **`cp`**: Copy files or directories.
* `cp file.txt backup.txt`
* `cp -r folder/ backup_folder/` (Recursive copy for folders)


* **`mv`**: Move or rename files.
* `mv old_name.txt new_name.txt`


* **`rm`**: Remove files or directories.
* `rm file.txt`
* `rm -rf folder/` (Force remove directory — **Use with caution!**)


* **`ln`**: Create a link (shortcut) between files.
* `ln -s source_file link_name` (Symbolic link)



---

## 🔍 3. Text Processing & Searching

*Finding information within files and directories.*

* **`cat`**: Display file contents or concatenate files.
* **`grep`**: Search for a specific pattern/text inside files.
* `grep "error" syslog.log`


* **`find`**: Search for files and directories based on criteria.
* `find /home -name "*.pdf"`


* **`head` / `tail**`: View the beginning or end of a file.
* `tail -f /var/log/auth.log` (Watch live updates)


* **`sed` / `awk**`: Powerful stream editors for text manipulation and reporting.
* **`diff`**: Compare two files for differences.

---

## 🛡️ 4. Permissions & Ownership

*Managing security and user access.*

* **`chmod`**: Change file permissions (Read, Write, Execute).
* `chmod 755 script.sh`


* **`chown`**: Change the owner and group of a file.
* `sudo chown user:group file.txt`


* **`sudo`**: Execute a command with administrative (root) privileges.
* **`whoami`**: Display the current logged-in username.

---

## ⚙️ 5. System Information & Monitoring

*Checking the health and status of your Linux machine.*

| Command | Action |
| --- | --- |
| **`top`** | Real-time monitor of system processes and CPU/RAM usage. |
| **`ps aux`** | List all currently running processes. |
| **`df -h`** | Check **D**isk **F**ree space in human-readable format. |
| **`du -sh`** | Check **D**isk **U**sage of a specific file or folder. |
| **`free -m`** | Display amount of free and used memory (RAM). |
| **`uname -a`** | Show system kernel information and OS details. |
| **`uptime`** | Show how long the system has been running. |
| **`history`** | List previously executed commands. |

---

## 🌐 6. Networking & Remote Access

*Connecting to the outside world.*

* **`ping`**: Test network connectivity to a host.
* **`ssh`**: Securely log into remote systems.
* `ssh username@remote_ip`


* **`scp`**: Securely copy files between systems over a network.
* **`curl` / `wget**`: Download files or interact with web servers/APIs.
* **`ip addr`**: Display IP addresses and network interface details.

---

## 📦 7. Archiving & Compression

*Bundling and shrinking files.*

* **`tar`**: Create or extract tape archives (e.g., `.tar`, `.tar.gz`).
* `tar -czvf archive.tar.gz folder/` (Compress)
* `tar -xzvf archive.tar.gz` (Extract)


* **`zip` / `unzip**`: Manage standard zip archives.

---

## 🛠️ 8. Productive Shortcuts

* **`Tab`**: Auto-complete command or file names.
* **`Ctrl + C`**: Stop the current running command.
* **`Ctrl + R`**: Search through your command history.
* **`man <command>`**: Open the manual for any command (e.g., `man grep`).
* **`|` (Pipe)**: Pass the output of one command as input to another.
* `ls -l | grep ".txt"`



---

*Reference: Based on the [LinuxTeck Beginners Guide](https://www.linuxteck.com/linux-commands-for-beginners/).*
