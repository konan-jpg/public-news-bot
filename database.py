import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import TIMEZONE

DB_FILE = "news_bot.db"


def init_db():
    """DB 초기화 (테이블 생성)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT UNIQUE,
            title TEXT,
            url TEXT,
            press TEXT,
            published_at TEXT,
            topic TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_url(url):
    """URL 해싱 (중복 체크용)"""
    clean_url = url.split('?')[0]
    return hashlib.md5(clean_url.encode()).hexdigest()


def is_duplicate(url):
    """24시간 이내 동일 URL 존재 여부"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    url_h = hash_url(url)
    cutoff = (datetime.now(TIMEZONE) - timedelta(hours=24)).isoformat()

    cursor.execute("""
        SELECT COUNT(*) FROM articles
        WHERE url_hash = ? AND created_at > ?
    """, (url_h, cutoff))

    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def save_article(article):
    """기사 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO articles (url_hash, title, url, press, published_at, topic, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            hash_url(article['url']),
            article['title'],
            article['url'],
            article.get('press', ''),
            article.get('published_at', ''),
            article.get('topic', ''),
            datetime.now(TIMEZONE).isoformat()
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def cleanup_old_articles():
    """7일 이상 오래된 기사 삭제"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cutoff = (datetime.now(TIMEZONE) - timedelta(days=7)).isoformat()
    cursor.execute("DELETE FROM articles WHERE created_at < ?", (cutoff,))
    conn.commit()
    conn.close()
