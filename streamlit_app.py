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
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180 

# --- 🎨 2. [UI] 스타일 (설명대로 코드 전 배치 및 정렬 강화) ---
st.markdown(f"""
    <style>
    /* 검색창 좌측 정렬 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ text-align: left !important; border: none !important; background-color: #f0f2f6 !important; }}

    /* 이미지 및 모든 요소 중앙 강제 정렬 */
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
        margin: 0 auto;
        display: block;
    }}
    div[data-testid="column"] {{ display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .stCaption {{ text-align: center !important; font-size: 13px !important; color: #333 !important; font-weight: 600; }}
    
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin: 25px 0 10px 0; text-align: left !important; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #ddd; border-radius: 12px; padding: 10px 18px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.07); display: inline-block; margin-right: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 및 세션 로직 (복구 완료) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("사용자 닉네임", placeholder="예: 치이카와")
    if st.button("내 기록장으로 이동") and u_input:
        st.session_state.user_id = u_input; st.query_params["user"] = u_input; st.rerun()
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
                    r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                            "url": itm["url"], "genre": itm.get("genre", "미지정"), 
                            "title": itm.get("title", "제목 없음"),
                            "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [
            {"url": i["url"], "genre": i.get("genre", "미지정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} 
            for i in st.session_state.collection
        ]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 메인 화면 & 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}님")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user_id = ""; st.query_params.clear(); st.rerun()
    if st.button("🗑️ 전체 초기화", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

st.title(f"📖 {st.session_state.user_id}의 독서 대시보드")
if st.session_state.collection:
    counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
    genre_html = "".join([f"<div class='genre-card'><b>{g}</b><br>{c}권</div>" for g, c in counts.items()])
    st.markdown(genre_html, unsafe_allow_html=True)
else:
    st.info("아직 기록된 책이 없습니다. 아래에서 책을 검색해보세요!")

st.divider()

# --- 🔍 5. 책 검색 (가로 4개 & 물리적 중앙 배치 & 날짜 선택 복구) ---
st.markdown("<span class='section-title'>🔍 책 검색 및 등록</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="책 제목이나 저자를 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        if items:
            # 4개씩 줄 단위로 생성
            for i in range(0, min(12, len(items)), 4):
                row_cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx >= len(items): break
                    item_html = items[idx]
                    
                    # 데이터 파싱
                    title_m = re.search(r'class="bo3"><b>(.*?)</b>', item_html)
                    img_m = re.search(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', item_html)
                    genre_m = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', item_html)
                    
                    if img_m:
                        title = title_m.group(1) if title_m else "제목 없음"
                        url = img_m.group()
                        genre = genre_m[-1] if genre_m else "미지정"
                        
                        with row_cols[j]:
                            # ✅ 물리적 강제 중앙 배치
                            _, inner, _ = st.columns([0.1, 0.8, 0.1])
                            with inner:
                                st.image(url)
                                st.caption(title[:14] + ".." if len(title) > 14 else title)
                                sel_genre = st.text_input("장르", value=genre, key=f"in_g_{idx}")
                                
                                # ✅ 날짜 선택 기능 복구
                                with st.expander("📅 기간 설정"):
                                    d_start = st.date_input("시작일", value=date.today(), key=f"ds_{idx}")
                                    d_end = st.date_input("종료일", value=date.today(), key=f"de_{idx}")
                                
                                b_read, b_wish = st.columns(2)
                                if b_read.button("📖 읽음", key=f"btn_r_{idx}", use_container_width=True):
                                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                                    st.session_state.collection.append({
                                        "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                        "url": url, "genre": sel_genre, "title": title,
                                        "start": d_start.isoformat(), "end": d_end.isoformat()
                                    })
                                    save_all(); st.rerun()
                                if b_wish.button("🩵 위시", key=f"btn_w_{idx}", use_container_width=True):
                                    st.session_state.wishlist.append({"url": url, "genre": sel_genre, "title": title})
                                    save_all(); st.rerun()
    except Exception as e:
        st.error(f"검색 중 오류가 발생했습니다: {e}")

# --- 📚 6. 내 서재 & 위시리스트 (이미지 렌더링 복구) ---
st.divider()
tab1, tab2 = st.tabs(["✅ 읽은 책 목록", "🩵 읽고 싶은 책"])

with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화", key="edit_read")
        lib_cols = st.columns(5)
        for idx, itm in enumerate(st.session_state.collection):
            with lib_cols[idx % 5]:
                st.image(itm["img"], use_container_width=True)
                st.caption(f"**{itm['title'][:10]}**")
                st.write(f"_{itm['genre']}_")
                st.write(f"📅 {itm.get('start')} ~ {itm.get('end')}")
                if edit_mode and st.button("❌ 삭제", key=f"del_r_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()

with tab2:
    if st.session_state.wishlist:
        edit_wish = st.toggle("삭제 모드 활성화", key="edit_wish")
        wish_cols = st.columns(5)
        for idx, itm in enumerate(st.session_state.wishlist):
            with wish_cols[idx % 5]:
                try:
                    w_r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if w_r.status_code == 200:
                        st.image(Image.open(io.BytesIO(w_r.content)), use_container_width=True)
                        st.caption(itm["title"][:12])
                    if edit_wish and st.button("🗑️ 제거", key=f"del_w_{idx}", use_container_width=True):
                        st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                except: st.write("이미지 로드 실패")