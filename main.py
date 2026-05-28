from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import hashlib
import os
import random
from urllib.parse import parse_qs, urlparse

import db
from db import (
    Product, Coupon, User, UserSession, Order, OrderItem, SessionLocal
)

app = FastAPI(title="NovaShop API", version="2.0")

# --- Configuração de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# --- Constantes ---
FREE_SHIPPING_MIN = 199
ACCESS_TOKEN_TTL = 15 * 60  # 15 minutos
REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60  # 7 dias

# --- Dados em Memória (produtos, cupons, etc.) ---
PRODUCTS_DATA = [
    {
        "id": 1,
        "name": "Fone Bluetooth TWS Pro",
        "description": "Som hi-fi, cancelamento de ruído ativo, 30h de bateria com estojo carregador.",
        "price": 79.90,
        "original_price": 199.90,
        "category": "Eletrônicos",
        "emoji": "🎧",
        "sold": 1247,
        "rating": 4.7,
        "reviews": 312,
        "stock": 45,
        "tags": ["frete gratis", "mais vendido"],
    },
    # ... (adicione todos os produtos aqui ou carregue do DB)
]

COUPONS_DATA = {
    "NOVA10": {"discount": 10, "type": "percent", "min_value": 50, "label": "10% OFF"},
    "NOVA20": {"discount": 20, "type": "percent", "min_value": 100, "label": "20% OFF"},
    "FRETE5": {"discount": 5, "type": "fixed", "min_value": 30, "label": "R$ 5 OFF"},
    "PRIMEIRACOMPRA": {"discount": 15, "type": "percent", "min_value": 80, "label": "15% OFF primeira compra"},
}

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "prompt": "Qual dos seguintes é um tipo de dado primitivo em Python?",
        "options": ["Lista", "Dicionário", "Inteiro", "Classe"],
        "correct_index": 2,
        "explanation": "O tipo inteiro (int) é um tipo primitivo em Python.",
    },
    {
        "id": 2,
        "prompt": "O que significa HTML em desenvolvimento web?",
        "options": ["HyperText Markup Language", "HighText Markdown Language", "Hyperlink Media Language", "HyperText Making Language"],
        "correct_index": 0,
        "explanation": "HTML significa HyperText Markup Language.",
    },
]

LEARNING_TIPS = [
    "Quebre problemas grandes em etapas menores antes de codificar.",
    "Comente seu código com clareza para lembrar por que cada parte existe.",
    "Use o console do navegador para inspecionar variáveis em JavaScript rapidamente.",
    "Pratique algoritmos pequenos diariamente para fortalecer lógica de programação.",
    "Sempre teste seu código com casos extremos para evitar bugs inesperados.",
]

SHIPPING_TABLE = [
    (1, 19999, "SP", 12.90, 3),
    (20000, 23999, "RJ", 14.90, 5),
    (30000, 39999, "MG", 16.90, 6),
    (40000, 48999, "BA", 18.90, 8),
    (50000, 57999, "PE", 19.90, 9),
    (60000, 63999, "CE", 21.90, 10),
    (70000, 73999, "DF", 15.90, 5),
    (80000, 88999, "PR", 17.90, 7),
    (90000, 99999, "RS", 19.90, 8),
    (0, 99999, "OUTROS", 22.90, 10),
]

# --- Helpers ---

def hash_password(password: str) -> str:
    """Gera hash SHA256 da senha."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return hash_password(password) == password_hash


def generate_token() -> str:
    """Gera token aleatório."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def calc_shipping(zip_code: str) -> tuple:
    """Calcula frete baseado no CEP. Retorna (valor, prazo_dias, estado)."""
    try:
        cep_num = int(zip_code.replace("-", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return 22.90, 10, "OUTROS"

    for start, end, state, price, days in SHIPPING_TABLE:
        if start <= cep_num <= end:
            return price, days, state

    return 22.90, 10, "OUTROS"


def generate_pix_code() -> str:
    """Gera um código PIX simulado."""
    payload = f"00020126580014br.gov.bcb.pix0136{os.urandom(16).hex()}52040000530398654"
    total = "05.00"
    payload += f"{total}5802BR5913NOVASHOP6009SAO PAULO62070503***6304"
    checksum = hashlib.md5(payload.encode()).hexdigest()[:4].upper()
    return payload + checksum


def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(db.get_db)
) -> Optional[dict]:
    """Extrai usuário do token Bearer."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ", 1)[1]
    user_session = session.query(UserSession).filter_by(
        access_token=token, revoked=False
    ).first()
    
    if not user_session or not user_session.access_expires_at:
        return None
    
    if user_session.access_expires_at < datetime.now():
        return None
    
    user = user_session.user
    if not user:
        return None
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "address": user.address,
        "is_admin": bool(user.is_admin),
        "session_id": user_session.id,
    }


def sanitize_user(user) -> dict:
    """Remove informações sensíveis do usuário."""
    if isinstance(user, dict):
        return {k: v for k, v in user.items() if k != "password_hash"}
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "address": user.address,
        "is_admin": bool(user.is_admin),
    }


# --- Rotas de Produtos ---

@app.get("/api/products")
def list_products(session: Session = Depends(db.get_db)):
    """Lista todos os produtos com categorias."""
    products = session.query(Product).all()
    products_list = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "original_price": p.original_price,
            "category": p.category,
            "emoji": p.emoji,
            "sold": p.sold,
            "rating": p.rating,
            "reviews": p.reviews,
            "stock": p.stock,
            "tags": p.tags or [],
        }
        for p in products
    ]
    categories = sorted(set(p["category"] for p in products_list if p.get("category")))
    return {"products": products_list, "categories": categories}


@app.get("/api/products/{product_id}")
def get_product(product_id: int, session: Session = Depends(db.get_db)):
    """Retorna detalhes de um produto específico."""
    product = session.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "original_price": product.original_price,
        "category": product.category,
        "emoji": product.emoji,
        "sold": product.sold,
        "rating": product.rating,
        "reviews": product.reviews,
        "stock": product.stock,
        "tags": product.tags or [],
    }


# --- Rotas de Autenticação ---

@app.post("/api/register", status_code=201)
def register(data: dict, session: Session = Depends(db.get_db)):
    """Registra novo usuário."""
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    cpf = (data.get("cpf") or "").strip()
    address = (data.get("address") or "").strip()

    if not all([name, email, password, cpf, address]):
        raise HTTPException(status_code=400, detail="Preencha todos os campos")

    if session.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        cpf=cpf,
        address=address,
    )
    session.add(user)
    session.flush()

    # Cria sessão imediata
    now = datetime.now()
    user_session = UserSession(
        user_id=user.id,
        access_token=generate_token(),
        refresh_token=generate_token(),
        access_expires_at=now + timedelta(seconds=ACCESS_TOKEN_TTL),
        refresh_expires_at=now + timedelta(seconds=REFRESH_TOKEN_TTL),
        revoked=False,
    )
    session.add(user_session)
    session.commit()

    return {
        "access_token": user_session.access_token,
        "refresh_token": user_session.refresh_token,
        "user": sanitize_user(user),
    }


@app.post("/api/login")
def login(data: dict, session: Session = Depends(db.get_db)):
    """Autentica usuário e cria sessão."""
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="E-mail e senha são obrigatórios")

    user = session.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    now = datetime.now()
    user_session = UserSession(
        user_id=user.id,
        access_token=generate_token(),
        refresh_token=generate_token(),
        access_expires_at=now + timedelta(seconds=ACCESS_TOKEN_TTL),
        refresh_expires_at=now + timedelta(seconds=REFRESH_TOKEN_TTL),
        revoked=False,
    )
    session.add(user_session)
    session.commit()

    return {
        "access_token": user_session.access_token,
        "refresh_token": user_session.refresh_token,
        "user": sanitize_user(user),
    }


@app.post("/api/logout")
def logout(
    user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_db)
):
    """Revoga sessão do usuário."""
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    user_session = session.query(UserSession).get(user["session_id"])
    if user_session:
        user_session.revoked = True
        session.commit()

    return {"message": "Logout efetuado"}


@app.post("/api/refresh")
def refresh(data: dict, session: Session = Depends(db.get_db)):
    """Renova tokens de autenticação."""
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token obrigatório")

    user_session = session.query(UserSession).filter_by(
        refresh_token=refresh_token, revoked=False
    ).first()

    if not user_session or not user_session.refresh_expires_at:
        raise HTTPException(status_code=401, detail="Token de atualização inválido")

    if user_session.refresh_expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Token expirado")

    user = user_session.user
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Revoga token antigo e cria novo
    user_session.revoked = True
    session.commit()

    now = datetime.now()
    new_session = UserSession(
        user_id=user.id,
        access_token=generate_token(),
        refresh_token=generate_token(),
        access_expires_at=now + timedelta(seconds=ACCESS_TOKEN_TTL),
        refresh_expires_at=now + timedelta(seconds=REFRESH_TOKEN_TTL),
        revoked=False,
    )
    session.add(new_session)
    session.commit()

    return {
        "access_token": new_session.access_token,
        "refresh_token": new_session.refresh_token,
        "user": sanitize_user(user),
    }


# --- Rotas de Usuário ---

@app.get("/api/me")
def me(user: dict = Depends(get_current_user)):
    """Retorna dados do usuário autenticado."""
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"user": user}


# --- Rotas de Frete e Cupons ---

@app.get("/api/shipping")
def get_shipping(zip: str = "", subtotal: float = 0.0):
    """Calcula frete baseado no CEP."""
    price, days, state = calc_shipping(zip)
    free = subtotal >= FREE_SHIPPING_MIN

    return {
        "price": 0.0 if free else price,
        "original_price": price,
        "days": days,
        "state": state,
        "free_shipping_eligible": free,
    }


@app.get("/api/coupons")
def validate_coupon(code: str = "", subtotal: float = 0.0, session: Session = Depends(db.get_db)):
    """Valida cupom de desconto."""
    code = code.upper()

    if not code:
        raise HTTPException(status_code=400, detail="Cupom não informado")

    cp = session.query(Coupon).filter_by(code=code).first()
    if not cp:
        raise HTTPException(status_code=400, detail="Cupom inválido")

    if subtotal < cp.min_value:
        raise HTTPException(
            status_code=400,
            detail=f"Compra mínima: R$ {cp.min_value:.2f}"
        )

    return {
        "valid": True,
        "coupon": {
            "code": cp.code,
            "discount": cp.discount,
            "type": cp.type,
            "min_value": cp.min_value,
            "label": cp.label,
        },
    }


# --- Rotas de Dicas e Quiz ---

@app.get("/api/tips")
def get_tip():
    """Retorna uma dica de aprendizado aleatória."""
    return {"tip": random.choice(LEARNING_TIPS)}


@app.get("/api/quiz")
def get_quiz_question():
    """Retorna uma pergunta do quiz."""
    question = random.choice(QUIZ_QUESTIONS)
    return {
        "question": {
            "id": question["id"],
            "prompt": question["prompt"],
            "options": question["options"],
        }
    }


@app.post("/api/quiz/answer")
def answer_quiz(data: dict):
    """Valida resposta do quiz."""
    question_id = data.get("question_id")
    selected = data.get("selected")

    if question_id is None or selected is None:
        raise HTTPException(status_code=400, detail="Question ID e resposta são obrigatórios")

    question = next((q for q in QUIZ_QUESTIONS if q["id"] == question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")

    return {
        "correct": selected == question["correct_index"],
        "correct_index": question["correct_index"],
        "explanation": question["explanation"],
    }


# --- Rotas de Pedidos ---

@app.post("/api/orders", status_code=201)
def create_order(
    data: dict,
    user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_db)
):
    """Cria novo pedido."""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")

    if not data or "items" not in data:
        raise HTTPException(status_code=400, detail="Dados inválidos")

    customer_zip = data.get("customer", {}).get("zip", "")

    items = []
    subtotal_items = 0

    for item in data["items"]:
        prod = session.query(Product).get(item["id"])
        if not prod:
            raise HTTPException(status_code=400, detail=f"Produto {item['id']} não encontrado")

        qty = item.get("qty", 1)
        if qty > prod.stock:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {prod.name}")

        subtotal = prod.price * qty
        items.append({"product": prod, "qty": qty, "subtotal": subtotal})
        subtotal_items += subtotal

    # Aplicar cupom
    coupon_applied = None
    discount = 0
    coupon_code = data.get("coupon", "").upper()
    if coupon_code:
        cp = session.query(Coupon).filter_by(code=coupon_code).first()
        if cp and subtotal_items >= cp.min_value:
            if cp.type == "percent":
                discount = subtotal_items * cp.discount / 100
            else:
                discount = cp.discount
            coupon_applied = cp.code

    # Calcular frete
    shipping_price, shipping_days, shipping_state = calc_shipping(customer_zip)
    if subtotal_items >= FREE_SHIPPING_MIN:
        shipping_price = 0

    total_final = subtotal_items - discount + shipping_price

    # Gerar PIX
    pix_code = generate_pix_code()
    pix_expires = datetime.now() + timedelta(minutes=30)

    # Criar pedido
    order_obj = Order(
        customer_name=user["name"],
        customer_email=user["email"],
        customer_cpf=user.get("cpf", ""),
        customer_address=user.get("address", ""),
        customer_zip=customer_zip,
        subtotal=round(subtotal_items, 2),
        discount=round(discount, 2),
        shipping=round(shipping_price, 2),
        shipping_days=shipping_days,
        total=round(total_final, 2),
        coupon_code=coupon_applied,
        payment=data.get("payment", "pix"),
        pix_code=pix_code,
        pix_expires_at=pix_expires,
        created_at=datetime.now(),
        status="pending_payment",
    )
    session.add(order_obj)
    session.flush()

    for it in items:
        prod = it["product"]
        oi = OrderItem(
            order=order_obj,
            product_id=prod.id,
            name=prod.name,
            qty=it["qty"],
            price=prod.price,
            subtotal=round(it["subtotal"], 2),
        )
        session.add(oi)
        prod.stock = max(0, prod.stock - it["qty"])
        prod.sold = (prod.sold or 0) + it["qty"]

    session.commit()

    return {
        "order_id": order_obj.id,
        "total": order_obj.total,
        "pix_code": pix_code,
        "pix_expires_at": pix_expires.isoformat() if pix_expires else None,
        "message": "Pedido criado! Aguardando pagamento.",
    }


@app.get("/api/orders/{order_id}")
def get_order(
    order_id: int,
    user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_db)
):
    """Retorna detalhes de um pedido."""
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    order_obj = session.query(Order).get(order_id)
    if not order_obj:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    items = [
        {
            "id": it.product_id,
            "name": it.name,
            "qty": it.qty,
            "price": it.price,
            "subtotal": it.subtotal,
        }
        for it in order_obj.items
    ]

    return {
        "id": order_obj.id,
        "customer": {
            "name": order_obj.customer_name,
            "email": order_obj.customer_email,
            "cpf": order_obj.customer_cpf,
            "address": order_obj.customer_address,
            "zip": order_obj.customer_zip,
        },
        "items_detail": items,
        "subtotal": order_obj.subtotal,
        "discount": order_obj.discount,
        "shipping": order_obj.shipping,
        "shipping_days": order_obj.shipping_days,
        "total": order_obj.total,
        "coupon": order_obj.coupon_code,
        "payment": order_obj.payment,
        "pix_code": order_obj.pix_code,
        "pix_expires_at": order_obj.pix_expires_at.isoformat() if order_obj.pix_expires_at else None,
        "created_at": order_obj.created_at.isoformat() if order_obj.created_at else None,
        "status": order_obj.status,
    }


# --- Rotas de Admin ---

@app.post("/api/products", status_code=201)
def create_product(
    data: dict,
    user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_db)
):
    """Cria novo produto (admin)."""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")

    product = Product(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price", 0.0),
        original_price=data.get("original_price"),
        category=data.get("category"),
        emoji=data.get("emoji"),
        sold=data.get("sold", 0),
        rating=data.get("rating", 0.0),
        reviews=data.get("reviews", 0),
        stock=data.get("stock", 0),
        tags=data.get("tags", []),
    )
    session.add(product)
    session.commit()

    return {"id": product.id, "message": "Produto criado."}


# --- Event Handlers ---

@app.on_event("startup")
def startup():
    """Inicializa o banco de dados na startup."""
    db.init_db()
    db.migrate_from_memory([], {}, [], [])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
