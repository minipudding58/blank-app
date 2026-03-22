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

# --- 🎨 2. [UI] 스타일 (설명대로 코드 전 배치) ---
st.markdown(f"""
    <style>
    /* 검색창 및 입력창 좌측 정렬 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ text-align: left !important; border: none !important; background-color: #f0f2f6 !important; }}

    /* 이미지 및 요소 중앙 강제 정렬 */
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
    
    /* 대시보드 및 장르 카드 스타일 (스크린샷 기반) */
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; min-height: 150px; display: flex; flex-direction: column; justify-content: center; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width: 80px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; align-items: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 및 세션 로직 ---
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

# --- 🏠 4. 대시보드 (상단 가로 배치 UI 완벽 복구) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}님")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user_id = ""; st.query_params.clear(); st.rerun()
    if st.button("🗑️ 전체 초기화", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# ✅ [복구] 상단 누적 독서량 및 장르 대시보드 (가로 정렬)
dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f"""
        <div class="count-box">
            <div style="font-size:14px; color:#666; margin-bottom:5px;">{datetime.now().year}년 누적</div>
            <div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div>
        </div>
    """, unsafe_allow_html=True)

with dash_col2:
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card'><b style='font-size:16px;'>{g}</b><br><span style='color:#666;'>{c}권</span></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
    else:
        st.info("책을 등록하여 독서 통계를 확인하세요!")

st.divider()

# --- 🔍 5. 책 검색 (가로 4개 & 물리적 중앙 배치 & 날짜 선택) ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력창", placeholder="책 제목이나 저자를 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        if items:
            # ✅ 가로 4개씩 줄 단위 생성
            for i in range(0, min(12, len(items)), 4):
                row_cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx >= len(items): break
                    item_html = items[idx]
                    
                    title_m = re.search(r'class="bo3"><b>(.*?)</b>', item_html)
                    img_m = re.search(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', item_html)
                    genre_m = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', item_html)
                    
                    if img_m:
                        title = title_m.group(1) if title_m else "제목 없음"
                        url = img_m.group()
                        genre = genre_m[-1] if genre_m else "미지정"
                        
                        with row_cols[j]:
                            # ✅ 물리적 강제 중앙 배치 ([0.1, 0.8, 0.1])
                            _, inner, _ = st.columns([0.1, 0.8, 0.1])
                            with inner:
                                st.image(url)
                                st.caption(title[:14] + ".." if len(title) > 14 else title)
                                sel_genre = st.text_input("장르 수정", value=genre, key=f"search_g_{idx}", label_visibility="collapsed")
                                with st.expander("📅 기간 설정"):
                                    d_start = st.date_input("시작일", value=date.today(), key=f"search_ds_{idx}")
                                    d_end = st.date_input("종료일", value=date.today(), key=f"search_de_{idx}")
                                
                                b_read, b_wish = st.columns(2)
                                if b_read.button("📖 읽음", key=f"search_btn_r_{idx}", use_container_width=True):
                                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                                    st.session_state.collection.append({
                                        "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                        "url": url, "genre": sel_genre, "title": title,
                                        "start": d_start.isoformat(), "end": d_end.isoformat()
                                    })
                                    save_all(); st.rerun()
                                if b_wish.button("🩵 위시", key=f"search_btn_w_{idx}", use_container_width=True):
                                    st.session_state.wishlist.append({"url": url, "genre": sel_genre, "title": title})
                                    save_all(); st.rerun()
    except Exception as e:
        st.error(f"검색 오류: {e}")

# --- 📚 6. 내 서재 & 위시리스트 ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재 목록", "🩵 읽고 싶은 책"])

with tab1:
    if st.session_state.collection:
        edit_r = st.toggle("편집 모드 활성화", key="edit_read_list")
        l_cols = st.columns(5)
        for idx, itm in enumerate(st.session_state.collection):
            with l_cols[idx % 5]:
                st.image(itm["img"], use_container_width=True)
                st.caption(f"**{itm['title'][:10]}**")
                st.write(f"📅 {itm.get('end')}")
                if edit_r and st.button("❌ 삭제", key=f"lib_del_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()

with tab2:
    if st.session_state.wishlist:
        edit_w = st.toggle("편집 모드 활성화", key="edit_wish_list")
        w_cols = st.columns(5)
        for idx, itm in enumerate(st.session_state.wishlist):
            with w_cols[idx % 5]:
                try:
                    w_r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if w_r.status_code == 200:
                        st.image(Image.open(io.BytesIO(w_r.content)), use_container_width=True)
                        st.caption(itm["title"][:12])
                        if edit_w and st.button("🗑️ 제거", key=f"wish_del_{idx}", use_container_width=True):
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                except: st.write("이미지 로드 실패")