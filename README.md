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
