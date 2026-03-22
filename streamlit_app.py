import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter, defaultdict

# --- ⚙️ 1. 기본 설정 (절대 고정) ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180 

# --- 🎨 2. [UI] CSS 스타일 (사용자 요청 레이아웃 100% 반영) ---
st.markdown(f"""
    <style>
    /* 입력창 디자인 및 텍스트 정렬 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ 
        text-align: left !important; 
        border: none !important; 
        background-color: #f0f2f6 !important; 
        border-radius: 10px !important;
    }}

    /* ✅ 검색 결과 카드: 회색 배경 + 이미지 중앙 정렬 (image_f64a5b.png 반영) */
    .search-card {{
        background-color: #f8f9fb;
        border-radius: 15px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center !important; 
        justify-content: center;
        margin-bottom: 10px;
        min-height: 220px;
    }}

    /* 이미지 중앙 정렬 강제 고정 (image_f646db.png 반영) */
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        margin: 0 auto !important;
        display: block !important;
    }}
    
    /* ✅ '분야' 라벨 및 입력창 좌측 정렬 (image_f655da.png 반영) */
    .field-left {{ 
        width: 100%; 
        text-align: left !important; 
        font-size: 14px; 
        color: #444; 
        font-weight: 600; 
        margin-top: 15px; 
        margin-bottom: 5px;
    }}

    /* '제목 없음' 텍스트 투명화 처리 */
    .no-title-text {{
        color: rgba(0,0,0,0) !important;
        font-size: 0px !important;
        line-height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        user-select: none;
    }}

    /* 상단 통계 섹션 소제목 (image_f646db.png 반영) */
    .genre-title {{ 
        font-size: 15px !important; 
        color: #555; 
        font-weight: 700; 
        margin: 5px 0 5px 0; 
        text-align: left !important; 
    }}
    
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; min-height: 150px; display: flex; flex-direction: column; justify-content: center; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width: 90px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; align-items: center; }}
    
    /* 내 서재 장르별 소제목 스타일 */
    .genre-subtitle {{ 
        font-size: 20px !important; 
        font-weight: 800 !important; 
        color: #333; 
        margin: 35px 0 15px 0; 
        border-bottom: 3px solid #87CEEB; 
        padding-bottom: 5px; 
        width: 100%; 
        text-align: left !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 로직 (생략 없이 유지) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임", placeholder="예: 치이카와")
    if st.button("입장") and u_input:
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
                            "url": itm["url"], "genre": itm.get("genre", "미정"), 
                            "title": itm.get("title", "제목 없음"), 
                            "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "genre": i.get("genre", "미정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 상단 대시보드 (image_f646db.png 반영) ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.markdown("<br><br>", unsafe_allow_html=True) 

dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f'<div class="count-box"><div style="font-size:14px; color:#666; margin-bottom:5px;">{datetime.now().year}년 누적</div><div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)

with dash_col2:
    if st.session_state.collection:
        st.markdown("<div class='genre-title'>분야별(장르별) 통계</div>", unsafe_allow_html=True)
        counts = Counter([itm.get("genre", "미정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card'><b>{g}</b><br><span style='color:#666;'>{c}권</span></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 검색 섹션 (image_f66125.png 그림판 4분할 수평 나열 요청 반영) ---
st.markdown("### 🔍 책 검색")
q = st.text_input("검색창", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        if items:
            # ✅ 가로로 4개씩 배치 (사용자가 빨간색으로 그린 image_f66125.png 구조)
            for i in range(0, min(8, len(items)), 4): 
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
                        found_genre = genre_m[-1] if genre_m else "미정"
                        
                        with row_cols[j]:
                            # ✅ 이미지 중앙 정렬 및 회색 배경 카드 (image_f64a5b.png 스타일)
                            st.markdown(f'<div class="search-card">', unsafe_allow_html=True)
                            st.image(url)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 제목 투명화 (내부 데이터용)
                            st.markdown(f"<div class='no-title-text'>{title}</div>", unsafe_allow_html=True)
                            
                            # ✅ '분야' 텍스트 및 입력창 좌측 정렬 (image_f655da.png 스타일)
                            st.markdown("<div class='field-left'>분야</div>", unsafe_allow_html=True)
                            sel_genre = st.text_input("분야수정", value=found_genre, label_visibility="collapsed", key=f"s_gen_{idx}")
                            
                            # 기간 설정 (생략 없음)
                            with st.expander("📅 기간 설정"):
                                ds = st.date_input("시작", value=date.today(), key=f"s_ds_{idx}")
                                de = st.date_input("종료", value=date.today(), key=f"s_de_{idx}")
                            
                            b_r, b_w = st.columns(2)
                            if b_r.button("📖 읽음", key=f"s_br_{idx}", use_container_width=True):
                                img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                                st.session_state.collection.append({
                                    "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                    "url": url, "genre": sel_genre, "title": title, 
                                    "start": ds.isoformat(), "end": de.isoformat()
                                })
                                save_all(); st.rerun()
                            if b_w.button("🩵 위시", key=f"s_bw_{idx}", use_container_width=True):
                                st.session_state.wishlist.append({"url": url, "genre": sel_genre, "title": title})
                                save_all(); st.rerun()
    except: pass

# --- 📚 6. 하단 목록 (내 서재 / 위시리스트 탭) ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재 (분야별 목록)", "🩵 위시리스트"])

with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화", key="lib_edit_full")
        grouped = defaultdict(list)
        for idx, item in enumerate(st.session_state.collection):
            grouped[item.get('genre', '미정')].append((idx, item))
        
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='genre-subtitle'>{g_name} ({len(g_items)}권)</div>", unsafe_allow_html=True)
            for k in range(0, len(g_items), 5):
                cols = st.columns(5)
                for c_idx, (orig_idx, itm) in enumerate(g_items[k:k+5]):
                    with cols[c_idx]:
                        st.image(itm["img"], use_container_width=True)
                        st.caption(f"**{itm['title'][:10]}**")
                        if edit_mode and st.button("❌", key=f"del_lib_{orig_idx}", use_container_width=True):
                            st.session_state.collection.pop(orig_idx); save_all(); st.rerun()

with tab2:
    if st.session_state.wishlist:
        w_edit = st.toggle("목록 제거 활성화", key="wish_edit_full")
        for k in range(0, len(st.session_state.wishlist), 5):
            cols = st.columns(5)
            for idx, itm in enumerate(st.session_state.wishlist[k:k+5]):
                with cols[idx]:
                    try:
                        w_r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                        if w_r.status_code == 200:
                            st.image(Image.open(io.BytesIO(w_r.content)), use_container_width=True)
                            st.caption(itm["title"][:10])
                            if w_edit and st.button("🗑️", key=f"del_wish_{idx}", use_container_width=True):
                                st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                    except: pass