import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter, defaultdict

# --- ⚙️ 1. 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")

# --- 🎨 2. [UI] CSS 스타일 (사용자 요청 레이아웃 유지) ---
st.markdown("""
    <style>
    .search-card {
        background-color: #f8f9fb;
        border-radius: 15px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 10px;
        min-height: 230px;
    }
    [data-testid="stImage"] img {
        height: 180px !important;
        width: auto !important;
        object-fit: contain !important;
    }
    .field-left { 
        width: 100%; text-align: left; font-size: 14px; 
        color: #444; font-weight: 600; margin-top: 15px; 
    }
    .no-title-text { color: rgba(0,0,0,0); font-size: 0px; user-select: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 로직 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    u_input = st.text_input("닉네임 입력")
    if st.button("입장") and u_input:
        st.session_state.user_id = u_input; st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    r = requests.get(itm["url"], timeout=5)
                    if r.status_code == 200:
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": itm["url"], "genre": itm.get("genre", "미정"), "title": itm.get("title", "제목 없음"), "start": itm.get("start"), "end": itm.get("end")})
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "genre": i.get("genre", "미정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 상단 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.divider()

# --- 🔍 5. 검색 섹션 (무조건 검색 결과 나오게 하는 로직) ---
st.markdown("### 🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        # 알라딘 검색 URL (가장 기본형으로 접속)
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(search_url, headers=headers)
        response.encoding = 'utf-8' # 한글 깨짐 방지
        html = response.text
        
        # ✅ 검색 결과 추출 (가장 확실한 이미지와 제목 패턴 사용)
        # 이미지와 제목이 쌍으로 들어있는 영역을 찾습니다.
        items = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', html)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', html)
        
        valid_books = []
        # 검색된 이미지와 제목을 매칭 (중복 제거 포함)
        seen = set()
        for i in range(min(len(items), len(titles))):
            if items[i] not in seen:
                valid_books.append({"url": items[i], "title": titles[i], "genre": "미정"})
                seen.add(items[i])

        if valid_books:
            # ✅ 가로 4열 배치 (image_f66125.png)
            for i in range(0, len(valid_books), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i + j < len(valid_books):
                        book = valid_books[i + j]
                        with cols[j]:
                            st.markdown('<div class="search-card">', unsafe_allow_html=True)
                            st.image(book["url"])
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown(f"<div class='no-title-text'>{book['title']}</div>", unsafe_allow_html=True)
                            st.markdown("<div class='field-left'>분야</div>", unsafe_allow_html=True)
                            genre = st.text_input("장르", value="미정", key=f"gen_{i+j}", label_visibility="collapsed")
                            
                            c1, c2 = st.columns(2)
                            if c1.button("📖 읽음", key=f"r_{i+j}"):
                                r_img = requests.get(book["url"]).content
                                st.session_state.collection.append({"img": Image.open(io.BytesIO(r_img)).convert("RGB"), "url": book["url"], "genre": genre, "title": book["title"]})
                                save_all(); st.rerun()
                            if c2.button("🩵 위시", key=f"w_{i+j}"):
                                st.session_state.wishlist.append({"url": book["url"], "genre": genre, "title": book["title"]})
                                save_all(); st.rerun()
        else:
            st.warning("결과를 찾을 수 없습니다. 검색어를 다시 확인해주세요.")
    except Exception as e:
        st.error(f"오류 발생: {e}")

# --- 📚 6. 내 서재 ---
st.divider()
if st.session_state.collection:
    st.markdown("### 📚 내 서재")
    for k in range(0, len(st.session_state.collection), 5):
        cols = st.columns(5)
        for idx, item in enumerate(st.session_state.collection[k:k+5]):
            with cols[idx]:
                st.image(item["img"], use_container_width=True)
                st.caption(item["title"][:10])