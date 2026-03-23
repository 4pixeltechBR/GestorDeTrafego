"""
Módulo de Integração com o Telegram.

Envio de notificações de aprovação (Modo Copilot), relatórios
diários do Analista ou alertas emergenciais de Guardrails.
"""

import logging
import asyncio
from typing import Optional

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.constants import ParseMode

from config.settings import settings

logger = logging.getLogger(__name__)


class NotificationSystem:
    """Sistema central de notificações (Telegram)."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_admin_chat_id
        
        self.bot: Optional[Bot] = None
        if settings.has_telegram:
            self.bot = Bot(token=self.bot_token)
            
    async def get_bot(self) -> Optional[Bot]:
        """Inicializa e retorna o Bot Assíncrono se configurado."""
        if not self.bot and settings.has_telegram:
            self.bot = Bot(token=self.bot_token)
            
        return self.bot
            
    async def ping(self):
        """Verifica conectividade no log."""
        if not settings.has_telegram:
            logger.info("[Telegram] Notificações Desativadas (Sem TOKEN).")
            return
            
        try:
            bot = await self.get_bot()
            me = await bot.get_me()
            logger.info(f"[Telegram] \u2705 Conectado! Bot Ativo: @{me.username}")
        except TelegramError as e:
            logger.error(f"[Telegram] \u274c Falha na conexão: {e}")

    async def send_message(self, text: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
        """Envia uma mensagem de texto puro."""
        if not settings.has_telegram:
            logger.info(f"[Notificação Local] \n{text}")
            return False

        try:
            bot = await self.get_bot()
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logger.error(f"[Telegram] Erro ao enviar mensagem: {e}")
            return False

    async def ask_approval(self, campaign_name: str, brief: str, actions: dict) -> bool:
        """
        Solicita aprovação (Copilot) com botões.
        As actions ditam o que os botões farão (ex: callback_data)
        """
        if not settings.has_telegram:
            logger.info(f"[Notificação Local] [COPILOT PENDING] Campanha: {campaign_name}\nResumo: {brief}")
            return False

        keyboard = [
            [
                InlineKeyboardButton("\u2705 Aprovar", callback_data=f"approve_{actions.get('campaign_id')}"),
                InlineKeyboardButton("\u274c Rejeitar", callback_data=f"reject_{actions.get('campaign_id')}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"\u26a0\ufe0f *Aprova\u00e7\u00e3o Necess\u00e1ria*\n\n"
            f"*Campanha:* `{campaign_name}`\n\n"
            f"*Resumo da A\u00e7\u00e3o:*\n{brief}"
        )

        try:
            bot = await self.get_bot()
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return True
        except Exception as e:
            logger.error(f"[Telegram] Erro ao enviar pedido de aprovação: {e}")
            return False
            
    async def send_daily_report(self, report_text: str):
        """Envia o relatório de análise matinal."""
        message = (
            f"<b>\ud83d\udcca Relat\u00f3rio Di\u00e1rio de Tr\u00e1fego</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{report_text}"
        )
        return await self.send_message(message, parse_mode=ParseMode.HTML)


# Singleton
notifier = NotificationSystem()
