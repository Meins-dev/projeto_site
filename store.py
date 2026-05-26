from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import hashlib
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Catálogo de produtos (estilo dropship) ──────────────────────────
PRODUCTS = [
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
    {
        "id": 2,
        "name": "Smartwatch Fitness Tracker",
        "description": "Monitor cardíaco, GPS integrado, resistente à água IP68, 14 dias de bateria.",
        "price": 129.90,
        "original_price": 299.90,
        "category": "Eletrônicos",
        "emoji": "⌚",
        "sold": 893,
        "rating": 4.5,
        "reviews": 201,
        "stock": 28,
        "tags": ["frete gratis"],
    },
    {
        "id": 3,
        "name": "Ring Light LED 26cm",
        "description": "3 temperaturas de cor, tripé ajustável incluso, ideal para lives e selfies.",
        "price": 49.90,
        "original_price": 119.90,
        "category": "Eletrônicos",
        "emoji": "💡",
        "sold": 2105,
        "rating": 4.3,
        "reviews": 578,
        "stock": 120,
        "tags": ["mais vendido"],
    },
    {
        "id": 4,
        "name": "Mochila Anti-Furto USB",
        "description": "Porta USB externa, compartimento laptop 15.6, material impermeável.",
        "price": 89.90,
        "original_price": 189.90,
        "category": "Acessórios",
        "emoji": "🎒",
        "sold": 674,
        "rating": 4.6,
        "reviews": 189,
        "stock": 63,
        "tags": ["frete gratis"],
    },
    {
        "id": 5,
        "name": "Garrafa Térmica 500ml LED",
        "description": "Aço inox 304, mantém temperatura por 12h, display LED de temperatura.",
        "price": 59.90,
        "original_price": 139.90,
        "category": "Casa",
        "emoji": "🧴",
        "sold": 1562,
        "rating": 4.8,
        "reviews": 445,
        "stock": 95,
        "tags": ["mais vendido"],
    },
    {
        "id": 6,
        "name": "Mini Projetor Portátil 1080p",
        "description": "Full HD nativo, WiFi e Bluetooth, compatível com celular e notebook.",
        "price": 299.90,
        "original_price": 599.90,
        "category": "Eletrônicos",
        "emoji": "📽️",
        "sold": 431,
        "rating": 4.4,
        "reviews": 98,
        "stock": 15,
        "tags": ["frete gratis"],
    },
    {
        "id": 7,
        "name": "Organizador Maquiagem LED 360",
        "description": "Espelho com LED, rotação 360, compartimentos ajustáveis, acrílico premium.",
        "price": 69.90,
        "original_price": 159.90,
        "category": "Beleza",
        "emoji": "💄",
        "sold": 987,
        "rating": 4.6,
        "reviews": 267,
        "stock": 54,
        "tags": [],
    },
    {
        "id": 8,
        "name": "Luminária Lunar 3D 15cm",
        "description": "Recarregável USB, 16 cores com controle, toque para trocar cor.",
        "price": 39.90,
        "original_price": 99.90,
        "category": "Casa",
        "emoji": "🌙",
        "sold": 1834,
        "rating": 4.9,
        "reviews": 623,
        "stock": 200,
        "tags": ["mais vendido"],
    },
    {
        "id": 9,
        "name": "Câmera Segurança WiFi 360",
        "description": "1080p, visão noturna colorida, áudio bidirecional, detecção de movimento.",
        "price": 89.90,
        "original_price": 219.90,
        "category": "Eletrônicos",
        "emoji": "📷",
        "sold": 1120,
        "rating": 4.3,
        "reviews": 334,
        "stock": 72,
        "tags": ["frete gratis"],
    },
    {
        "id": 10,
        "name": "Kit Skincare Coreano 5 passos",
        "description": "Limpeza, tônico, sérum vitamina C, hidratante ácido hialurônico, protetor solar.",
        "price": 119.90,
        "original_price": 279.90,
        "category": "Beleza",
        "emoji": "✨",
        "sold": 756,
        "rating": 4.7,
        "reviews": 198,
        "stock": 38,
        "tags": ["frete gratis"],
    },
    {
        "id": 11,
        "name": "Umidificador Ultrassônico 300ml",
        "description": "Ultra silencioso, LED decorativo 7 cores, desligamento automático.",
        "price": 54.90,
        "original_price": 129.90,
        "category": "Casa",
        "emoji": "💨",
        "sold": 1345,
        "rating": 4.5,
        "reviews": 401,
        "stock": 88,
        "tags": [],
    },
    {
        "id": 12,
        "name": "Óculos de Sol Polarizado UV400",
        "description": "Lentes polarizadas, proteção UV400, design unissex, estojo rígido incluso.",
        "price": 44.90,
        "original_price": 109.90,
        "category": "Acessórios",
        "emoji": "🕶️",
        "sold": 2011,
        "rating": 4.4,
        "reviews": 567,
        "stock": 150,
        "tags": ["mais vendido"],
    },
    {
        "id": 13,
        "name": "Caixa de Som Bluetooth 20W",
        "description": "Som estéreo, à prova d'água IPX7, 12h de bateria, luzes LED.",
        "price": 99.90,
        "original_price": 229.90,
        "category": "Eletrônicos",
        "emoji": "🔊",
        "sold": 923,
        "rating": 4.6,
        "reviews": 276,
        "stock": 56,
        "tags": ["frete gratis"],
    },
    {
        "id": 14,
        "name": "Carregador Portátil 20000mAh",
        "description": "Carga rápida 22.5W, 3 saídas USB, display LED, compatível com todos.",
        "price": 69.90,
        "original_price": 159.90,
        "category": "Eletrônicos",
        "emoji": "🔋",
        "sold": 1678,
        "rating": 4.5,
        "reviews": 489,
        "stock": 110,
        "tags": ["mais vendido"],
    },
    {
        "id": 15,
        "name": "Difusor de Aromas 500ml",
        "description": "Ultrassônico, 4 modos de timer, LED ambiente, cobre até 40m².",
        "price": 79.90,
        "original_price": 179.90,
        "category": "Casa",
        "emoji": "🌿",
        "sold": 534,
        "rating": 4.7,
        "reviews": 145,
        "stock": 42,
        "tags": [],
    },
    {
        "id": 16,
        "name": "Kit Pinceis Maquiagem 12 peças",
        "description": "Cerdas sintéticas premium, cabo madeira, estojo elegante de couro eco.",
        "price": 49.90,
        "original_price": 119.90,
        "category": "Beleza",
        "emoji": "🖌️",
        "sold": 867,
        "rating": 4.8,
        "reviews": 234,
        "stock": 95,
        "tags": [],
    },
    {
        "id": 17,
        "name": "Webcam 1080p com Microfone",
        "description": "Auto foco, correção de luz, microfone duplo, plug and play USB.",
        "price": 79.90,
        "original_price": 189.90,
        "category": "Eletrônicos",
        "emoji": "📹",
        "sold": 645,
        "rating": 4.3,
        "reviews": 178,
        "stock": 67,
        "tags": [],
    },
    {
        "id": 18,
        "name": "Relógio Minimalista Magnético",
        "description": "Pulseira magnética inox, movimento quartzo japonês, resistente à água.",
        "price": 89.90,
        "original_price": 219.90,
        "category": "Acessórios",
        "emoji": "🕐",
        "sold": 412,
        "rating": 4.6,
        "reviews": 109,
        "stock": 33,
        "tags": ["frete gratis"],
    },
    {
        "id": 19,
        "name": "LED Strip RGB 10m com Controle",
        "description": "5050 RGB, controle remoto 44 teclas, adesivo 3M, cortável a cada 3 leds.",
        "price": 34.90,
        "original_price": 89.90,
        "category": "Casa",
        "emoji": "🌈",
        "sold": 2345,
        "rating": 4.2,
        "reviews": 712,
        "stock": 300,
        "tags": ["mais vendido"],
    },
    {
        "id": 20,
        "name": "Massageador Cervical Elétrico",
        "description": "6 modos, aquecimento infravermelho, recarregável USB, ergonômico.",
        "price": 59.90,
        "original_price": 149.90,
        "category": "Saúde",
        "emoji": "💆",
        "sold": 789,
        "rating": 4.5,
        "reviews": 201,
        "stock": 58,
        "tags": [],
    },
    {
        "id": 21,
        "name": "Kit Bandas Elásticas Fitness",
        "description": "5 níveis de resistência, bolsa transporte, guia exercícios incluso.",
        "price": 29.90,
        "original_price": 79.90,
        "category": "Saúde",
        "emoji": "💪",
        "sold": 1567,
        "rating": 4.4,
        "reviews": 423,
        "stock": 250,
        "tags": [],
    },
    {
        "id": 22,
        "name": "Lanterna Tática Recarregável",
        "description": "5000 lumens, 5 modos, zoom ajustável, bateria 18650 inclusa.",
        "price": 49.90,
        "original_price": 129.90,
        "category": "Acessórios",
        "emoji": "🔦",
        "sold": 934,
        "rating": 4.6,
        "reviews": 267,
        "stock": 78,
        "tags": [],
    },
    {
        "id": 23,
        "name": "Aspirador de Pó Robô Inteligente",
        "description": "Mapeamento laser, app WiFi, 120min autonomia, aspira e passa pano.",
        "price": 399.90,
        "original_price": 899.90,
        "category": "Casa",
        "emoji": "🤖",
        "sold": 234,
        "rating": 4.3,
        "reviews": 67,
        "stock": 12,
        "tags": ["frete gratis"],
    },
    {
        "id": 24,
        "name": "Perfume Importado 100ml EDT",
        "description": "Fragrância amadeirada, longa duração 8h+, frasco premium.",
        "price": 89.90,
        "original_price": 229.90,
        "category": "Beleza",
        "emoji": "🧴",
        "sold": 612,
        "rating": 4.7,
        "reviews": 178,
        "stock": 41,
        "tags": ["frete gratis"],
    },
    {
        "id": 25,
        "name": "Teclado Mecânico 60% RGB",
        "description": "Switch blue, retroiluminação RGB, hot-swap, USB-C, compacto.",
        "price": 149.90,
        "original_price": 329.90,
        "category": "Eletrônicos",
        "emoji": "⌨️",
        "sold": 556,
        "rating": 4.8,
        "reviews": 189,
        "stock": 34,
        "tags": ["frete gratis"],
    },
    {
        "id": 26,
        "name": "Tapete de Yoga Antiderrapante",
        "description": "TPE ecológico, 6mm espessura, 183x61cm, alça transporte inclusa.",
        "price": 44.90,
        "original_price": 109.90,
        "category": "Saúde",
        "emoji": "🧘",
        "sold": 445,
        "rating": 4.5,
        "reviews": 112,
        "stock": 89,
        "tags": [],
    },
    {
        "id": 27,
        "name": "Mouse Gamer 7200 DPI",
        "description": "Sensor óptico, 6 botões programáveis, RGB, 12000 cliques.",
        "price": 59.90,
        "original_price": 149.90,
        "category": "Eletrônicos",
        "emoji": "🖱️",
        "sold": 1123,
        "rating": 4.4,
        "reviews": 345,
        "stock": 96,
        "tags": [],
    },
    {
        "id": 28,
        "name": "Organizador de Cabos Magnético",
        "description": "Silicone premium, 6 slots, base adesiva, compatível com todos cabos.",
        "price": 19.90,
        "original_price": 49.90,
        "category": "Acessórios",
        "emoji": "🧲",
        "sold": 3201,
        "rating": 4.3,
        "reviews": 890,
        "stock": 500,
        "tags": ["mais vendido"],
    },
]

CATEGORIES = sorted(set(p["category"] for p in PRODUCTS))

# ── Cupons de desconto ──────────────────────────────────────────────
COUPONS = {
    "NOVA10": {"discount": 10, "type": "percent", "min_value": 50, "label": "10% OFF"},
    "NOVA20": {"discount": 20, "type": "percent", "min_value": 100, "label": "20% OFF"},
    "FRETE5": {"discount": 5, "type": "fixed", "min_value": 30, "label": "R$ 5OFF"},
    "PRIMEIRACOMPRA": {"discount": 15, "type": "percent", "min_value": 80, "label": "15% OFF primeira compra"},
}

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "prompt": "Qual dos seguintes é um tipo de dado primitivo em Python?",
        "options": ["Lista", "Dicionário", "Inteiro", "Classe"],
        "correct_index": 2,
        "explanation": "O tipo inteiro (int) é um tipo primitivo em Python. Listas e dicionários são tipos de coleção, e classes são estruturas de definição de objetos.",
    },
    {
        "id": 2,
        "prompt": "O que significa HTML em desenvolvimento web?",
        "options": ["HyperText Markup Language", "HighText Markdown Language", "Hyperlink Media Language", "HyperText Making Language"],
        "correct_index": 0,
        "explanation": "HTML significa HyperText Markup Language e é a linguagem de marcação usada para estruturar páginas web.",
    },
    {
        "id": 3,
        "prompt": "Qual atributo HTML usamos para carregar um arquivo CSS externo?",
        "options": ["src", "href", "link", "rel"],
        "correct_index": 1,
        "explanation": "O atributo href é usado dentro da tag <link> para referenciar um arquivo CSS externo.",
    },
    {
        "id": 4,
        "prompt": "Qual comando Git cria um novo branch local?",
        "options": ["git branch nome", "git checkout main", "git clone nome", "git push origin"],
        "correct_index": 0,
        "explanation": "O comando git branch nome cria um novo branch local com o nome especificado.",
    },
]

LEARNING_TIPS = [
    "Quebre problemas grandes em etapas menores antes de codificar.",
    "Comente seu código com clareza para lembrar por que cada parte existe.",
    "Use o console do navegador para inspecionar variáveis em JavaScript rapidamente.",
    "Pratique algoritmos pequenos diariamente para fortalecer lógica de programação.",
    "Sempre teste seu código com casos extremos para evitar bugs inesperados.",
]

# ── Tabela de frete por região (CEP) ────────────────────────────────
SHIPPING_TABLE = [
    (1, 19999, "SP", 12.90, 3),    # SP capital/regiao - 3 dias
    (20000, 23999, "RJ", 14.90, 5), # RJ - 5 dias
    (30000, 39999, "MG", 16.90, 6), # MG - 6 dias
    (40000, 48999, "BA", 18.90, 8), # BA - 8 dias
    (50000, 57999, "PE", 19.90, 9), # PE - 9 dias
    (60000, 63999, "CE", 21.90, 10),# CE - 10 dias
    (70000, 73999, "DF", 15.90, 5), # DF - 5 dias
    (80000, 88999, "PR", 17.90, 7), # PR/SC - 7 dias
    (90000, 99999, "RS", 19.90, 8), # RS - 8 dias
    (0, 99999, "OUTROS", 22.90, 10),  # Default - 10 dias
]

FREE_SHIPPING_MIN = 199

def calc_shipping(zip_code):
    """Calcula frete baseado no CEP. Retorna (valor, prazo_dias, estado)."""
    try:
        cep_num = int(zip_code.replace("-", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return 22.90, 10, "OUTROS"

    for start, end, state, price, days in SHIPPING_TABLE:
        if start <= cep_num <= end:
            return price, days, state

    return 22.90, 10, "OUTROS"


# ── Armazém de pedidos ──────────────────────────────────────────────
ORDERS = []
ORDER_COUNTER = 0
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
USERS = []
SESSIONS = {}


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password, password_hash):
    return hash_password(password) == password_hash


def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, indent=2, ensure_ascii=False)


def load_users():
    global USERS
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            USERS = json.load(f)
    else:
        USERS = []


def generate_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()


def get_auth_user(handler):
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    email = SESSIONS.get(token)
    if not email:
        return None
    return next((u for u in USERS if u["email"] == email), None)


def sanitize_user(user):
    return {k: v for k, v in user.items() if k != "password_hash"}


def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(ORDERS, f, indent=2, ensure_ascii=False)


def load_orders():
    global ORDERS, ORDER_COUNTER
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            ORDERS = json.load(f)
        ORDER_COUNTER = len(ORDERS)


load_users()
load_orders()


def generate_pix_code():
    """Gera um código PIX simulado."""
    payload = f"00020126580014br.gov.bcb.pix0136{os.urandom(16).hex()}52040000530398654"
    total = "05.00"
    payload += f"{total}5802BR5913NOVASHOP6009SAO PAULO62070503***6304"
    checksum = hashlib.md5(payload.encode()).hexdigest()[:4].upper()
    return payload + checksum


# ── Servidor ────────────────────────────────────────────────────────
class StoreHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/products":
            self._json({"products": PRODUCTS, "categories": CATEGORIES})
            return

        if path == "/api/me":
            user = get_auth_user(self)
            if not user:
                self._json({"error": "Não autenticado"}, 401)
                return
            self._json({"user": sanitize_user(user)})
            return

        if path == "/api/shipping":
            qs = parse_qs(urlparse(self.path).query)
            zip_code = qs.get("zip", [""])[0]
            subtotal = float(qs.get("subtotal", ["0"])[0])
            price, days, state = calc_shipping(zip_code)
            free = subtotal >= FREE_SHIPPING_MIN
            self._json({
                "price": 0.0 if free else price,
                "original_price": price,
                "days": days,
                "state": state,
                "free_shipping_eligible": free,
            })
            return

        if path == "/api/coupons":
            code = qs.get("code", [""])[0].upper()
            subtotal = float(qs.get("subtotal", ["0"])[0])
            coupon = COUPONS.get(code)
            if not coupon:
                self._json({"valid": False, "message": "Cupom inválido"})
                return
            if subtotal < coupon["min_value"]:
                self._json({
                    "valid": False,
                    "message": f"Compra mínima: R$ {coupon['min_value']:.2f}",
                })
                return
            self._json({"valid": True, "coupon": {**coupon, "code": code}})
            return

        if path == "/api/tips":
            tip = random.choice(LEARNING_TIPS)
            self._json({"tip": tip})
            return

        if path == "/api/quiz":
            question = random.choice(QUIZ_QUESTIONS)
            self._json({
                "question": {
                    "id": question["id"],
                    "prompt": question["prompt"],
                    "options": question["options"],
                }
            })
            return

        if path.startswith("/api/orders/"):
            order_id = path.split("/")[-1]
            try:
                order_id = int(order_id)
            except ValueError:
                self._json({"error": "ID inválido"}, 400)
                return
            order = next((o for o in ORDERS if o["id"] == order_id), None)
            if not order:
                self._json({"error": "Pedido não encontrado"}, 404)
                return
            self._json(order)
            return

        super().do_GET()

    def do_POST(self):
        global ORDER_COUNTER
        path = urlparse(self.path).path

        if path == "/api/login":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            email = (body.get("email") or "").strip().lower()
            password = body.get("password", "")
            user = next((u for u in USERS if u["email"] == email), None)
            if not user or not verify_password(password, user.get("password_hash", "")):
                self._json({"error": "Credenciais inválidas"}, 401)
                return
            token = generate_token()
            SESSIONS[token] = user["email"]
            self._json({"token": token, "user": sanitize_user(user)})
            return

        if path == "/api/register":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            name = (body.get("name") or "").strip()
            email = (body.get("email") or "").strip().lower()
            password = body.get("password", "")
            cpf = (body.get("cpf") or "").strip()
            address = (body.get("address") or "").strip()

            if not name or not email or not password or not cpf or not address:
                self._json({"error": "Preencha todos os campos"}, 400)
                return
            if any(u["email"] == email for u in USERS):
                self._json({"error": "E-mail já cadastrado"}, 400)
                return

            user = {
                "name": name,
                "email": email,
                "password_hash": hash_password(password),
                "cpf": cpf,
                "address": address,
            }
            USERS.append(user)
            save_users()
            token = generate_token()
            SESSIONS[token] = email
            self._json({"token": token, "user": sanitize_user(user)}, 201)
            return

        if path == "/api/logout":
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
                SESSIONS.pop(token, None)
            self._json({"message": "Logout efetuado"})
            return

        if path == "/api/quiz/answer":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            question_id = body.get("question_id")
            selected = body.get("selected")
            question = next((q for q in QUIZ_QUESTIONS if q["id"] == question_id), None)
            if not question:
                self._json({"error": "Pergunta não encontrada"}, 404)
                return
            correct = selected == question["correct_index"]
            self._json({
                "correct": correct,
                "correct_index": question["correct_index"],
                "explanation": question["explanation"],
            })
            return

        if path == "/api/orders":
            user = get_auth_user(self)
            if not user:
                self._json({"error": "Autenticação necessária"}, 401)
                return

            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            if not body or "items" not in body:
                self._json({"error": "Dados inválidos"}, 400)
                return

            customer = {
                "name": user["name"],
                "email": user["email"],
                "cpf": user.get("cpf", ""),
                "address": user.get("address", ""),
                "zip": body.get("customer", {}).get("zip", ""),
            }

            # Valida itens
            items = []
            total = 0
            for item in body["items"]:
                product = next((p for p in PRODUCTS if p["id"] == item["id"]), None)
                if not product:
                    self._json({"error": f"Produto {item['id']} não encontrado"}, 400)
                    return
                qty = item.get("qty", 1)
                if qty > product["stock"]:
                    self._json({"error": f"Estoque insuficiente para {product['name']}"}, 400)
                    return
                subtotal = product["price"] * qty
                items.append({**product, "qty": qty, "subtotal": subtotal})
                total += subtotal

            # Calcula subtotal
            subtotal_items = total

            # Aplica cupom
            coupon_applied = None
            discount = 0
            coupon_code = body.get("coupon", "").upper()
            if coupon_code and coupon_code in COUPONS:
                cp = COUPONS[coupon_code]
                if subtotal_items >= cp["min_value"]:
                    if cp["type"] == "percent":
                        discount = subtotal_items * cp["discount"] / 100
                    else:
                        discount = cp["discount"]
                    coupon_applied = {**cp, "code": coupon_code}

            # Calcula frete
            zip_code = customer.get("zip", "")
            shipping_price, shipping_days, shipping_state = calc_shipping(zip_code)
            if subtotal_items >= FREE_SHIPPING_MIN:
                shipping_price = 0

            total_final = subtotal_items - discount + shipping_price

            # Gera PIX
            pix_code = generate_pix_code()
            pix_expires = datetime.now()
            pix_expires = pix_expires.replace(minute=pix_expires.minute + 30)

            ORDER_COUNTER += 1
            order = {
                "id": ORDER_COUNTER,
                "customer": customer,
                "items": body["items"],
                "items_detail": [{
                    "id": i["id"],
                    "name": i["name"],
                    "qty": i["qty"],
                    "price": i["price"],
                    "subtotal": round(i["subtotal"], 2),
                } for i in items],
                "subtotal": round(subtotal_items, 2),
                "discount": round(discount, 2),
                "shipping": round(shipping_price, 2),
                "shipping_days": shipping_days,
                "total": round(total_final, 2),
                "coupon": coupon_applied,
                "payment": body.get("payment", "pix"),
                "pix_code": pix_code,
                "pix_expires_at": pix_expires.isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "pending_payment",
            }
            ORDERS.append(order)
            save_orders()

            self._json({
                "order_id": order["id"],
                "total": order["total"],
                "pix_code": pix_code,
                "pix_expires_at": pix_expires.isoformat(),
                "message": "Pedido criado! Aguardando pagamento.",
            }, 201)
            return

        self.send_error(404)

    def _json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")


if __name__ == "__main__":
    port = 5000
    server = HTTPServer(("0.0.0.0", port), StoreHandler)
    print(f"NovaShop rodando em http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        save_orders()
        server.server_close()
