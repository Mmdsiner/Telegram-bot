from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="خرید سرویس", callback_data="buy")],
        [InlineKeyboardButton(text="پشتیبانی", callback_data="support")]
    ])

def plan_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="معمولی", callback_data="plan_normal")],
        [InlineKeyboardButton(text="ویژه", callback_data="plan_vip")]
    ])

def payment_actions(payment_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید", callback_data=f"approve_{payment_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{payment_id}")
        ]
    ])
