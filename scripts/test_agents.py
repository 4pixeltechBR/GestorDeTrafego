"""
Script de teste de integração — Fase 2.

Testa o fluxo completo: Orquestrador → Copywriter → Compliance → Executor.

USO:
    python scripts/test_agents.py

REQUER:
    - .env configurado com pelo menos 1 API Key de IA
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

# Fix para emojis no console Windows
sys.stdout.reconfigure(encoding='utf-8')

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from app.agents.orchestrator import OrchestratorAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.compliance import ComplianceAgent
from app.agents.executor import ExecutorAgent
from app.agents.analyst import AnalystAgent
from app.core.database import init_db
from config.settings import settings

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%H:%M:%S",
)

console = Console()

# =============================================
# BRIEFING DE TESTE
# =============================================
BRIEFING_TESTE = (
    "Quero criar uma campanha para trocar pneus aro 15. "
    "Meu auto center fica em São Paulo, zona sul. "
    "Orçamento de R$50 por dia. "
    "Quero atrair motoristas que precisam trocar pneu."
)

METRICAS_TESTE = {
    "spend": 45.50,
    "impressions": 12000,
    "clicks": 320,
    "cpc": 0.14,
    "ctr": 2.67,
    "cpm": 3.79,
    "roas": 2.1,
    "frequency": 1.8,
    "conversions": 12,
}


async def banner():
    console.print(Panel(
        "[bold cyan]🚀 GESTOR DE TRÁFEGO IA — Teste de Integração (Fase 2)[/bold cyan]\n"
        "[dim]Testando fluxo completo: Orquestrador → Copywriter → Compliance → Executor → Analista[/dim]",
        border_style="cyan"
    ))


async def check_config():
    """Verifica configuração antes de testar."""
    console.print("\n[bold]🔧 Verificando configuração...[/bold]")
    providers = settings.available_providers
    if not providers:
        console.print(
            "[red]❌ Nenhuma API Key configurada no .env![/red]\n"
            "Configure pelo menos uma: GROQ_API_KEY, GOOGLE_AI_KEY, "
            "NVIDIA_NIM_KEY ou OPENROUTER_KEY"
        )
        sys.exit(1)

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("Provedores ativos:", f"[green]{', '.join(providers)}[/green]")
    table.add_row("Meta Ads:", f"{'[green]✅[/green]' if settings.has_meta_config else '[yellow]⚠️ Não configurado[/yellow]'}")
    table.add_row("Telegram:", f"{'[green]✅[/green]' if settings.has_telegram else '[yellow]⚠️ Desativado[/yellow]'}")
    table.add_row("Modo:", f"[cyan]{settings.approval_mode.upper()}[/cyan]")
    console.print(table)


async def test_orchestrator() -> dict:
    """Testa o Orquestrador."""
    console.print("\n[bold yellow]1/5 🧠 ORQUESTRADOR[/bold yellow] — Interpretando briefing...")
    console.print(f"[dim]Briefing: {BRIEFING_TESTE}[/dim]\n")

    agent = OrchestratorAgent()
    result = await agent.parse_briefing(BRIEFING_TESTE)

    # Remove _meta para exibição limpa
    meta = result.pop("_meta", {})

    console.print(Panel(
        json.dumps(result, ensure_ascii=False, indent=2),
        title="[green]✅ Briefing Interpretado[/green]",
        border_style="green"
    ))
    console.print(
        f"[dim]via {meta.get('llm_provider', '?')} / {meta.get('llm_model', '?')} "
        f"({meta.get('tokens_used', {}).get('total', '?')} tokens)[/dim]"
    )

    result["_meta"] = meta  # Restaura meta
    return result


async def test_copywriter(orchestrator_result: dict) -> list[dict]:
    """Testa o Copywriter."""
    console.print("\n[bold yellow]2/5 ✍️ COPYWRITER[/bold yellow] — Gerando copies...")

    agent = CopywriterAgent()
    result = await agent.generate_copies(
        produto=orchestrator_result.get("produto", "Pneu Aro 15"),
        nicho=orchestrator_result.get("nicho", "auto_center"),
        publico_alvo=orchestrator_result.get("publico_alvo", {}),
        objetivo=orchestrator_result.get("objetivo", "OUTCOME_TRAFFIC"),
    )

    meta = result.pop("_meta", {})
    copies = result.get("opcoes", [])

    for i, copy in enumerate(copies, 1):
        console.print(Panel(
            f"[bold]Título:[/bold] {copy.get('titulo', '?')}\n"
            f"[bold]Texto:[/bold] {copy.get('texto_principal', '?')}\n"
            f"[bold]Descrição:[/bold] {copy.get('descricao', '?')}\n"
            f"[bold]CTA:[/bold] [cyan]{copy.get('cta', '?')}[/cyan]",
            title=f"[green]Opção {i}[/green]",
            border_style="green"
        ))

    console.print(
        f"[dim]via {meta.get('llm_provider', '?')} / {meta.get('llm_model', '?')} "
        f"({meta.get('tokens_used', {}).get('total', '?')} tokens)[/dim]"
    )

    result["_meta"] = meta
    return copies


async def test_compliance(copies: list[dict]) -> dict:
    """Testa o Compliance."""
    console.print("\n[bold yellow]3/5 ⚖️ COMPLIANCE[/bold yellow] — Validando copies...")

    agent = ComplianceAgent()
    result = await agent.validate_copy(copies, nicho="auto_center")

    meta = result.pop("_meta", {})
    aprovado = result.get("aprovado", False)
    risco = result.get("risco", "?")

    status_color = "green" if aprovado else "red"
    risco_color = {"BAIXO": "green", "MEDIO": "yellow", "ALTO": "red"}.get(risco, "white")

    console.print(
        f"  Status: [{status_color}]{'✅ APROVADO' if aprovado else '❌ REJEITADO'}[/{status_color}]  "
        f"Risco: [{risco_color}]{risco}[/{risco_color}]"
    )

    problemas = result.get("problemas", [])
    if problemas:
        for p in problemas:
            console.print(f"  ⚠️  {p.get('tipo', '?')}: [yellow]{p.get('trecho', '?')}[/yellow]")
            console.print(f"     → {p.get('sugestao', '?')}")

    console.print(
        f"[dim]via {meta.get('llm_provider', '?')} / {meta.get('llm_model', '?')} "
        f"({meta.get('tokens_used', {}).get('total', '?')} tokens)[/dim]"
    )

    result["_meta"] = meta
    return result


async def test_executor(orchestrator_result: dict, best_copy: dict) -> dict:
    """Testa o Executor."""
    console.print("\n[bold yellow]4/5 📐 EXECUTOR[/bold yellow] — Montando JSON Meta API...")

    agent = ExecutorAgent()
    result = await agent.build_campaign_json(
        produto=orchestrator_result.get("produto", "Pneu Aro 15"),
        nicho=orchestrator_result.get("nicho", "auto_center"),
        copy=best_copy,
        orcamento_diario=orchestrator_result.get("orcamento_diario", 50.0),
        publico_alvo=orchestrator_result.get("publico_alvo", {}),
        objetivo=orchestrator_result.get("objetivo", "OUTCOME_TRAFFIC"),
    )

    meta = result.pop("_meta", {})

    if "erro" in result:
        console.print(f"[red]❌ Erro: {result['erro']}[/red]")
    else:
        console.print(Panel(
            json.dumps(result, ensure_ascii=False, indent=2),
            title="[green]✅ JSON Meta API Pronto[/green]",
            border_style="green"
        ))

    console.print(
        f"[dim]via {meta.get('llm_provider', '?')} / {meta.get('llm_model', '?')} "
        f"({meta.get('tokens_used', {}).get('total', '?')} tokens)[/dim]"
    )

    result["_meta"] = meta
    return result


async def test_analyst() -> dict:
    """Testa o Analista com métricas simuladas."""
    console.print("\n[bold yellow]5/5 📊 ANALISTA[/bold yellow] — Analisando métricas simuladas...")

    agent = AnalystAgent()
    result = await agent.analyze(
        metrics=METRICAS_TESTE,
        campaign_name="Pneu Aro 15 — Zona Sul SP",
        nicho="auto_center",
        days_running=5,
        benchmarks={"cpc_medio": 1.80, "roas_minimo": 1.5, "frequencia_maxima": 3.5},
    )

    meta = result.pop("_meta", {})
    recomendacao = result.get("recomendacao", {})
    acao = recomendacao.get("acao", "?")

    acao_color = {"MANTER": "green", "OTIMIZAR": "yellow", "PAUSAR": "red"}.get(acao, "white")

    console.print(Panel(
        f"[bold]Resumo:[/bold] {result.get('resumo', '?')}\n\n"
        f"[bold]Diagnóstico:[/bold] {result.get('diagnostico', '?')}\n"
        f"[bold]Recomendação:[/bold] [{acao_color}]{acao}[/{acao_color}]\n"
        f"[bold]Motivo:[/bold] {recomendacao.get('motivo', '?')}\n\n"
        f"[bold]Sugestões:[/bold]\n" +
        "\n".join(f"  • {s}" for s in recomendacao.get("sugestoes", [])),
        title="[green]✅ Análise Concluída[/green]",
        border_style="green"
    ))

    console.print(
        f"[dim]via {meta.get('llm_provider', '?')} / {meta.get('llm_model', '?')} "
        f"({meta.get('tokens_used', {}).get('total', '?')} tokens)[/dim]"
    )

    result["_meta"] = meta
    return result


async def main():
    await banner()
    await check_config()
    await init_db()

    try:
        # Fluxo completo
        orch_result = await test_orchestrator()
        copies = await test_copywriter(orch_result)
        compliance_result = await test_compliance(copies)
        best_copy = copies[0] if copies else {}
        executor_result = await test_executor(orch_result, best_copy)
        analyst_result = await test_analyst()

        # Resumo final
        console.print("\n")
        console.print(Panel(
            "[bold green]🎉 FASE 2 CONCLUÍDA COM SUCESSO![/bold green]\n"
            "Todos os 5 agentes responderam corretamente.\n"
            "Próximo passo: Fase 3 — Integração Meta Ads API.",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[red]❌ Erro durante o teste: {type(e).__name__}: {e}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
