
# Linux Commands Cheat Sheet

## Navigation

### pwd
```bash
pwd
```

### cd
```bash
cd /path/to/dir
cd ..
cd ~
```

### ls
```bash
ls
ls -l
ls -a
ls -lh
ls -R
```

---

# File Operations

### touch
```bash
touch file.txt
```

### cp
```bash
cp source.txt destination.txt
cp -r dir1 dir2
```

### mv
```bash
mv file1 file2
mv file.txt /path/
```

### rm
```bash
rm file.txt
rm -r directory
rm -rf directory
```

### mkdir
```bash
mkdir newdir
mkdir -p parent/child
```

### rmdir
```bash
rmdir dirname
```

---

# File Viewing

### cat
```bash
cat file.txt
```

### less
```bash
less file.txt
```

### head
```bash
head file.txt
head -n 20 file.txt
```

### tail
```bash
tail file.txt
tail -f logfile.log
```

---

# Search & Text

### grep
```bash
grep "text" file.txt
grep -r "text" directory
```

### find
```bash
find /path -name file.txt
find /path -type f
```

### sort
```bash
sort file.txt
```

### wc
```bash
wc file.txt
wc -l file.txt
```

---

# System Information

### whoami
```bash
whoami
```

### hostname
```bash
hostname
```

### uname
```bash
uname
uname -a
```

### date
```bash
date
```

### uptime
```bash
uptime
```

---

# Disk Usage

### df
```bash
df
df -h
```

### du
```bash
du -sh *
```

---

# Process Monitoring

### ps
```bash
ps
ps aux
```

### top
```bash
top
```

---

# Network

### ip
```bash
ip address
ip a
```

### ping
```bash
ping google.com
```

### ss
```bash
ss -tulnp
```

### netstat
```bash
netstat -ntlp
```

---

# Terminal Utilities

### clear
```bash
clear
```

### history
```bash
history
```

### man
```bash
man ls
```

### echo
```bash
echo "hello"
```

### exit
```bash
exit
```
