import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TOPICS, get_now
from news_collector import collect_all_news

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def escape_html(text):
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 뉴스 알림 봇입니다.\n\n"
        "/news - 최신 뉴스 브리핑\n"
    )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 최신 뉴스를 수집하고 있습니다... (약 10초 소요)")
    try:
        articles = collect_all_news()
        logging.info(f"수집된 뉴스 개수: {len(articles)}")

        if not articles:
            await update.message.reply_text("❌ 수집된 최신 뉴스가 없습니다.")
            return

        grouped = {}
        for a in articles:
            t = a['topic']
            if t not in grouped:
                grouped[t] = []
            grouped[t].append(a)

        report = "<b>📰 뉴스 보고서</b>\n\n"
        for topic, items in grouped.items():
            report += f"<b>📌 {escape_html(topic)}</b>\n"
            for idx, item in enumerate(items[:20], 1):
                title = escape_html(item['title'])
                press = escape_html(item['press'])
                pub = escape_html(item['published_at'])
                url = item['url']
                report += f'{idx}. <a href="{url}">{title}</a>\n'
                report += f'   <i>{press} | {pub}</i>\n\n'
            report += "\n"

        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                await update.message.reply_text(report[x:x+4000], parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text(report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"뉴스 수집 중 오류: {e}")
        await update.message.reply_text(f"❌ 오류 발생: {e}")

async def scheduled_news(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    try:
        articles = collect_all_news()
        if not articles:
            await context.bot.send_message(chat_id=chat_id, text="❌ 금일 수집된 주요 뉴스가 없습니다.")
            return

        grouped = {}
        for a in articles:
            t = a['topic']
            if t not in grouped:
                grouped[t] = []
            grouped[t].append(a)

        report = "<b>📰 정기 뉴스 보고서</b>\n\n"
        for topic, items in grouped.items():
            report += f"<b>📌 {escape_html(topic)}</b>\n"
            for idx, item in enumerate(items[:20], 1):
                title = escape_html(item['title'])
                press = escape_html(item['press'])
                pub = escape_html(item['published_at'])
                url = item['url']
                report += f'{idx}. <a href="{url}">{title}</a>\n'
                report += f'   <i>{press} | {pub}</i>\n\n'
            report += "\n"

        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                await context.bot.send_message(chat_id=chat_id, text=report[x:x+4000], parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await context.bot.send_message(chat_id=chat_id, text=report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"스케줄링 실행 중 오류: {e}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))

    job_queue = application.job_queue
    if job_queue:
        from config import TIMEZONE, TELEGRAM_CHAT_ID
        import datetime
        for t in [datetime.time(hour=8, minute=0, tzinfo=TIMEZONE), datetime.time(hour=15, minute=0, tzinfo=TIMEZONE)]:
            job_queue.run_daily(scheduled_news, t, chat_id=TELEGRAM_CHAT_ID, name=str(t))
        logging.info("스케줄러 설정 완료")

    application.run_polling()
