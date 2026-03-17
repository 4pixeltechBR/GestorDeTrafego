# Contribuindo com o Gestor de Tráfego IA

Obrigado pelo seu interesse em melhorar o motor Open Source que viemos construindo! Não importa se você achou um pequeno erro de digitação nos templates `.yaml` ou se reconstruiu todo o motor assíncrono do FastAPI, **todas as ajudas de PRs são muito bem-vindas**.

---

## 🧭 Onde mais precisamos de você?

O sistema atual tem **5 agentes**, porém a publicidade cresce vertiginosamente. Se você quer atuar num P0 urgente:

1. **Templates de Nicho (`/templates/`):** Nós lançamos com o `auto_center.yaml`. Se você conhece outros nichos profundamente de Meta Ads (Ex: Clínica de Estética, Hamburgueria Delivery, Dentista), crie os dicionários YAML inspirados neste molde e envie um **Pull Request**. A Comunidade agradece.
2. **Dashboard UI (`/ui/`):** Usamos Vanilla CSS (Módulo PilotoAds). Você constrói dashboards melhores? Precisamos tornar a aba de Histórico reativa puxando dados do banco de dados (hoje as rotas estão engatilhadas no `app/main.py`).
3. **Novos Provedores na Cascata:** Configurou Llama via Ollama (Local)? Modificou o `llm_router.py` para injetar RAG em VectorDB? Abra um Discuss ou Issue para acoplarmos no `settings.py`!

---

## 🛠️ Regras Básicas do Fluxo do Repositório (Branches)

- **`main`**: Código ultraestável (Onde tudo deve falhar menos em produção).
- Nunca crie PRs para a `main`. Sempre faça seu "Fork", crie uma branch com o nome da sua evolução (`git checkout -b feature/novo-agente-designer`) e envie o PR.
- Siga os Padrões do PEP8 para códigos em Python.

---

## ⚙️ Ambiente de Desenvolvimento Local

Para evitar quebrar suas chaves de API oficiais (o Orquestrador puxa os trocados) ou subir anúncios falhos na Meta do seu Cliente:

1. Modifique seu arquivo `config/settings.py` e o seu local `.env` incluindo `APPROVAL_MODE=copilot`.
2. Isto garantirá que o *Agente Executor* monte o JSON e as cópias, acione a Cascata inteira de validação, **mas não dispare o POST final** no servidor oficial do Facebook sem o seu "YES" via Telegram.

Divirta-se pilotando a IA.
