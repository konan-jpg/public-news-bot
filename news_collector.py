import requests
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from config import TOPICS, EXCLUDE_KEYWORDS, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, get_now
from database import is_duplicate, save_article


def search_google_news(query, hours=24):
    """구글 뉴스 RSS 검색 (UTC 기준 필터링)"""
    results = []
    try:
        encoded_query = quote(query + " when:1d")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

        feed = feedparser.parse(url)

        # UTC 기준으로 통일하여 비교 (Timezone 오류 방지)
        now_utc = datetime.now(timezone.utc)
        cutoff_utc = now_utc - timedelta(hours=hours)

        for entry in feed.entries[:20]:
            try:
                # published_parsed는 UTC 기준 time.struct_time입니다.
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except (TypeError, AttributeError):
                continue  # 날짜 파싱 실패 시 건너뜀
            
            # 24시간 지난 기사는 과감히 패스
            if pub_date < cutoff_utc:
                continue

            title = entry.title
            link = entry.link

            if any(exc in title for exc in EXCLUDE_KEYWORDS):
                continue

            if is_duplicate(link):
                continue

            # 표시용으로는 KST로 변환
            from config import TIMEZONE
            pub_date_kst = pub_date.astimezone(TIMEZONE)

            results.append({
                'title': title,
                'url': link,
                'press': entry.source.title if hasattr(entry, 'source') else 'Google News',
                'published_at': pub_date_kst.strftime('%Y-%m-%d %H:%M'),
                'query': query
            })
    except Exception as e:
        print(f"Google News 검색 오류 ({query}): {e}")

    return results


def search_naver_news(query, hours=24):
    """네이버 뉴스 검색 API"""
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
            "display": 20,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        for item in data.get('items', []):
            title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            link = item['link']
            pub_date_str = item['pubDate']

            if any(exc in title for exc in EXCLUDE_KEYWORDS):
                continue

            if is_duplicate(link):
                continue

            results.append({
                'title': title,
                'url': link,
                'press': '네이버뉴스',
                'published_at': pub_date_str,
                'query': query
            })
    except Exception as e:
        print(f"네이버 검색 오류 ({query}): {e}")

    return results


def collect_all_news(hours=24):
    """전체 주제 뉴스 수집 (2차 필터링 포함)"""
    all_articles = []

    for topic_name, topic_config in TOPICS.items():
        queries = topic_config["queries"]
        required_words = topic_config.get("required", [])

        for query in queries:
            articles = search_google_news(query, hours)
            for article in articles:
                # 2차 필터링: 제목에 필수 단어가 포함되어 있는지 확인
                title = article['title']
                if required_words and not any(rw in title for rw in required_words):
                    continue  # 필수 단어가 하나도 없으면 건너뜀

                article['topic'] = topic_name
                save_article(article)
                all_articles.append(article)

            if NAVER_CLIENT_ID:
                articles_naver = search_naver_news(query, hours)
                for article in articles_naver:
                    title = article['title']
                    if required_words and not any(rw in title for rw in required_words):
                        continue

                    article['topic'] = topic_name
                    save_article(article)
                    all_articles.append(article)

    return all_articles


def score_article(article, keywords):
    """기사 중요도 점수 계산"""
    score = 0
    title = article['title'].lower()

    for kw in keywords:
        if kw.lower() in title:
            score += 10

    important_words = ["갈등", "이전", "반발", "통합", "폐합", "협의", "주민", "국방부", "군"]
    for word in important_words:
        if word in title:
            score += 5

    return score
