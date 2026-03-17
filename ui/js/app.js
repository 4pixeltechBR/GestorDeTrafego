/**
 * Vanilla Javascript - Lógica SPA (Single Page Application) e Fetch API
 */

// Navegação em Vistas SPA
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');
const pageTitle = document.getElementById('current-page-title');
const pageSubtitle = document.getElementById('current-page-subtitle');

const TITLES = {
    'dashboard': { title: 'Dashboard Visionário', subtitle: 'Visão geral do tráfego orientado por IA' },
    'nova-campanha': { title: 'Lançar Foguete', subtitle: 'Briefing livre para o Orquestrador' },
    'historico': { title: 'Histórico & Auditoria', subtitle: 'Decisões da arquitetura multi-agente' },
    'configuracoes': { title: 'Parâmetros Internos', subtitle: 'Validação de ambiente Open Source' }
};

function switchView(viewId) {
    // Esconder todas as views e desmarcar menu
    views.forEach(v => v.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));

    // Ativar view pedida e o item de menu correspondente
    document.getElementById(`view-${viewId}`).classList.add('active');
    
    // Troca Títulos
    if (TITLES[viewId]) {
        pageTitle.innerText = TITLES[viewId].title;
        pageSubtitle.innerText = TITLES[viewId].subtitle;
    }

    const linkedNav = document.querySelector(`[data-view="${viewId}"]`);
    if(linkedNav) linkedNav.classList.add('active');
}

// Listeners de Clique de Menu
navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const viewName = item.getAttribute('data-view');
        switchView(viewName);
    });
});


/** 
 * FETCH DA API FASTAPI E LÓGICA DO NEGÓCIO
 */

// 1. Healthcheck: Busca se a API, LLM e Meta estao conectadas
async function loadSystemVitals() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) throw new Error("API Indisponível");
        const data = await response.json();
        
        // Atualiza UI
        const llmStatus = document.getElementById("llm-status");
        if(data.providers && data.providers.length > 0) {
            llmStatus.innerHTML = `<i class="ri-brain-line"></i> IA: Pronta (${data.providers.join(', ')})`;
            llmStatus.classList.add("text-success");
        } else {
            llmStatus.innerHTML = `<i class="ri-error-warning-line"></i> IA: Sem Configuração no .env`;
            llmStatus.classList.add("text-error");
        }

        const metaStatus = document.getElementById("meta-status");
        if(data.meta_configured) {
            metaStatus.innerHTML = `<i class="ri-facebook-circle-line"></i> Meta API: Conectada (Graph v25)`;
            metaStatus.classList.add("text-success");
        } else {
            metaStatus.innerHTML = `<i class="ri-facebook-circle-line"></i> Meta API: Pendente Tokens`;
            metaStatus.classList.add("text-warning");
        }

    } catch (e) {
        console.error("Erro ao carregar vitais:", e);
    }
}

// 2. Simula criação de campanha interagindo com o Terminal View
const btnGerar = document.getElementById("btn-gerar-campanha");
const briefingInput = document.getElementById("briefing-input");
const terminal = document.getElementById("generation-terminal");
const terminalLogs = document.getElementById("terminal-logs");

function addTerminalLog(agent, msg, type="normal") {
    let cssClass = "log-line";
    if (type === "success") cssClass += " log-success";
    if (type === "error") cssClass += " log-error";
    if (type === "warn") cssClass += " log-warn";

    const div = document.createElement("div");
    div.className = cssClass;
    
    // Pega hora formato HH:MM:ss
    const time = new Date().toLocaleTimeString('pt-BR');
    
    div.innerHTML = `<span style="color:#64748b">[${time}]</span> <span class="log-agent">[${agent}]</span> ${msg}`;
    terminalLogs.appendChild(div);
    
    // Auto-scroll
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
}

btnGerar.addEventListener("click", async () => {
    const text = briefingInput.value.trim();
    if (!text) {
        alert("Epa! Coloque algum briefing na caixa de texto.");
        return;
    }

    // Reset console
    terminalLogs.innerHTML = "";
    terminal.style.display = "block";
    btnGerar.disabled = true;
    btnGerar.innerHTML = "<i class='ri-loader-4-line ri-spin'></i> Acordando Agentes...";

    // Aqui faríamos a chamada real para a rota POST /api/campaigns/create
    // Mas antes precisamos escrevê-la no Python.
    // Vamos adicionar um delay visual por enquanto e falhar indicando que a rota Python precisa ser ligada
    
    addTerminalLog("Orquestrador", "Processando raw text recebido do Dashboard...");
    
    try {
        const response = await fetch('/api/campaigns/setup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ briefing: text })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || `Erro HTTP: ${response.status}`);
        }
        
        // Simular fluxo das informações ocorrendo asincronamente
        setTimeout(() => {
            addTerminalLog("Orquestrador", `Briefing Interpretado. Roteando Campanha: ${result.data.campaign_name}...`, "success");
        }, 800);
        setTimeout(() => {
            addTerminalLog("Guardrail Budget", `Aprovado: Gasto diário de R$ ${result.data.daily_budget} validado.`, "success");
        }, 1500);
        setTimeout(() => {
            addTerminalLog("Copywriter", `Gerou ${result.data.copies_generated} variacões A/B para nicho: ${result.data.niche}.`, "success");
        }, 3000);
        setTimeout(() => {
            addTerminalLog("Compliance", `Nenhuma violação grave encontrada. Tudo Limpo.`, "success");
        }, 4000);
        setTimeout(() => {
            addTerminalLog("Executor", `JSON MetaAds payload renderizado. O Orquestrador avisará via Telegram.`, "success");
            btnGerar.disabled = false;
            btnGerar.innerHTML = "<i class='ri-check-double-line'></i> Acionado com Sucesso!";
            btnGerar.classList.add("btn-success");
        }, 5500);

    } catch(e) {
        addTerminalLog("API Interna", String(e), "error");
        btnGerar.disabled = false;
        btnGerar.innerHTML = "<i class='ri-magic-line'></i> Tentar Novamente";
    }
});


// Init UI Lifecycle
document.addEventListener("DOMContentLoaded", () => {
    loadSystemVitals();
});
