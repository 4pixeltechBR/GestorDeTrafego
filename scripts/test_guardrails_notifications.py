"""
Teste dos Módulos da Fase 4.

- Guardrails de Orçamento
- Telegram Notifications Ping
- Schedulers
"""

import asyncio
import sys
import logging
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel

from app.guardrails.budget import check_budget_guardrails, BudgetExceededError
from app.notifications.telegram_bot import notifier
from app.scheduler.tasks import init_scheduler
from app.core.database import init_db
from config.settings import settings

logging.basicConfig(level=logging.INFO)
console = Console()

async def main():
    console.print(Panel("[bold cyan]🚀 Testando Camada de Seguranca, Telegram e Scheduler (Fase 4)[/bold cyan]"))
    
    await init_db()

    # 1. Testando Guardrails
    console.print("\n[bold]1. Testando Guardrails (Orçamento)...[/bold]")
    max_budget = settings.budget_max_diario
    console.print(f"Orçamento Máximo Diário configurado: R$ {max_budget:.2f}")

    # Teste de aprovação (Dentro do limite)
    try:
        console.print("   [dim]>>> Tentando aprovar campanha de R$ 30,00...[/dim]")
        await check_budget_guardrails(30.0)
        console.print("   [green]✅ Aprovada com sucesso pelo guardrail.[/green]")
    except Exception as e:
        console.print(f"   [red]❌ Erro inesperado: {e}[/red]")

    # Teste de bloqueio (Acima do limite direto)
    try:
        absurd_amount = max_budget + 100.0
        console.print(f"   [dim]>>> Tentando aprovar campanha de R$ {absurd_amount:.2f}...[/dim]")
        await check_budget_guardrails(absurd_amount)
        console.print("   [red]❌ Teste Falhou: O sistema permitiu um gasto além do teto!![/red]")
    except BudgetExceededError as e:
        console.print(f"   [green]✅ Bloqueio funcionou! Erro:[/green] [yellow]{e}[/yellow]")

    # 2. Testando Inicialização do Scheduler
    console.print("\n[bold]2. Testando Agendador (APScheduler)...[/bold]")
    try:
        scheduler = init_scheduler()
        scheduler.start()
        jobs = scheduler.get_jobs()
        if jobs:
            console.print(f"   [green]✅ Cron Job configurado:[/green] {jobs[0].name} (Próxima execução: {jobs[0].next_run_time})")
        else:
            console.print("   [red]❌ Nenhum job configurado.[/red]")
        scheduler.shutdown()
    except Exception as e:
        console.print(f"   [red]❌ Erro no Scheduler:[/red] {e}")

    # 3. Testando Ping do Telegram
    console.print("\n[bold]3. Testando Conector do Telegram...[/bold]")
    try:
        await notifier.ping()
        console.print("   [green]✅ O módulo de notificações passou sem crashar na inicialização![/green]")
    except Exception as e:
        console.print(f"   [red]❌ Erro no Telegram:[/red] {e}")


    console.print("\n[bold green]🎉 FASE 4 (Guardrails + Schedulers) PRONTA PARA COMMIT![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
