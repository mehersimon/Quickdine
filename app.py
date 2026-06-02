import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import init_db, get_db, Restaurant, MenuItem, Order
from routers.api import router
from ws_manager import manager
from auth import get_current_manager

import qrcode
import io, base64

app = FastAPI(title="QuickDine", version="1.0.0")

# ── Init DB on startup ──────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()

# ── Static files ────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── API routes ──────────────────────────────────────────────────────────────
app.include_router(router)

# ── Page routes ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard/menu", response_class=HTMLResponse)
async def menu_page(request: Request):
    return templates.TemplateResponse("menu_manage.html", {"request": request})


@app.get("/dashboard/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})


@app.get("/dashboard/qr", response_class=HTMLResponse)
async def qr_page(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})


@app.get("/menu/{restaurant_id}", response_class=HTMLResponse)
async def customer_menu(request: Request, restaurant_id: str):
    return templates.TemplateResponse("customer_menu.html", {"request": request, "restaurant_id": restaurant_id})


# ── QR code generation endpoint ──────────────────────────────────────────────

@app.get("/api/qr/generate/{restaurant_id}")
def generate_qr(restaurant_id: str):
    """Returns a PNG QR code for the restaurant menu URL."""
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    url = f"{base_url}/menu/{restaurant_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="quickdine_qr_{restaurant_id}.png"'})


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/orders/{restaurant_id}")
async def ws_orders(websocket: WebSocket, restaurant_id: str):
    await manager.connect(restaurant_id, websocket)
    try:
        while True:
            await websocket.receive_text()   # keep alive / ping pong
    except WebSocketDisconnect:
        manager.disconnect(restaurant_id, websocket)
