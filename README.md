# Projeto Site

Um projeto de estudos de programação que combina um site simples com um backend em Python para integração com provedores de LLM e roteamento inteligente de requests.

## Objetivo

Este repositório serve como um ambiente de aprendizado para programação e arquitetura de aplicações web. A ideia é experimentar:

- roteamento inteligente entre provedores de IA usando o `SmartRouter`
- chamadas assíncronas a provedores locais e externos via `httpx`
- um endpoint de status (`/status`) para monitorar a saúde dos provedores
- testes automatizados em Python com `pytest`

## Recursos principais

- `python/smart_router.py`: lógica de seleção de provedor com base em latência, custo e saúde
- `python/ollama_provider.py`: integração com o Oak LLM local via Ollama
- `python/atomic_chat_provider.py`: suporte opcional a Atomic Chat
- `python/status_asgi.py`: endpoint ASGI que expõe o status dos provedores em JSON
- `python/tests/`: suíte de testes para validar comportamento e conversões de mensagens

## Como usar

1. Crie e ative um ambiente virtual Python:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale dependências (se houver um `requirements.txt` ou adicione o que precisar):

```bash
pip install httpx pytest
```

3. Execute os testes:

```bash
pytest -q
```

4. Rode o endpoint de status localmente com `uvicorn`:

```bash
pip install "uvicorn[standard]"
uvicorn python.status_asgi:app --reload --port 8000
```

Acesse `http://127.0.0.1:8000/status` para ver o status dos provedores.

## Organização do projeto

- `index.html`: frontend do site
- `store.py`: lógica de dados do site
- `python/`: código backend e provedores de IA
- `python/tests/`: testes unitários e de integração leve

## Variáveis de ambiente úteis

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `OLLAMA_BASE_URL`
- `ATOMIC_CHAT_BASE_URL`
- `BIG_MODEL`
- `SMALL_MODEL`
- `ROUTER_STRATEGY` (valor padrão: `balanced`)
- `ROUTER_FALLBACK` (valor padrão: `true`)

## Por que este projeto?

Ele foi criado para aprender e experimentar com integrações de IA, arquiteturas assíncronas e roteamento inteligente de solicitações, tudo em um contexto simples de site de estudo de programação.

