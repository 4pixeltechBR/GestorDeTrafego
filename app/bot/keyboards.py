"""
keyboards.py — Teclados inline do Telegram (botões de aprovação).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def approval_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    """Botões de aprovação para uma campanha pendente."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aprovar e subir", callback_data=f"approve_{pending_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"reject_{pending_id}"),
        ],
        [
            InlineKeyboardButton("🔄 Gerar novas opções", callback_data=f"regenerate_{pending_id}"),
        ],
    ])


def copy_selector_keyboard(pending_id: str, num_copies: int) -> InlineKeyboardMarkup:
    """Permite ao usuário escolher qual copy usar antes de subir."""
    buttons = []
    for i in range(num_copies):
        buttons.append([
            InlineKeyboardButton(
                f"Usar Opção {i + 1}",
                callback_data=f"selectcopy_{pending_id}_{i}"
            )
        ])
    buttons.append([
        InlineKeyboardButton("❌ Cancelar tudo", callback_data=f"reject_{pending_id}")
    ])
    return InlineKeyboardMarkup(buttons)
