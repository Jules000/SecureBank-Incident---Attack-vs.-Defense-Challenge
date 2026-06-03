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

### 5. Run the app (development)

```bash
python3 app.py
```

Access at `http://<ubuntu-ip>:5000`

### 6. Run with Gunicorn (production-style for lab)

```bash
pip3 install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### 7. (Optional) Run as a systemd service

```ini
# /etc/systemd/system/securebank.service
[Unit]
Description=SecureBank Flask App
After=network.target

[Service]
WorkingDirectory=/var/www/bank
ExecStart=/usr/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now securebank
```

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
