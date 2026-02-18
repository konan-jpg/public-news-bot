import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TOPICS, get_now
from news_collector import collect_all_news
import sys

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def escape_markdown(text):
    """마크다운 특수문자 이스케이프"""
    if not text: return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 뉴스 알림 봇입니다.\n\n"
        "/news - 최신 뉴스 브리핑 (최대 20개)\n"
        "/test - 테스트 모드 (DB 저장 안 함)"
    )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자가 /news 입력 시 실행"""
    await update.message.reply_text("🔍 최신 뉴스를 수집하고 있습니다... (약 10초 소요)")
    
    try:
        # 뉴스 수집 (최근 24시간)
        logging.info("뉴스 수집 시작...")
        articles = collect_all_news(hours=24)
        logging.info(f"수집된 뉴스 개수: {len(articles)}")
        
        if not articles:
            await update.message.reply_text("❌ 수집된 최신 뉴스가 없습니다. (서버 시간/필터링 문제 가능성)")
            return

        report = "📰 *정기 뉴스 보고서* (최근 24시간)\n\n"
        grouped_articles = {}
        
        for article in articles:
            topic = article['topic']
            if topic not in grouped_articles:
                grouped_articles[topic] = []
            grouped_articles[topic].append(article)

        for topic, items in grouped_articles.items():
            report += f"📌 *{escape_markdown(topic)}*\n"
            for idx, item in enumerate(items[:20], 1):
                title = escape_markdown(item['title'])
                press = escape_markdown(item['press'])
                pub_date = escape_markdown(item['published_at'])
                url = item['url']
                
                try:
                    report += f"{idx}\\. [{title}]({url}) \\- {press}\n"
                    report += f"   _{press} \\| {pub_date}_\n\n"
                except Exception:
                    continue
            report += "\n"

        # 나눠서 보내기
        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                await update.message.reply_text(report[x:x+4000], parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        else:
            await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"뉴스 수집 중 오류: {e}")
        await update.message.reply_text(f"❌ 오류 발생: {e}")

async def scheduled_news(context: ContextTypes.DEFAULT_TYPE):
    """정기 스케줄링 실행 (08:00, 15:00)"""
    job = context.job
    chat_id = job.chat_id
    
    logging.info("스케줄링된 뉴스 수집 시작...")
    
    try:
        articles = collect_all_news(hours=24)
        
        if not articles:
            await context.bot.send_message(chat_id=chat_id, text="❌ 금일 수집된 주요 뉴스가 없습니다.")
            return

        report = "📰 *정기 뉴스 보고서*\n\n"
        grouped_articles = {}
        for article in articles:
            topic = article['topic']
            if topic not in grouped_articles:
                grouped_articles[topic] = []
            grouped_articles[topic].append(article)

        for topic, items in grouped_articles.items():
            report += f"📌 *{escape_markdown(topic)}*\n"
            for idx, item in enumerate(items[:20], 1):
                title = escape_markdown(item['title'])
                press = escape_markdown(item['press'])
                pub_date = escape_markdown(item['published_at'])
                url = item['url']
                
                report += f"{idx}\\. [{title}]({url}) \\- {press}\n"
                report += f"   _{press} \\| {pub_date}_\n\n"
            report += "\n"

        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                await context.bot.send_message(chat_id=chat_id, text=report[x:x+4000], parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        else:
            await context.bot.send_message(chat_id=chat_id, text=report, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"스케줄링 실행 중 오류: {e}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 명령어 핸들러 (영어만 가능!)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))

    # 스케줄러 설정 (JobQueue)
    job_queue = application.job_queue
    
    if job_queue:
        from config import TIMEZONE, TELEGRAM_CHAT_ID
        import datetime
        
        target_times = [
            datetime.time(hour=8, minute=0, tzinfo=TIMEZONE),
            datetime.time(hour=15, minute=0, tzinfo=TIMEZONE)
        ]
        
        for t in target_times:
            job_queue.run_daily(scheduled_news, t, chat_id=TELEGRAM_CHAT_ID, name=str(t))
            
        logging.info("스케줄러 설정 완료")
    
    application.run_polling()
