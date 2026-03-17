<div align="center">
  <img src="https://raw.githubusercontent.com/4pixeltechBR/GestorDeTrafego/main/ui/assets/icon.png" alt="Logo Gestor de Tráfego IA" width="120" onerror="this.style.display='none'">
  
  # 🚀 Gestor de Tráfego IA (PilotoAds)
  
  **O seu Copiloto de Tráfego Pago Open Source e Custo Zero.**
  
  [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Meta Ads API](https://img.shields.io/badge/Meta_Ads_API-v25.0-0668E1.svg)](https://developers.facebook.com/docs/marketing-apis/)
  
  <p align="center">
    Uma arquitetura multi-agente que interpreta briefings casuais, cria copys persuasivas validadas contra as políticas do Facebook, e sobe campanhas no Meta Ads automaticamente—tudo rodando no conforto (e segurança) da sua própria máquina.
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

## 🧠 Arquitetura: Os 5 Especialistas

O motor pulsa através de 5 agentes IA de papéis estritos. Eles não conversam sobre trivialidades; eles constroem campanhas.

- 🧠 **Orquestrador:** Interpreta seu desejo ("Quero vender pneu aro 15 na Zona Sul de SP") e estrutura as variáveis (público, idade, geolocalização, nicho).
- ✍️ **Copywriter:** Munido de templates YAML específicos para cada nicho, gera 3 opções de textos persuasivos focados em conversão direta.
- ⚖️ **Compliance:** Varre os textos gerados em busca de palavras proibidas pelo algoritmo do Facebook (ex: "renda extra", "emagreça 10kg"). Ele barra multas e bloqueios de BM antes mesmo da API da Meta sonhar com a campanha.
- 📐 **Executor:** Envelopa os dados validados em JSONs blindados para a Meta Graph API v25.0, criando a Campanha (Sempre em modo Pausada, para sua revisão) -> AdSet -> AdCreative -> Anúncio.
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
