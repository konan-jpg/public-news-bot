import os
from datetime import datetime
from zoneinfo import ZoneInfo

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = "8531743936:AAE8xqKeLbd5NForWW9OPWZ3W_8XFsOQOms"
TELEGRAM_CHAT_ID = "595782938"

# 네이버 뉴스 API 키 (전체 교체 시 이 부분이 반영됨)
NAVER_CLIENT_ID = "OduExCNDSQXiWuJoLChK"
NAVER_CLIENT_SECRET = "uuO13_poBK"

# 시간대
TIMEZONE = ZoneInfo("Asia/Seoul")

# 수집 주제/키워드
# queries: 검색에 사용할 키워드
# required: 기사 제목에 이 단어 중 최소 1개는 반드시 포함되어야 함 (2차 필터링)
TOPICS = {
    "한국국방연구원": {
        "queries": [
            "한국국방연구원 이전",
            "KIDA 이전",
            "한국국방연구원 혁신도시",
        ],
        "required": ["한국국방연구원", "KIDA", "국방연구원"],
    },
    "공공기관_통합폐합": {
        "queries": [
            "공공기관 통합",
            "공공기관 폐합",
            "공공기관 기능조정",
            "공공기관 개편",
        ],
        "required": ["공공기관"],
    },
    "훈련장_군사시설_갈등": {
        "queries": [
            "훈련장 갈등",
            "사격장 주민 반발",
            "군사시설 이전 주민",
            "군공항 이전 갈등",
        ],
        "required": ["훈련장", "사격장", "군사시설", "군공항", "사격"],
    },
    "해상풍력_국방갈등": {
        "queries": [
            "해상풍력 국방부",
            "풍력단지 군 작전",
            "해상풍력 레이더 갈등",
        ],
        "required": ["해상풍력", "풍력단지"],
    },
    "국방통계": {
        "queries": [
            "국방통계",
            "군사통계",
            "국방 통계자료",
        ],
        "required": ["국방", "군사"],
    },
}

# 제목에 아래 단어가 들어가면 제외(노이즈 제거용)
EXCLUDE_KEYWORDS = [
    # 스포츠
    "야구", "축구", "농구", "골프", "배구", "테니스", "격투기",
    "호날두", "맨유", "손흥민", "토트넘", "리버풀", "프리미어리그",
    "메시", "바르셀로나", "레알마드리드", "챔피언스리그",
    "KBO", "MLB", "NBA", "EPL", "K리그",
    # 연예
    "연예", "드라마", "예능", "아이돌", "방탄소년단", "BTS",
    # 주식/경제 노이즈
    "주가", "코스피", "코스닥", "증시", "상장",
]

def get_now():
    return datetime.now(TIMEZONE)
