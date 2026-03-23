"""
formatter.py — Formata resultados do pipeline para exibição no Telegram.
"""


def format_campaign_preview(result: dict) -> str:
    """
    Formata o resultado completo do pipeline em mensagem HTML para o Telegram.
    Exibe TODAS as copies geradas para o usuário escolher.
    """
    orch = result.get("orchestration", {})
    copies = result.get("copies", [])
    canal = result.get("canal", "meta")
    orcamento = result.get("orcamento", 0)
    nicho = result.get("nicho", "")

    canal_label = "📘 Facebook/Instagram" if canal == "meta" else "🔍 Google Search"

    lines = [
        "✅ <b>Campanha pronta para revisão!</b>",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📋 <b>RESUMO</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📍 Plataforma: {canal_label}",
        f"🏷️  Nicho: {nicho}",
        f"💰 Orçamento: R${orcamento:.0f}/dia",
        "",
    ]

    if canal == "meta":
        for i, copy in enumerate(copies, 1):
            lines += [
                "━━━━━━━━━━━━━━━━━━━━━━",
                f"✍️  <b>OPÇÃO {i}</b>",
                f"<b>{copy.get('titulo', '')}</b>",
                f"{copy.get('texto_principal', '')}",
                f"<i>{copy.get('descricao', '')}</i>",
                "",
            ]
    elif canal == "google_search":
        for i, copy in enumerate(copies, 1):
            headlines = copy.get("headlines", [])
            descriptions = copy.get("descriptions", [])
            lines += [
                "━━━━━━━━━━━━━━━━━━━━━━",
                f"🔍 <b>OPÇÃO {i} — RSA</b>",
                f"<b>Headlines:</b> {' | '.join(headlines[:3])}",
                f"<b>Descriptions:</b> {descriptions[0] if descriptions else ''}",
                "",
            ]

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ <i>A campanha será criada como PAUSADA. Você ativa quando quiser.</i>",
    ]

    return "\n".join(lines)


def format_compliance_error(problemas: list) -> str:
    """Formata erros de compliance para exibição no Telegram."""
    lines = [
        "⚖️ <b>Compliance bloqueou a campanha</b>",
        "",
        "Os seguintes problemas foram encontrados:",
        "",
    ]
    for p in problemas:
        lines.append(f"• <b>{p.get('tipo', '?')}:</b> <i>{p.get('trecho', '?')}</i>")
        lines.append(f"  → {p.get('sugestao', '')}")
        lines.append("")

    lines.append("Reformule o briefing e tente novamente.")
    return "\n".join(lines)


def format_daily_report(campaign_name: str, metrics: dict, analysis: dict) -> str:
    """Formata o relatório diário de uma campanha para o Telegram."""
    diag = analysis.get("diagnostico", "?")
    rec = analysis.get("recomendacao", {})
    acao = rec.get("acao", "?")
    sugestoes = rec.get("sugestoes", [])

    diag_emoji = {"SAUDAVEL": "🟢", "ATENCAO": "🟡", "CRITICO": "🔴"}.get(diag, "⚪")
    acao_emoji = {"MANTER": "✅", "OTIMIZAR": "⚠️", "PAUSAR": "🛑"}.get(acao, "❓")

    lines = [
        f"<b>📣 {campaign_name}</b>",
        f"├ Investido: R${metrics.get('spend', 0):.2f}",
        f"├ Alcance: {metrics.get('impressions', 0):,}",
        f"├ Cliques: {metrics.get('clicks', 0)}",
        f"├ CPC: R${metrics.get('cpc', 0):.2f}",
        f"├ CTR: {metrics.get('ctr', 0):.2f}%",
        f"└ ROAS: {metrics.get('roas', 0):.1f}x",
        "",
        f"{diag_emoji} Diagnóstico: <b>{diag}</b>",
        f"{acao_emoji} Recomendação: <b>{acao}</b>",
    ]

    if sugestoes:
        lines.append("")
        lines.append("💡 <b>Sugestões:</b>")
        for s in sugestoes[:2]:
            lines.append(f"• {s}")

    return "\n".join(lines)
