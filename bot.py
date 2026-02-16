import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TOPICS
from database import init_db, cleanup_old_articles
from news_collector import collect_all_news, score_article

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    await update.message.reply_text(
        "🗞️ 뉴스봇입니다.\n\n"
        "명령어:\n"
        "/뉴스 - 최근 24시간 뉴스 보고서\n"
        "/help - 도움말"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어"""
    topics_list = "\n".join([f"- {name}" for name in TOPICS.keys()])
    await update.message.reply_text(
        f"📋 수집 주제:\n{topics_list}\n\n"
        "💡 /뉴스 명령어로 최근 24시간 뉴스를 확인하세요."
    )


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """뉴스 수집 및 보고서 전송"""
    await update.message.reply_text("🔍 뉴스를 수집하고 있습니다...")

    articles = collect_all_news(hours=24)

    if not articles:
        await update.message.reply_text("📭 최근 24시간 이내 새로운 뉴스가 없습니다.")
        return

    grouped = {}
    for article in articles:
        grouped.setdefault(article["topic"], []).append(article)

    report = "📰 <b>뉴스 보고서</b> (최근 24시간)\n\n"

    for topic_name, topic_articles in grouped.items():
        keywords = TOPICS[topic_name]
        sorted_articles = sorted(
            topic_articles,
            key=lambda x: score_article(x, keywords),
            reverse=True
        )[:5]

        report += f"<b>📌 {topic_name}</b>\n"
        for i, article in enumerate(sorted_articles, 1):
            title = article["title"]
            url = article["url"]
            press = article.get("press", "")
            pub_date = article.get("published_at", "")

            report += f'{i}. <a href="{url}">{title}</a>\n'
            report += f"   <i>{press} | {pub_date}</i>\n\n"

        report += "\n"

    report += f"✅ 총 {len(articles)}건 수집\n"

    if len(report) > 4000:
        chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await update.message.reply_text(report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    cleanup_old_articles()


def main():
    """봇 시작"""
    init_db()

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 환경변수를 설정하세요.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("뉴스", news_command))
    application.add_handler(CommandHandler("news", news_command))

    logger.info("봇이 시작되었습니다...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
