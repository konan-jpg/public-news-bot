import requests
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from config import TOPICS, EXCLUDE_KEYWORDS, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, get_now
from database import is_duplicate, save_article
import logging

# 기본 수집 기간: 14일 (336시간)로 변경!
def search_google_news(query, hours=336):
    results = []
    try:
        # when:14d (최근 14일)
        encoded_query = quote(query + " when:14d")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

        feed = feedparser.parse(url)
        
        now_utc = datetime.now(timezone.utc)
        cutoff_utc = now_utc - timedelta(hours=hours)

        logging.info(f"검색어 [{query}] 수집 시작... (기준: {hours}시간 전)")

        for entry in feed.entries[:30]:
            try:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except (TypeError, AttributeError):
                continue

            if pub_date < cutoff_utc:
                continue

            title = entry.title
            link = entry.link

            if any(exc in title for exc in EXCLUDE_KEYWORDS):
                continue

            if is_duplicate(link):
                continue

            from config import TIMEZONE
            pub_date_kst = pub_date.astimezone(TIMEZONE)

            results.append({
                'title': title,
                'url': link,
                'press': entry.source.title if hasattr(entry, 'source') else 'Google News',
                'published_at': pub_date_kst.strftime('%Y-%m-%d %H:%M'),
                'query': query,
                'topic': ''
            })
            
    except Exception as e:
        logging.error(f"Google News 검색 오류 ({query}): {e}")

    return results

def search_naver_news(query, hours=336):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return []

    results = []
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        params = {
            "query": query,
            "display": 30,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        cutoff_dt = get_now() - timedelta(hours=hours)

        for item in data.get('items', []):
            title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            link = item['link']
            
            try:
                pub_date_str = item['pubDate']
                pub_date_dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S +0900")
                pub_date_dt = pub_date_dt.replace(tzinfo=get_now().tzinfo)
                
                if pub_date_dt < cutoff_dt:
                    continue
            except Exception:
                continue

            if any(exc in title for exc in EXCLUDE_KEYWORDS):
                continue

            if is_duplicate(link):
                continue

            results.append({
                'title': title,
                'url': link,
                'press': '네이버뉴스',
                'published_at': pub_date_dt.strftime('%Y-%m-%d %H:%M'),
                'query': query,
                'topic': ''
            })
    except Exception as e:
        print(f"네이버 검색 오류 ({query}): {e}")

    return results

def collect_all_news(hours=336):
    """전체 주제 뉴스 수집 및 저장"""
    all_articles = []

    for topic_name, topic_config in TOPICS.items():
        queries = topic_config["queries"]
        required_words = topic_config.get("required", [])

        for query in queries:
            articles = search_google_news(query, hours)
            for article in articles:
                if required_words:
                    if not any(rw in article['title'] for rw in required_words):
                        continue
                
                article['topic'] = topic_name
                save_article(article)
                all_articles.append(article)

            if NAVER_CLIENT_ID:
                articles_naver = search_naver_news(query, hours)
                for article in articles_naver:
                    if required_words:
                        if not any(rw in article['title'] for rw in required_words):
                            continue
                    
                    article['topic'] = topic_name
                    save_article(article)
                    all_articles.append(article)

    all_articles.sort(key=lambda x: x['published_at'], reverse=True)
    return all_articles
