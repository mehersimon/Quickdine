import os, uuid, shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from models import get_db, Restaurant, MenuItem, Order
from auth import hash_password, verify_password, create_token, get_current_manager, gen_restaurant_id
from ws_manager import manager

router = APIRouter()

UPLOAD_DIR = "static/uploads"
os.makedirs(f"{UPLOAD_DIR}/logos", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/food",  exist_ok=True)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    restaurant_name: str
    owner_name: str
    email: str
    password: str
    phone: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(Restaurant).filter(Restaurant.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    rid = gen_restaurant_id()
    resto = Restaurant(
        id=rid,
        restaurant_name=req.restaurant_name,
        owner_name=req.owner_name,
        email=req.email,
        password_hash=hash_password(req.password),
        phone=req.phone or "",
    )
    db.add(resto); db.commit()
    token = create_token({"sub": rid})
    return {"token": token, "restaurant_id": rid, "restaurant_name": req.restaurant_name}


@router.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    resto = db.query(Restaurant).filter(Restaurant.email == req.email).first()
    if not resto or not verify_password(req.password, resto.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_token({"sub": resto.id})
    return {"token": token, "restaurant_id": resto.id, "restaurant_name": resto.restaurant_name}


@router.get("/api/auth/me")
def me(manager_: Restaurant = Depends(get_current_manager)):
    return {
        "id": manager_.id,
        "restaurant_name": manager_.restaurant_name,
        "owner_name": manager_.owner_name,
        "email": manager_.email,
        "phone": manager_.phone,
        "logo_url": manager_.logo_url,
    }

# ─────────────────────────────────────────
# RESTAURANT PROFILE
# ─────────────────────────────────────────

@router.post("/api/restaurant/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current: Restaurant = Depends(get_current_manager),
    db: Session = Depends(get_db),
):
    ext  = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png","jpg","jpeg","gif","webp"}:
        raise HTTPException(400, "Invalid image type")
    fname = f"{current.id}_logo.{ext}"
    path  = f"{UPLOAD_DIR}/logos/{fname}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    url = f"/static/uploads/logos/{fname}"
    db.query(Restaurant).filter(Restaurant.id == current.id).update({"logo_url": url})
    db.commit()
    return {"logo_url": url}

# ─────────────────────────────────────────
# MENU ITEMS
# ─────────────────────────────────────────

@router.get("/api/menu/{restaurant_id}")
def get_menu(restaurant_id: str, db: Session = Depends(get_db)):
    resto = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not resto:
        raise HTTPException(404, "Restaurant not found")
    items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    ).all()
    return {
        "restaurant": {"name": resto.restaurant_name, "logo_url": resto.logo_url},
        "items": [
            {"id": i.id, "name": i.name, "description": i.description,
             "image_url": i.image_url, "category": i.category, "price": i.price}
            for i in items
        ]
    }


@router.get("/api/dashboard/menu")
def list_menu(current: Restaurant = Depends(get_current_manager), db: Session = Depends(get_db)):
    items = db.query(MenuItem).filter(MenuItem.restaurant_id == current.id).all()
    return [
        {"id": i.id, "name": i.name, "description": i.description,
         "image_url": i.image_url, "category": i.category,
         "price": i.price, "is_available": i.is_available}
        for i in items
    ]


@router.post("/api/dashboard/menu")
async def add_item(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("General"),
    price: float = Form(...),
    file: Optional[UploadFile] = File(None),
    current: Restaurant = Depends(get_current_manager),
    db: Session = Depends(get_db),
):
    image_url = ""
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"png","jpg","jpeg","gif","webp"}:
            raise HTTPException(400, "Invalid image type")
        fname = f"{uuid.uuid4().hex}.{ext}"
        path  = f"{UPLOAD_DIR}/food/{fname}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/static/uploads/food/{fname}"
    item = MenuItem(
        restaurant_id=current.id, name=name, description=description,
        category=category, price=price, image_url=image_url
    )
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "name": item.name, "price": item.price, "is_available": item.is_available}


@router.put("/api/dashboard/menu/{item_id}")
async def update_item(
    item_id: int,
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("General"),
    price: float = Form(...),
    is_available: str = Form("true"),
    file: Optional[UploadFile] = File(None),
    current: Restaurant = Depends(get_current_manager),
    db: Session = Depends(get_db),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    item.name = name; item.description = description
    item.category = category; item.price = price
    item.is_available = is_available.lower() == "true"
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"png","jpg","jpeg","gif","webp"}:
            raise HTTPException(400, "Invalid image type")
        fname = f"{uuid.uuid4().hex}.{ext}"
        path  = f"{UPLOAD_DIR}/food/{fname}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        item.image_url = f"/static/uploads/food/{fname}"
    db.commit()
    return {"ok": True}


@router.delete("/api/dashboard/menu/{item_id}")
def delete_item(item_id: int, current: Restaurant = Depends(get_current_manager), db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item); db.commit()
    return {"ok": True}


@router.patch("/api/dashboard/menu/{item_id}/toggle")
def toggle_item(item_id: int, current: Restaurant = Depends(get_current_manager), db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    item.is_available = not item.is_available
    db.commit()
    return {"is_available": item.is_available}

# ─────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────

class PlaceOrderRequest(BaseModel):
    restaurant_id: str
    customer_name: str
    table_number: Optional[str] = ""
    items: List[int]  # list of menu item IDs


@router.post("/api/orders")
async def place_order(req: PlaceOrderRequest, db: Session = Depends(get_db)):
    if not req.customer_name.strip():
        raise HTTPException(400, "Customer name required")
    if not req.items:
        raise HTTPException(400, "Select at least one item")

    menu_items = db.query(MenuItem).filter(
        MenuItem.id.in_(req.items),
        MenuItem.restaurant_id == req.restaurant_id,
        MenuItem.is_available == True,
    ).all()
    if not menu_items:
        raise HTTPException(400, "No valid items found")

    item_map   = {i.id: i for i in menu_items}
    ordered    = [{"id": mid, "name": item_map[mid].name, "price": item_map[mid].price}
                  for mid in req.items if mid in item_map]
    total      = sum(i["price"] for i in ordered)

    order = Order(
        restaurant_id=req.restaurant_id,
        customer_name=req.customer_name.strip(),
        table_number=req.table_number or "",
        ordered_items=ordered,
        total_amount=total,
    )
    db.add(order); db.commit(); db.refresh(order)

    payload = {
        "type": "new_order",
        "order": {
            "id": order.id,
            "customer_name": order.customer_name,
            "table_number": order.table_number,
            "ordered_items": order.ordered_items,
            "total_amount": order.total_amount,
            "status": order.status,
            "timestamp": order.timestamp.isoformat(),
        }
    }
    await manager.broadcast(req.restaurant_id, payload)
    return {"ok": True, "order_id": order.id}


@router.get("/api/dashboard/orders")
def list_orders(current: Restaurant = Depends(get_current_manager), db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    orders = db.query(Order).filter(Order.restaurant_id == current.id).order_by(Order.timestamp.desc()).limit(100).all()
    return [
        {"id": o.id, "customer_name": o.customer_name, "table_number": o.table_number,
         "ordered_items": o.ordered_items, "total_amount": o.total_amount,
         "status": o.status, "timestamp": o.timestamp.isoformat()}
        for o in orders
    ]


@router.get("/api/dashboard/stats")
def stats(current: Restaurant = Depends(get_current_manager), db: Session = Depends(get_db)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = db.query(Order).filter(
        Order.restaurant_id == current.id,
        Order.timestamp >= today_start,
    ).all()
    pending  = sum(1 for o in today_orders if o.status == "Pending")
    revenue  = sum(o.total_amount for o in today_orders)
    total_items = db.query(MenuItem).filter(MenuItem.restaurant_id == current.id).count()
    return {
        "orders_today": len(today_orders),
        "pending": pending,
        "revenue": revenue,
        "total_items": total_items,
    }


@router.patch("/api/dashboard/orders/{order_id}/status")
async def update_status(
    order_id: int,
    body: dict,
    current: Restaurant = Depends(get_current_manager),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == current.id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    valid = ["Pending", "Preparing", "Ready", "Served"]
    new_status = body.get("status")
    if new_status not in valid:
        raise HTTPException(400, "Invalid status")
    order.status = new_status
    db.commit()
    await manager.broadcast(current.id, {"type": "status_update", "order_id": order_id, "status": new_status})
    return {"ok": True}

# ─────────────────────────────────────────
# QR CODE
# ─────────────────────────────────────────

@router.get("/api/dashboard/qr")
def get_qr_info(current: Restaurant = Depends(get_current_manager)):
    menu_url = f"{BASE_URL}/menu/{current.id}"
    return {
        "restaurant_id": current.id,
        "restaurant_name": current.restaurant_name,
        "logo_url": current.logo_url,
        "menu_url": menu_url,
    }
