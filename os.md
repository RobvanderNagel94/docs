---
layout: default
title: Os
---
## Commands
- [1. System Info](#1-system-info)
- [2. File and Directory Management](#2-file-and-directory-management)
- [3. Search](#3-search)
- [4. Permissions](#4-permissions)
- [5. Process Management](#5-process-management)
- [6. Package Management Ubuntu/Debian](#6-package-management-ubuntudebian)
- [7. Networking](#7-networking)
- [8. Disk Usage](#8-disk-usage)
- [9. Scheduling](#9-scheduling)
- [10. Archive & Compression](#10-archive--compression)
- [11. Users and Groups](#11-users-and-groups)
- [12. Dev Tools](#12-dev-tools)
- [13. Miscellaneous](#13-miscellaneous)

---

### 1. System Info
```bash
uname -a         # Show kernel and architecture info
hostname         # Show hostname
uptime           # Show system uptime
top              # Real-time system processes
htop             # Interactive process viewer (if installed)
vmstat           # Memory, CPU, I/O stats
free -h          # Show memory usage
who              # Show who is logged in
id               # Show current user ID and group info
```

### 2. File and Directory Management
```bash
ls -l            # List files (long format)
ls -a            # Show hidden files
pwd              # Show current directory
cd <dir>         # Change directory
mkdir <dir>      # Create new directory
rmdir <dir>      # Delete empty directory
rm -r <dir>      # Delete directory and contents
touch <file>     # Create empty file
cp <src> <dest>  # Copy file or dir
mv <src> <dest>  # Move or rename
rm <file>        # Delete file
tree             # Display directory tree (if installed)
cat <file>       # View file contents
less <file>      # View file (scrollable)
more <file>      # View file (older pager)
head <file>      # First 10 lines
tail <file>      # Last 10 lines
tail -f <file>   # Live tail (useful for logs)
nano <file>      # Terminal text editor
vim <file>       # Vi improved
```

### 3. Search
```bash
find <dir> -name "<pattern>"     # Find files by name
grep "pattern" <file>            # Search text in file
grep -r "pattern" <dir>          # Recursive grep
locate <file>                    # Fast file search (needs `updatedb`)
which <command>                  # Show path of command
whereis <command>                # Locate binary, source, and man page
```

### 4. Permissions
```bash
chmod +x <file>         # Make script executable
chmod 755 <file>        # rwxr-xr-x (owner: all, group/others: read+execute)
chmod 644 <file>        # rw-r--r-- (owner: read+write, group/others: read)
chmod 700 <file>        # rwx------ (owner only)
chmod 600 <file>        # rw------- (owner only, no execute)
chmod -R 755 <dir>      # Recursively set permissions
chmod u+x <file>        # Add execute for user (owner)
chmod g-w <file>        # Remove write for group
chmod o+r <file>        # Add read for others
chmod a-x <file>        # Remove execute for all
chown user:group <file> # Change ownership
ls -l                   # View permissions
umask                   # Default permission mask
```

### 5. Process Management
```bash
ps aux             # Show running processes
top / htop         # Real-time process monitor
kill <pid>         # Kill process
kill -9 <pid>      # Force kill
pkill <name>       # Kill by name
xargs              # Pass input to commands
jobs               # Show background jobs
fg / bg            # Resume jobs in foreground/background
```

### 6. Package Management Ubuntu/Debian
```bash
sudo apt update
sudo apt upgrade
sudo apt install <pkg>
sudo apt remove <pkg>
dpkg -i <pkg>.deb
```

### 7. Networking
```bash
ip a               # Show IP addresses
ifconfig           # Show network info (older)
ping <host>        # Ping a host
traceroute <host>  # Trace network path
nslookup <host>    # DNS lookup
dig <host>         # Advanced DNS lookup
curl <url>         # HTTP requests
wget <url>         # Download files
netstat -tuln      # Listening ports (older)
ss -tuln           # Listening ports (modern)
telnet <host> <port> # Check open ports
```

#### Example curl

```bash
# Get curl
curl http://localhost:8000/
# GET with header
curl -H "Accept: application/json" \
     -H "X-Custom-Header: value123" \
     http://localhost:8000/data
# GET with Bearer Token
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     http://localhost:8000/secure-endpoint
# POST
curl -X POST http://localhost:8000/submit
# POST with param
curl -X POST "http://localhost:8000/produce?message=HelloKafka"
# POST with Json
curl -X POST http://localhost:8000/api/data \
     -H "Content-Type: application/json" \
     -d '{"key1": "value1", "key2": "value2"}'
# POST with Bearer and Json
curl -X POST http://localhost:8000/api/protected \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"message": "Secure POST"}'
```

### 8. Disk Usage
```bash
df -h             # Show mounted disks
du -sh <dir>      # Show disk usage of dir
mount             # Show mounted filesystems
umount <device>   # Unmount device
lsblk             # List block devices
```

### 9. Scheduling
```bash
crontab -e             # Edit cron jobs
crontab -l             # List cron jobs
at <time>              # Schedule one-time job
30 2 * * * /home/user/backup.sh # backup every day at 2:30 AM
```

### 10. Archive & Compression
```bash
tar -czf file.tar.gz <dir>    # Create gzip archive
tar -xzf file.tar.gz          # Extract archive
zip -r file.zip <dir>         # Create zip
unzip file.zip                # Extract zip
gzip <file>                   # Compress file
gunzip <file.gz>              # Decompress
```

### 11. Users and Groups
```bash
adduser <name>       # Add user
passwd <user>        # Change password
deluser <name>       # Remove user
groupadd <group>     # Add group
usermod -aG <group> <user>  # Add user to group
```

### 12. Dev Tools
```bash
man <command>        # Manual page
alias ll='ls -alF'   # Create aliases
history              # Show command history
env                  # Show environment vars
export VAR=value     # Set env variable
echo $VAR            # Use env variable
```

### 13. Miscellaneous
```bash
# Create and zip search results for "docker"
grep -r "docker" . > docker_search_results.txt && zip docker_search_results.zip docker_search_results.txt

# Find and replace "localhost:3000" with "api.myapp.dev" across files
grep -rl "localhost:3000" . | xargs sed -i '' 's/localhost:3000/api.myapp.dev/g'

# List JSON files containing a specific key/value
find . -name "*.json" | xargs grep -l '"status": "error"'

# Count most common words in Markdown files
cat *.md | tr -cs '[:alpha:]' '[\n*]' | sort | uniq -c | sort -nr | head -20

# Extract active status entries from JSON using jq
cat response.json | jq '.data[] | select(.status=="active") | {id, name}'

# Download a ZIP and extract it
curl -L -o archive.zip "https://example.com/archive.zip" && unzip archive.zip -d extracted

# List all symbolic links and their targets
find . -type l -exec ls -l {} \;

# Show Docker containers using >100MB RAM
docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" | awk -F '[ /]+' '$2+0 > 100 { print $1, $2$3 }'

# cURL JSON API → filter → grep important
curl -s https://api.example.com/data | jq -r '.[] | .name' | grep "important"

# Summarize Python files by line count
find . -name "*.py" | xargs wc -l | sort -nr | tee python_file_line_counts.txt
```
