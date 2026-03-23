"""
handlers.py — Handlers do Telegram.

Recebe mensagens de texto como briefings e callbacks de botões inline.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.core.pipeline import run_campaign_pipeline, ComplianceBlockedError
from app.core.database import save_pending_campaign, get_pending_campaign, update_campaign_status
from app.guardrails.budget import BudgetExceededError
from app.bot.formatter import format_campaign_preview, format_compliance_error
from app.bot.keyboards import approval_keyboard
from app.meta.manager import publish_campaign_structure
from config.settings import settings

logger = logging.getLogger(__name__)


def _is_admin(update: Update) -> bool:
    """Verifica se a mensagem veio do admin configurado no .env."""
    return str(update.effective_chat.id) == str(settings.telegram_admin_chat_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recebe qualquer mensagem de texto como briefing e aciona o pipeline completo.
    """
    if not _is_admin(update):
        return

    briefing = update.message.text.strip()

    if len(briefing) < 10:
        await update.message.reply_text(
            "⚠️ Briefing muito curto. Me conta mais sobre o que quer anunciar."
        )
        return

    msg = await update.message.reply_text("⏳ Analisando briefing...")

    try:
        # Roda o pipeline completo
        result = await run_campaign_pipeline(briefing)

        # Salva como PENDING no banco
        pending_id = await save_pending_campaign(result)

        # Se APPROVAL_MODE=auto, executa sem pedir aprovação
        if result.get("auto_execute"):
            await msg.edit_text("⚡ Modo AUTO: subindo campanha diretamente...")
            await _handle_approve_direct(msg, pending_id)
            return

        # Formata e envia preview com botões de aprovação
        preview = format_campaign_preview(result)
        await msg.edit_text(
            preview,
            parse_mode="HTML",
            reply_markup=approval_keyboard(pending_id),
        )

    except BudgetExceededError as e:
        await msg.edit_text(
            f"🛑 <b>Guardrail de orçamento ativado</b>\n\n{e}",
            parse_mode="HTML",
        )

    except ComplianceBlockedError as e:
        await msg.edit_text(
            format_compliance_error(e.problemas),
            parse_mode="HTML",
        )

    except RuntimeError as e:
        # LLM Router esgotou todos os provedores
        await msg.edit_text(
            f"❌ <b>Erro no processamento</b>\n\n{e}\n\n"
            f"Verifique se pelo menos uma API Key de IA está configurada no .env.",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"[Handler] Erro inesperado: {e}", exc_info=True)
        await msg.edit_text(
            f"❌ Erro inesperado: <code>{type(e).__name__}</code>\n"
            f"Verifique os logs para detalhes.",
            parse_mode="HTML",
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa cliques nos botões inline (aprovar, rejeitar, regenerar).
    """
    if not _is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_", 1)
    action = parts[0]
    pending_id = parts[1] if len(parts) > 1 else ""

    if action == "approve":
        await _handle_approve(query, pending_id)

    elif action == "reject":
        await update_campaign_status(pending_id, "CANCELLED")
        await query.edit_message_text("❌ Campanha cancelada.")

    elif action == "regenerate":
        await query.edit_message_text("🔄 Buscando campanha para regenerar...")
        campaign = await get_pending_campaign(pending_id)
        if not campaign or not campaign.get("pipeline_result"):
            await query.edit_message_text("❌ Campanha não encontrada para regenerar.")
            return

        briefing = campaign.get("product", "")
        if not briefing:
            await query.edit_message_text("❌ Não foi possível recuperar o briefing original.")
            return

        await update_campaign_status(pending_id, "CANCELLED")
        await query.edit_message_text("⏳ Gerando novas opções de copy...")

        try:
            result = await run_campaign_pipeline(briefing)
            new_pending_id = await save_pending_campaign(result)
            preview = format_campaign_preview(result)
            await query.edit_message_text(
                preview,
                parse_mode="HTML",
                reply_markup=approval_keyboard(new_pending_id),
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Erro ao regenerar: {e}")


async def _handle_approve(query, pending_id: str):
    """Lógica de aprovação e publicação no Meta Ads."""
    await query.edit_message_text("🚀 Aprovado! Subindo campanha no Meta Ads...")

    campaign = await get_pending_campaign(pending_id)
    if not campaign:
        await query.edit_message_text("❌ Campanha não encontrada no banco de dados.")
        return

    pipeline_result = campaign.get("pipeline_result", {})
    payloads = pipeline_result.get("payloads", [])

    if not payloads:
        await query.edit_message_text("❌ Payload da campanha não encontrado.")
        return

    # Usa o primeiro payload (primeira copy)
    payload = payloads[0]
    campaign_json = payload.get("campaign", {})
    adset_json = payload.get("adset", {})
    ad_json = payload.get("ad", {})

    success, result_data = await publish_campaign_structure(
        campaign_json, adset_json, ad_json
    )

    if success:
        meta_campaign_id = result_data.get("campaign_id")
        await update_campaign_status(pending_id, "PAUSED", meta_campaign_id)

        await query.edit_message_text(
            f"✅ <b>Campanha criada com sucesso!</b>\n\n"
            f"🆔 ID Meta: <code>{meta_campaign_id}</code>\n"
            f"⚠️ Status: <b>PAUSADA</b> — ative no Gerenciador de Anúncios quando quiser.\n\n"
            f"O Analista enviará relatórios diários às 08:00.",
            parse_mode="HTML",
        )
    else:
        step = result_data.get("step_failed", "?")
        error = result_data.get("error", {})
        await query.edit_message_text(
            f"❌ <b>Falha ao publicar</b>\n\n"
            f"Passo: <code>{step}</code>\n"
            f"Erro: <code>{error.get('msg', '?')}</code>\n\n"
            f"Verifique suas credenciais Meta no .env.",
            parse_mode="HTML",
        )


async def _handle_approve_direct(msg, pending_id: str):
    """Executa aprovação direta sem interação do usuário (modo AUTO)."""
    campaign = await get_pending_campaign(pending_id)
    if not campaign:
        await msg.edit_text("❌ Erro interno: campanha não encontrada.")
        return

    pipeline_result = campaign.get("pipeline_result", {})
    payloads = pipeline_result.get("payloads", [])

    if not payloads:
        await msg.edit_text("❌ Payload não encontrado.")
        return

    payload = payloads[0]
    success, result_data = await publish_campaign_structure(
        payload.get("campaign", {}),
        payload.get("adset", {}),
        payload.get("ad", {}),
    )

    if success:
        await update_campaign_status(pending_id, "PAUSED", result_data.get("campaign_id"))
        await msg.edit_text(
            f"✅ <b>Campanha criada (modo AUTO)</b>\n"
            f"ID: <code>{result_data.get('campaign_id')}</code>\n"
            f"Status: PAUSADA",
            parse_mode="HTML",
        )
    else:
        await msg.edit_text(f"❌ Falha: {result_data.get('error', {}).get('msg', '?')}")
