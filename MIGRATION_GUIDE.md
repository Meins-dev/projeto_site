# 🚀 Migração: HTTP Server → FastAPI

## O que mudou?

### Antes (store.py com http.server)
```python
# if/else aninhados
if path == "/api/products":
    # ... lógica
elif path == "/api/login":
    # ... lógica
# ... 200+ linhas de if/else
```

### Agora (main.py com FastAPI)
```python
# Decorators com roteamento automático
@app.get("/api/products")
def list_products():
    # ... lógica

@app.post("/api/login")
def login():
    # ... lógica
```

## 📋 Benefícios

✅ **Tipagem automática** - FastAPI valida tipos automaticamente  
✅ **Documentação automática** - Swagger em `/docs` e ReDoc em `/redoc`  
✅ **Performance** - Uvicorn é mais rápido que http.server  
✅ **Escalabilidade** - Fácil adicionar middlewares, rotas, etc.  
✅ **Deploy simples** - Render/Railway reconhecem FastAPI nativamente  
✅ **Async support** - Suporte a async/await (se precisar no futuro)  

## 🔧 Como usar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente (.env)
```bash
# Para desenvolvimento (SQLite local)
DATABASE_URL=sqlite:///./nshop.db

# Para produção (PostgreSQL em Render/Railway)
DATABASE_URL=postgresql://user:password@host:5432/database
```

### 3. Executar o servidor

**Desenvolvimento:**
```bash
python main.py
# Ou com auto-reload:
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

**Produção (Render/Railway):**
```bash
# O Render/Railway executa automaticamente:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Acessar a API
- **API**: http://localhost:5000
- **Documentação interativa**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 📊 Comparação de Rotas

| Rota | HTTP Server | FastAPI | Status |
|------|-------------|---------|--------|
| GET /api/products | ✅ Funciona | ✅ Funciona | Idêntico |
| GET /api/products/{id} | ✅ Funciona | ✅ Funciona | Idêntico |
| POST /api/login | ✅ Funciona | ✅ Funciona | Idêntico |
| POST /api/register | ✅ Funciona | ✅ Funciona | Idêntico |
| POST /api/orders | ✅ Funciona | ✅ Funciona | Idêntico |
| GET /api/me | ✅ Funciona | ✅ Funciona | Idêntico |
| GET /api/shipping | ✅ Funciona | ✅ Funciona | Query params melhorados |
| GET /api/coupons | ✅ Funciona | ✅ Funciona | Query params melhorados |
| GET /api/tips | ✅ Funciona | ✅ Funciona | Idêntico |
| GET /api/quiz | ✅ Funciona | ✅ Funciona | Idêntico |
| POST /api/quiz/answer | ✅ Funciona | ✅ Funciona | Idêntico |

## 🔐 Autenticação

**Header obrigatório:**
```
Authorization: Bearer <token>
```

**Exemplo com curl:**
```bash
curl -H "Authorization: Bearer seu_token_aqui" \
  http://localhost:5000/api/me
```

## 🗄️ Estrutura de Arquivos

```
project_dropshiping/
├── main.py                 # 🆕 Novo servidor FastAPI
├── db.py                   # ✏️ Atualizado para PostgreSQL
├── store.py                # ⚠️ Legado (pode deletar)
├── requirements.txt        # ✏️ Atualizado com FastAPI
├── .env                    # 🆕 Variáveis de ambiente
├── .gitignore
├── nshop.db               # SQLite local (desenvolvimento)
└── netlify/               # Funções legadas (Netlify)
```

## 🚀 Deploy no Render/Railway

### Render.com
1. Conecte seu repositório GitHub
2. Crie novo Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Adicione `DATABASE_URL` nas variáveis de ambiente (PostgreSQL do Render)

### Railway.app
1. Conecte seu repositório GitHub
2. Selecione Python
3. Railway detecta automaticamente `requirements.txt`
4. Adicione plugin PostgreSQL
5. Railway expõe `DATABASE_URL` automaticamente

## ⚠️ Migração de Dados

Se tinha dados no SQLite antigo:
```python
# Em db.py, execute uma única vez:
from db import SessionLocal, migrate_from_memory
session = SessionLocal()
# Import dos dados antigos
migrate_from_memory(PRODUCTS, COUPONS, USERS, ORDERS)
```

## 🔄 Diferenças Técnicas

### Query Parameters
**Antes (store.py):**
```python
qs = parse_qs(urlparse(self.path).query)
zip_code = qs.get("zip", [""])[0]
```

**Agora (FastAPI):**
```python
@app.get("/api/shipping")
def get_shipping(zip: str = "", subtotal: float = 0.0):
    # FastAPI parseia automaticamente
```

### Respostas JSON
**Antes (store.py):**
```python
def _json(self, data, status=200):
    payload = json.dumps(data, ensure_ascii=False).encode()
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    # ... mais headers
```

**Agora (FastAPI):**
```python
@app.get("/api/products")
def list_products():
    return {...}  # FastAPI serializa automaticamente
```

### Dependências
**Antes (store.py):**
```python
user = get_auth_user(self)
if not user:
    self._json({"error": "Não autenticado"}, 401)
```

**Agora (FastAPI):**
```python
def list_products(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
```

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements.txt
```

### `DATABASE_URL not found`
Crie arquivo `.env` na raiz do projeto (já criado para você).

### `Port already in use`
```bash
# Use porta diferente
uvicorn main:app --port 5001
```

### CORS errors
FastAPI já tem CORS configurado para todas as origens. Se precisar restringir:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-frontend.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 📚 Próximos passos

1. ✅ Deletar `store.py` (ou manter como referência)
2. ✅ Testar todas as rotas com `http://localhost:5000/docs`
3. ✅ Configurar CI/CD (GitHub Actions)
4. ✅ Deploy em Render/Railway
5. ✅ Monitorar logs em produção

---

**Perguntas?** Consulte a [documentação FastAPI](https://fastapi.tiangolo.com/)
