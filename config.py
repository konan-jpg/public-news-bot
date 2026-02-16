import os
from datetime import datetime
from zoneinfo import ZoneInfo

# 텔레그램
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 네이버 오픈API(선택)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# 시간대
TIMEZONE = ZoneInfo("Asia/Seoul")

# 수집 주제/키워드
TOPICS = {
    "한국국방연구원": [
        "한국국방연구원 이전",
        "KIDA 이전",
        "한국국방연구원 혁신도시",
    ],
    "공공기관_통합폐합": [
        "공공기관 통합",
        "공공기관 폐합",
        "공공기관 기능조정",
        "공공기관 개편",
    ],
    "훈련장_군사시설_갈등": [
        "훈련장 갈등",
        "사격장 주민 반발",
        "군사시설 이전",
        "군공항 이전 갈등",
    ],
    "해상풍력_국방갈등": [
        "해상풍력 국방부",
        "풍력단지 군 작전",
        "해상풍력 레이더 갈등",
    ],
}

# 제목에 아래 단어가 들어가면 제외(노이즈 제거용)
EXCLUDE_KEYWORDS = ["야구", "축구", "농구", "골프", "연예", "드라마", "예능", "아이돌"]


def get_now():
    return datetime.now(TIMEZONE)
