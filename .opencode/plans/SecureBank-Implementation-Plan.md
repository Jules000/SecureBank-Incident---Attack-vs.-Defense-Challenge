# SecureBank Flask App — Implementation Plan

## Folder Structure

```
F:\BankingApp\
├── app.py                        # Flask application (vulnerable)
├── setup_db.py                   # Database initializer (SHA256 hashes)
├── requirements.txt              # Python dependencies
├── package.json                  # Tailwind CLI dev dependency
├── tailwind.config.js            # Tailwind content paths
├── database\                     # Created at runtime
│   └── db.sqlite
├── static\
│   ├── css\
│   │   ├── input.css             # Tailwind directives + @font-face import
│   │   └── tailwind.css          # Compiled output (generated via CLI)
│   ├── fonts\inter\              # Downloaded Inter variable woff2 files
│   │   ├── Inter-Variable.woff2
│   │   └── fonts.css
│   └── images\
│       ├── hero-dashboard.png    # Google CDN image (downloaded)
│       └── founder-collab.png    # Google CDN image (downloaded)
└── templates\
    ├── index.html                # Landing page (copied & modified)
    ├── login.html                # Login page (copied & modified)
    └── dashboard.html            # Dashboard (copied & modified)
```

## Cross-Platform DB Path

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "db.sqlite")
```

## Database Schema (`setup_db.py`)

**Table: `users`**
| Column | Type |
|---|---|
| id | INTEGER PRIMARY KEY AUTOINCREMENT |
| username | TEXT UNIQUE NOT NULL |
| password | TEXT NOT NULL (SHA256 hash) |
| name | TEXT NOT NULL |
| balance | REAL NOT NULL |

**Seed Data (7 users)**
| username | password (plain) | name | balance |
|---|---|---|---|
| alice | rockyou | Alice Johnson | 5500.00 |
| bob | password123 | Bob Smith | 12300.00 |
| charlie | iloveyou | Charlie Brown | 8700.00 |
| diana | letmein | Diana Prince | 22150.00 |
| edward | 12345678 | Edward Norton | 3120.00 |
| frank | admin123 | Frank Castle | 9750.00 |
| grace | welcome | Grace Hopper | 6400.00 |

## App Routes (`app.py`)

| Route | Methods | Behavior |
|---|---|---|
| `/` | GET | `render_template("index.html")` |
| `/login` | GET | `render_template("login.html")` |
| `/login` | POST | SQLi via f-string, SHA256 input, query. On exception → raw error. On match → session. |
| `/dashboard` | GET | Session guard. Compute initials. Render template. |
| `/logout` | GET | `session.clear()` → redirect `/` |

## Vulnerabilities

1. SQL Injection — f-string in login query
2. Verbose Errors — raw SQLite exception displayed
3. Weak Session Key — `"bank_secret"` hardcoded
4. Unsalted SHA256 — crackable with HashCat

## HTML Template Changes

| Change | index | login | dashboard |
|---|---|---|---|
| Remove CDN scripts | ✅ | ✅ | ✅ |
| Add local CSS link | ✅ | ✅ | ✅ |
| Local image paths | ✅ (2) | — | — |
| Keep `{{ error }}` | — | ✅ | — |
| Add `{{ user_name }}` | — | — | ✅ |
| Add `{{ user_initials }}` | — | — | ✅ |
| Add `{{ balance }}` | — | — | ✅ |

## Build Steps

1. `npm install`
2. `npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify`
3. `python setup_db.py`
4. `python app.py`
