<div align="center">
  <img src="https://raw.githubusercontent.com/4pixeltechBR/GestorDeTrafego/main/ui/assets/icon.png" alt="Logo Gestor de Tráfego IA" width="120" onerror="this.style.display='none'">
  
  # 🚀 Gestor de Tráfego IA (PilotoAds)
  
  **O seu Copiloto de Tráfego Pago Open Source e Custo Zero.**
  
  [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Meta Ads API](https://img.shields.io/badge/Meta_Ads_API-v25.0-0668E1.svg)](https://developers.facebook.com/docs/marketing-apis/)
  [![Google Ads API](https://img.shields.io/badge/Google_Ads_API-v18.0-EA4335.svg)](https://developers.google.com/google-ads/api/docs/start)
  
  <p align="center">
    Uma arquitetura multi-agente <strong>Omnichannel (Meta + Google)</strong> que interpreta briefings casuais, cria copys persuasivas ou anúncios de pesquisa (RSA), valida contra as políticas, e sobe campanhas automaticamente—tudo rodando no conforto da sua própria máquina.
  </p>
</div>

---

## 💡 O Jogo Mudou: Por que este projeto existe?

Se você é um pequeno empresário, gestor de tráfego iniciante ou desenvolvedor, sabe que ferramentas de automação de tráfego são caras (SaaS com mensalidades absurdas) e muitas vezes roubam a inteligência dos seus dados.

O **Gestor de Tráfego IA** foi concebido sob três pilares inegociáveis:
1. **Privacidade Absoluta:** O banco de dados (SQLite), seus Tokens do Meta Ads e seu orçamento ficam trancados na **sua máquina**. Nenhuma credencial sua vai para a nuvem.
2. **Custo Zero de IA (LLM Router):** O sistema utiliza uma cascata de inteligência artificial. Ele tenta usar provedores gratuitos poderosos (ex: Groq, Gemini) de forma sequencial. Se a chave A der erro de limite (Rate Limit 429), ele engata a chave B invisivelmente em 300ms.
3. **Simplicidade:** Dois cliques no Windows (`start.bat`) e uma interface moderna e bonita se abre no seu navegador. Nenhuma porta preta de terminal chata.

---

## 🌪️ A Mágica do Custo-Zero (Sua Cascata de APIs)

A grande sacada do Gestor de Tráfego IA é o **LLM Router**. 

Provedores poderosos oferecem cotas gratuitas (Free Tier), mas com limites rigorosos (Ex: *15 requisições por minuto* ou *30K tokens por minuto*). Se você tenta processar uma campanha inteira em um só provedor grátis, você bate no teto (Erro 429) e seu script morre.

**Como o Gestor resolve isso:**
Ele roda uma "Cascata". O sistema aciona os agentes em uma fila de provedores pré-configurada no arquivo `config/llm_cascade.yaml`. Se a **Google (Gemini)** barrar você por cota estourada, o código intercepta a queda silenciosamente em 300ms e re-envia a mesma prompt, com o mesmo contexto, para a **Groq (Llama 3.3)**. 

O usuário final só vê a interface trabalhando, sem interrupções e sem pagar $1 dólar à OpenAI ou Anthropic.

### 🏆 Qual Modelo e Provedor Escolher?

Para manter o ecossistema Custo-Zero e ao mesmo tempo ter raciocínio nível Sênior, nós recomendamos fortemente esta trindade (configure no seu `.env`):

1. **Groq (`llama-3.3-70b-versatile`)**:
   - **Por que usar:** É absurdamente rápido (800+ tokens por segundo) e a inteligência do Llama 3 70B é perfeitamente afiada para formatar JSONs e interpretar contextos.
   - **Onde o sistema usa:** *Orquestrador* (raciocínio rápido) e *Executor* (geração pura de JSON com zero margem de formatação errada).
2. **Google AI Studio (`gemini-2.0-flash`)**:
   - **Por que usar:** O Free Tier do Google tem uma janela de contexto colossal e ele é absurdamente criativo.
   - **Onde o sistema usa:** *Copywriter* (criatividade) e *Analista* (digestão de números grandes e métricas do Facebook).
3. **NVIDIA NIM (`meta/llama-3.3-70b-instruct`)** ou **OpenRouter (Free Models)**:
   - **Por que usar:** Atuam como os zagueiros substitutos. Se a Groq e o Google esgotarem as cotas diárias/minuto, o tráfego passa em fração de segundos pela linha defensiva gratuita alternativa.

---

## 🧠 Arquitetura: Os 6 Especialistas

O motor pulsa através de 6 agentes IA de papéis estritos. Eles não conversam sobre trivialidades; eles constroem campanhas omnichannel.

- 🧠 **Orquestrador:** Interpreta seu desejo ("Quero vender pneu aro 15 na Zona Sul de SP"), estrutura as variáveis (público, idade) e decide o melhor canal: Meta (Visual) ou Google (Intenção/Urgência).
- ✍️ **Copywriter:** No Meta, gera 3 opções de textos persuasivos focados em conversão. No Google, gera Headlines e Descriptions milimetricamente calculadas para o formato RSA (Responsive Search Ads).
- 🔍 **Keyword Planner (Novo):** O farejador do Google Search. Extrai palavras-chave exatas, de frase e amplas, além de blindar a campanha listando palavras negativas (Ex: "grátis", "como fazer").
- ⚖️ **Compliance:** Varre os textos gerados em busca de palavras proibidas pelo algoritmo do Facebook e Google. Ele barra multas e bloqueios antes mesmo da API sonhar com a campanha.
- 📐 **Executor:** Envelopa os dados validados e bifurca o sistema construindo o pacote JSON Graph API ou os frames gRPC mutáveis do Google Ads. (Sempre em modo Pausada, para sua revisão).
- 📊 **Analista (O Motor Noturno):** Todos os dias, às 08:00 AM, ele acorda sozinho, caça os resultados diários, calcula o ROAS / CPA e te envia um relatório gerencial direto no Telegram. *(Modo Copilot)*.

---

## 🛠️ Como Instalar e Rodar (Windows)

Não se preocupe com comandos obscuros. Siga estes passos simples:

### Pré-requisitos
- [Python 3.10 ou superior](https://www.python.org/downloads/) instalado no Windows (lembre de marcar "Add Python to PATH" na instalação).
- O [Git](https://git-scm.com/) instalado, se for clonar via terminal.

### Passo 1: Clone ou Faça o Download
No terminal, digite:
```bash
git clone https://github.com/4pixeltechBR/GestorDeTrafego.git "Gestor de Trafego"
cd "Gestor de Trafego"
```
*(Ou clique no botão verde `Code > Download ZIP` e extraia a pasta nas suas "Área de Trabalho" ou Documentos).*

### Passo 2: Configure as suas Chaves (O Cofre)
Renomeie o arquivo base para poder colocar seus dados:
```bash
copy .env.example .env
```
Abra o ".env" no bloco de notas e insira apenas as chaves de IA que você tiver (quanto mais, melhor para a Cascata funcionar de graça):
- [Groq Console](https://console.groq.com/keys) (Super Rápido e Grátis)
- [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini Grátis)

### Passo 3: Inicie a Máquina!
Dê dois cliques no arquivo:
```
▶️ start.bat
```
Ele vai baixar todas as bibliotecas necessárias, preparar o banco de dados e lançar a interface interativa no endereço: `http://localhost:8080`.

---

## 🛡️ Guardrails: O Cinto de Segurança do seu Dinheiro

Deixar IA gerenciar dinheiro assusta? Sim. Por isso nós não confiamos nela.

A Fase 4 do projeto instalou os **Guardrails Rígidos em Python e SQLite**. 
Não importa o que a IA faça: se no `.env` está definido `BUDGET_MAX_DIARIO=100`, qualquer solicitação de criação de campanha que vá exceder R$100,00 da conta diária é barrada localmente. A IA nunca tocará na porta da Meta API nestes casos.

---

## 🤝 O Projeto é da Comunidade! (Como Contribuir)

Estou oferecendo essa estrutura de R$0 a R$1M de escala de graça. Se você tem ideias para novos nichos, novos Agentes (Agente de Vídeo, Agente de Imagem, etc.), puxe um Fork!

Leia o arquivo `CONTRIBUTING.md` para entender como nossa arquitetura funciona e faça seu Pull Request.

---

## 📜 Licença

Aberto sob a luz da **MIT License**. Use, quebre, remonte e venda serviços em cima se quiser. Apenas, se puder, credite.

<div align="center">
  <i>Construído com ❤️, Inteligência Artificial e a meta de ajudar PMEs no Brasil.</i>
</div>
