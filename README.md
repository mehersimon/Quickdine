# QuickDine 🍽️

A production-ready QR-based restaurant ordering SaaS platform.

## Features

- 🔒 JWT Authentication for restaurant managers
- 📱 Mobile-first customer menu (no app download needed)
- ⚡ Real-time kitchen orders via WebSockets
- 📋 Full menu management (CRUD, images, categories, availability)
- 📱 Permanent QR code per restaurant
- 🖨️ QR download, print, share
- 🪑 Optional table-specific QR links (`?table=N`)
- 🌑 Dark, glassmorphism UI

## Quick Start

```bash
# 1. Clone / unzip project
cd quickdine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
uvicorn app:app --reload

# 4. Open http://localhost:8000
```

## Project Structure

```
quickdine/
├── app.py              # FastAPI entry point
├── models.py           # SQLAlchemy models + DB setup
├── auth.py             # JWT + password utilities
├── ws_manager.py       # WebSocket connection manager
├── routers/
│   └── api.py          # All REST API routes
├── templates/          # Jinja2 HTML pages
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── menu_manage.html
│   ├── orders.html
│   ├── qr.html
│   ├── customer_menu.html
│   └── partials/sidebar.html
├── static/
│   ├── css/
│   │   ├── main.css
│   │   ├── auth.css
│   │   ├── dashboard.css
│   │   ├── orders.css
│   │   └── customer.css
│   ├── js/
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   ├── menu.js
│   │   └── orders.js
│   └── uploads/        # Food + logo images
└── requirements.txt
```

## Routes

| Route | Description |
|---|---|
| `/` | Landing page |
| `/login` | Manager login |
| `/register` | Manager registration |
| `/dashboard` | Stats overview |
| `/dashboard/menu` | Menu management |
| `/dashboard/orders` | Live kitchen dashboard |
| `/dashboard/qr` | QR code page |
| `/menu/{restaurant_id}` | Customer-facing menu |
| `/menu/{restaurant_id}?table=N` | Table-specific menu |

## Environment Variables

Create a `.env` file to override defaults:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./quickdine.db
BASE_URL=https://yourdomain.com
```

## Production Deployment

1. Set `DATABASE_URL` to a PostgreSQL URL
2. Set `SECRET_KEY` to a long random string
3. Set `BASE_URL` to your domain
4. Use a reverse proxy (nginx) in front of uvicorn
5. Configure persistent storage for `static/uploads/`

## Tech Stack

- **Backend**: Python 3, FastAPI, SQLAlchemy, JWT
- **Frontend**: HTML5, CSS3, Vanilla JS (no framework)
- **DB**: SQLite (dev) / PostgreSQL (prod)
- **Real-time**: WebSockets
- **QR**: qrcode[pil]
