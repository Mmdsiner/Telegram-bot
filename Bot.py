from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,ContextTypes,filters,CallbackQueryHandler
import sqlite3,time

TOKEN="TOKEN_BOT"
ADMIN_ID=123456789

CARD_NUMBER="6219861845998847"
CARD_NAME="محمد رنجبر"

# ================= DATABASE =================

db=sqlite3.connect("bot.db",check_same_thread=False)
cursor=db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
buys INTEGER DEFAULT 0,
score INTEGER DEFAULT 0,
inviter INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
service TEXT,
gig INTEGER,
price INTEGER,
status TEXT,
card_sent INTEGER DEFAULT 0
)
""")

db.commit()

# ================= MEMORY =================

user_state={}
last_msg={}
broadcast_mode=False

# ================= START =================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user
    inviter=None

    if context.args:
        inviter=int(context.args[0])

    cursor.execute("SELECT id FROM users WHERE id=?",(user.id,))
    if not cursor.fetchone():
        cursor.execute(
        "INSERT INTO users(id,name,inviter) VALUES(?,?,?)",
        (user.id,user.first_name,inviter)
        )
        db.commit()

    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید سرویس",callback_data="buy")],
        [InlineKeyboardButton("👤 حساب کاربری",callback_data="account")],
        [InlineKeyboardButton("🎁 دریافت جایزه",callback_data="gift")],
        [InlineKeyboardButton("📞 پشتیبانی",url="https://t.me/mmdsiner")]
    ])

    await update.message.reply_text("🚀 خوش اومدی",reply_markup=kb)

# ================= BUTTONS =================

async def buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()
    user_id=query.from_user.id
    data=query.data

    # خرید
    if data=="buy":

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("VIP",callback_data="VIP"),
             InlineKeyboardButton("CIP",callback_data="CIP")]
        ])

        await query.edit_message_text("نوع سرویس:",reply_markup=kb)

    elif data in ["VIP","CIP"]:

        user_state[user_id]=data
        price="750" if data=="VIP" else "499"

        await query.edit_message_text(
        f"هر گیگ {price} تومان\nتعداد گیگ رو ارسال کن"
        )

    elif data=="account":

        cursor.execute("SELECT buys,score FROM users WHERE id=?",(user_id,))
        buys,score=cursor.fetchone()

        link=f"https://t.me/{context.bot.username}?start={user_id}"

        await query.edit_message_text(
f"""👤 حساب

🛒 خریدها: {buys}
⭐ امتیاز: {score}

🔗 دعوت:
{link}
"""
        )

    elif data=="gift":

        cursor.execute("SELECT score FROM users WHERE id=?",(user_id,))
        score=cursor.fetchone()[0]

        if score>=10:
            cursor.execute("UPDATE users SET score=score-10 WHERE id=?",(user_id,))
            db.commit()
            await query.edit_message_text("🎁 جایزه ثبت شد")
        else:
            await query.edit_message_text("❌ امتیاز کافی نیست")

# ================= MESSAGE =================

async def handle(update:Update,context:ContextTypes.DEFAULT_TYPE):

    global broadcast_mode

    user_id=update.effective_user.id

    # ضد اسپم
    now=time.time()
    if user_id in last_msg and now-last_msg[user_id]<2:
        return
    last_msg[user_id]=now

    # پیام همگانی
    if broadcast_mode and user_id==ADMIN_ID:

        cursor.execute("SELECT id FROM users")
        users=cursor.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0],update.message.text)
            except:
                pass

        broadcast_mode=False
        await update.message.reply_text("✅ ارسال شد")
        return

    # تعداد گیگ
    if update.message.text and update.message.text.isdigit() and user_id in user_state:

        gig=int(update.message.text)

        if user_state[user_id]=="VIP":
            price=gig*750
            service="VIP"
        else:
            price=gig*499
            service="CIP"

        cursor.execute(
        "INSERT INTO orders(user_id,service,gig,price,status) VALUES(?,?,?,?,?)",
        (user_id,service,gig,price,"pending")
        )
        order_id=cursor.lastrowid
        db.commit()

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 دریافت شماره کارت",callback_data=f"card_{order_id}")]
        ])

        await update.message.reply_text(
f"""
📊 فاکتور

{service} - {gig} گیگ
💰 مبلغ: {price}

قبل پرداخت کارت بگیر
""",
reply_markup=kb
        )

        user_state.pop(user_id)

    # رسید پرداخت
    elif update.message.photo:

        cursor.execute("""
        SELECT order_id,card_sent
        FROM orders
        WHERE user_id=? AND status='pending'
        ORDER BY order_id DESC LIMIT 1
        """,(user_id,))

        row=cursor.fetchone()

        # ضد رسید فیک
        if not row or row[1]==0:
            await update.message.reply_text("❌ ابتدا شماره کارت بگیر")
            return

        order_id=row[0]

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تایید",callback_data=f"ok_{order_id}"),
             InlineKeyboardButton("❌ رد",callback_data=f"no_{order_id}")]
        ])

        await context.bot.send_message(ADMIN_ID,f"سفارش #{order_id}",reply_markup=kb)

        await context.bot.forward_message(
            ADMIN_ID,
            user_id,
            update.message.message_id
        )

        await update.message.reply_text("⏳ منتظر تایید")

# ================= ADMIN =================

async def admin(update:Update,context:ContextTypes.DEFAULT_TYPE):

    global broadcast_mode

    query=update.callback_query
    await query.answer()

    data=query.data

    # کارت جدید
    if data.startswith("card_"):

        order_id=int(data.split("_")[1])

        cursor.execute(
        "UPDATE orders SET card_sent=1 WHERE order_id=?",
        (order_id,)
        )
        db.commit()

        await query.edit_message_text(
f"""
💳 شماره کارت جدید

{CARD_NUMBER}
{CARD_NAME}

بعد پرداخت رسید ارسال کن
"""
        )

    # تایید
    elif data.startswith("ok_"):

        order_id=int(data.split("_")[1])

        cursor.execute("SELECT user_id FROM orders WHERE order_id=?",(order_id,))
        user_id=cursor.fetchone()[0]

        cursor.execute("UPDATE users SET buys=buys+1 WHERE id=?",(user_id,))
        cursor.execute("UPDATE orders SET status='done' WHERE order_id=?",(order_id,))
        db.commit()

        await context.bot.send_message(user_id,"✅ پرداخت تایید شد")
        await query.edit_message_text("✅ تایید شد")

    # رد
    elif data.startswith("no_"):

        await query.edit_message_text("❌ رد شد")

# ================= ADMIN PANEL =================

async def panel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    global broadcast_mode

    if update.effective_user.id!=ADMIN_ID:
        return

    if update.message.text=="/panel":

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 آمار",callback_data="stats")],
            [InlineKeyboardButton("📢 پیام همگانی",callback_data="broadcast")]
        ])

        await update.message.reply_text("پنل مدیریت",reply_markup=kb)

async def admin_panel_buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):

    global broadcast_mode

    query=update.callback_query
    await query.answer()

    if query.data=="stats":

        cursor.execute("SELECT COUNT(*) FROM users")
        users=cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status='done'")
        sales=cursor.fetchone()[0]

        await query.edit_message_text(
f"""
📊 آمار

👥 کاربران: {users}
💰 فروش موفق: {sales}
"""
        )

    elif query.data=="broadcast":

        broadcast_mode=True
        await query.edit_message_text("پیام رو بفرست")

# ================= RUN =================

app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("panel",panel))

app.add_handler(CallbackQueryHandler(buttons,pattern="^(buy|VIP|CIP|account|gift)$"))
app.add_handler(CallbackQueryHandler(admin_panel_buttons,pattern="^(stats|broadcast)$"))
app.add_handler(CallbackQueryHandler(admin))
app.add_handler(MessageHandler(filters.ALL,handle))

print("BOT RUNNING 24/7")
app.run_polling()
