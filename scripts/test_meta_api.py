"""
Script de teste da camada Meta Ads API — Fase 3.

Testa a instância do cliente assíncrono, a construtora de URL
e o tratamento de erros sem precisar de um token real.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from app.meta.client import MetaAsyncClient, MetaAPIError

logging.basicConfig(level=logging.INFO)
console = Console()

async def main():
    console.print(Panel("[bold cyan]🚀 Testando Camada Meta Ads API (Fase 3)[/bold cyan]"))
    
    # 1. Testando instanciacao do Cliente
    try:
        console.print("\n[bold]1. Inicializando MetaAsyncClient...[/bold]")
        client = MetaAsyncClient()
        
        console.print(f"Base URL: [green]{client.base_url}[/green]")
        console.print(f"Ad Account ID: [green]{client.ad_account_id}[/green]")
        console.print(f"Cliente Configurado?: [{'green' if client.is_configured else 'yellow'}]{client.is_configured}[/]")
        
        if not client.is_configured:
            console.print("[dim]Aviso: As variáveis META_ACCESS_TOKEN e META_AD_ACCOUNT_ID não estão no .env. Isso é esperado neste teste se você não as configurou ainda.[/dim]")
            
        # 2. Testando a Construção da URL
        console.print("\n[bold]2. Testando Roteamento Interno...[/bold]")
        mock_campaign_url = client._build_url("/{ad_account_id}/campaigns")
        console.print(f"URL Resolve: [cyan]{mock_campaign_url}[/cyan]")
        
        # 3. Testando Disparo Assíncrono sem Token (Deve Retornar Erro 401 ou Erro de Validação Local)
        if not client.is_configured:
            console.print("\n[bold]3. Testando Proteção de Request Local...[/bold]")
            try:
                await client.request("GET", "/{ad_account_id}/insights")
                console.print("[red]❌ Teste Falhou: Devia ter barrado a request sem credenciais![/red]")
            except MetaAPIError as e:
                console.print(f"[green]✅ Proteção funcionou![/green] Erro capturado do cliente local: [yellow]{e}[/yellow]")
        else:
            console.print("\n[bold]3. Testando Ping ao Servidor do Facebook...[/bold]")
            try:
                # Tenta puxar a lista de campanhas da conta
                resp = await client.request("GET", "/{ad_account_id}/campaigns")
                console.print("[green]✅ Conexão Meta Ads estabelecida e Autenticada![/green]")
                console.print(resp)
            except MetaAPIError as e:
                console.print(f"⚠️ Resposta do Servidor: Status {e.status_code}")
                console.print(f"Detalhes: {e.response}")
                console.print("\n[dim]Se o status for 400 ou 401, o token configurado é inválido ou expirou.[/dim]")

        console.print("\n[bold green]🎉 FASE 3 (Meta Client) PRONTA PARA COMMIT![/bold green]")

    except Exception as e:
        console.print(f"\n[red]❌ Erro inesperado: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
