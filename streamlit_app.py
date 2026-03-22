import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")
TARGET_H_PX = 200 

# --- 🎨 2. [UI] 스타일 (검색창 좌측 정렬 및 텍스트 제어) ---
st.markdown(f"""
    <style>
    /* ✅ 검색창 무조건 좌측 정렬 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ text-align: left !important; border: none !important; background-color: #f0f2f6 !important; }}

    /* 이미지 크기 고정 및 중앙 정렬 보조 */
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }}

    /* 입력창 및 캡션 중앙 정렬 */
    [data-testid="column"] input {{ text-align: center !important; }}
    .stCaption {{ text-align: center !important; width: 100% !important; }}
    
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin: 20px 0 10px 0; text-align: left !important; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 10px; padding: 8px 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input; st.query_params["user"] = u_input; st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f); st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                            "url": itm["url"], "start": itm.get("start"), "end": itm.get("end"), "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.divider()

# --- 🔍 5. 책 검색 (물리적 공간 배치를 통한 중앙 정렬 강제) ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색창", placeholder="제목/저자 입력...", label_visibility="collapsed") 

if q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        if items:
            for item_html in items[:4]:
                img_match = re.search(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', item_html)
                # ✅ 장르 추출 정규식 강화 (미지정 해결)
                genre_matches = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', item_html)
                
                if img_match:
                    url = img_match.group()
                    found_genre = genre_matches[-1] if genre_matches else "미지정"
                    
                    # ✅ [핵심] 양옆에 빈 컬럼을 두어 중앙 정렬 강제
                    spacer_left, center_col, spacer_right = st.columns([1, 1.5, 1])
                    with center_col:
                        st.image(url) # 물리적으로 화면 중앙에 위치
                        sel_genre = st.text_input("장르", value=found_genre, key=f"sg_{url}", label_visibility="collapsed")
                        b_cols = st.columns(2)
                        if b_cols[0].button("📖 읽음", key=f"r_{url}", use_container_width=True):
                            img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                            save_all(); st.rerun()
                        if b_cols[1].button("🩵 위시", key=f"w_{url}", use_container_width=True):
                            st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()
                    st.divider() # 검색 결과 단위 구분
    except: pass

# --- 📚 6. 하단 목록 ---
st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
if st.session_state.collection:
    list_cols = st.columns(5)
    for idx, itm in enumerate(st.session_state.collection):
        with list_cols[idx % 5]:
            st.image(itm["img"], use_container_width=True)
            st.caption(f"{itm.get('genre', '미지정')}")