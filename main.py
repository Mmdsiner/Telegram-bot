import os
import time
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

print("TOKEN LENGTH:", len(TOKEN) if TOKEN else "NONE")

import os

TOKEN = os.getenv("TOKEN")

app = ApplicationBuilder().token(TOKEN).build()
# ================= DB =================

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id BIGINT PRIMARY KEY,
name TEXT,
buys INT DEFAULT 0,
score INT DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id SERIAL PRIMARY KEY,
user_id BIGINT,
service TEXT,
gig INT,
price INT,
status TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS discounts(
code TEXT PRIMARY KEY,
percent INT
)
""")

conn.commit()

# ================= MEMORY =================

user_state = {}
last_msg = {}
broadcast_mode = {}

# ================= MENUS =================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید", callback_data="buy")],
        [InlineKeyboardButton("👤 حساب", callback_data="account")],
        [InlineKeyboardButton("🎁 جایزه", callback_data="gift")]
    ])

# ================= START =================

async def start(update: Update, context):
    user = update.effective_user

    cursor.execute("SELECT id FROM users WHERE id=%s", (user.id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES(%s,%s,0,0)", (user.id, user.first_name))
        conn.commit()

    await update.message.reply_text("خوش آمدید", reply_markup=main_menu())

# ================= ADMIN =================

async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("💰 درآمد", callback_data="income")],
        [InlineKeyboardButton("📢 همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("🎟 کد تخفیف", callback_data="discount")]
    ]

    await update.message.reply_text("پنل مدیریت", reply_markup=InlineKeyboardMarkup(kb))

# ================= BUTTONS =================

async def buttons(update: Update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "buy":
        kb = [[InlineKeyboardButton("VIP", callback_data="VIP"),
               InlineKeyboardButton("CIP", callback_data="CIP")]]
        await q.edit_message_text("انتخاب:", reply_markup=InlineKeyboardMarkup(kb))

    elif data in ["VIP","CIP"]:
        user_state[uid] = {"service": data}
        await q.edit_message_text("گیگ رو وارد کن:")

    elif data == "account":
        cursor.execute("SELECT buys,score FROM users WHERE id=%s",(uid,))
        b,s = cursor.fetchone()
        await q.edit_message_text(f"خرید:{b}\nامتیاز:{s}")

    elif data == "stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders")
        orders = cursor.fetchone()[0]

        await q.edit_message_text(f"کاربران:{users}\nسفارش:{orders}")

    elif data == "income":
        cursor.execute("SELECT SUM(price) FROM orders WHERE status='done'")
        inc = cursor.fetchone()[0] or 0
        await q.edit_message_text(f"درآمد:{inc}")

    elif data == "broadcast":
        broadcast_mode[uid] = True
        await q.message.reply_text("متن رو بفرست")

    elif data == "discount":
        await q.message.reply_text("کد و درصد بفرست (مثال: off20 20)")

# ================= MESSAGE =================

async def handle(update: Update, context):
    uid = update.effective_user.id

    # anti spam
    now = time.time()
    if uid in last_msg and now - last_msg[uid] < 1:
        return
    last_msg[uid] = now

    # broadcast
    if uid in broadcast_mode:
        cursor.execute("SELECT id FROM users")
        for u in cursor.fetchall():
            try:
                await context.bot.send_message(u[0], update.message.text)
            except:
                pass

        await update.message.reply_text("ارسال شد")
        broadcast_mode.pop(uid)
        return

    # discount create
    if uid == ADMIN_ID and " " in update.message.text:
        try:
            code, percent = update.message.text.split()
            cursor.execute("INSERT INTO discounts VALUES(%s,%s)",(code,int(percent)))
            conn.commit()
            await update.message.reply_text("ثبت شد")
            return
        except:
            pass

    # order
    if update.message.text.isdigit() and uid in user_state:
        gig = int(update.message.text)
        service = user_state[uid]["service"]

        price = gig * (750 if service=="VIP" else 499)

        cursor.execute(
            "INSERT INTO orders(user_id,service,gig,price,status) VALUES(%s,%s,%s,%s,'pending') RETURNING order_id",
            (uid,service,gig,price)
        )
        order_id = cursor.fetchone()[0]
        conn.commit()

        await update.message.reply_text(f"سفارش ثبت شد\nمبلغ:{price}")

        user_state.pop(uid)

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT, handle))

print("RUNNING")
app.run_polling()

