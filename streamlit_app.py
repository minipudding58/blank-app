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
TARGET_H_PX = 180 

# --- 🎨 2. [UI] CSS 스타일 (사용자 기획 완벽 고정) ---
st.markdown(f"""
    <style>
    /* 입력창 좌측 정렬 및 배경색 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ text-align: left !important; border: none !important; background-color: #f0f2f6 !important; }}

    /* 도서 이미지 및 캡션 중앙 정렬 */
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
    
    /* ✅ 복구: "분야별(장르별) 통계" 소제목 스타일 */
    .genre-title {{ 
        font-size: 15px !important; 
        color: #555; 
        font-weight: 700; 
        margin: 5px 0 5px 0; 
        text-align: left !important; 
    }}
    
    /* 대시보드 및 장르 카드 레이아웃 */
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; min-height: 150px; display: flex; flex-direction: column; justify-content: center; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width: 90px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; align-items: center; }}
    
    /* ✅ 내 서재 탭 장르별 중제목 스타일 (에세이 (2권) 등) */
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
    
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin: 25px 0 10px 0; text-align: left !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 로직 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("사용자 닉네임 입력", placeholder="예: 치이카와")
    if st.button("내 기록장 입장") and u_input:
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
        "collection": [{"url": i["url"], "genre": i.get("genre", "미지정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 상단 대시보드 레이아웃 ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}님")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user_id = ""; st.query_params.clear(); st.rerun()
    if st.button("🗑️ 전체 데이터 초기화", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

# ✅ 복구: 타이틀 및 공백 두 줄 (image_f5e8e6.png 근거)
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.markdown("<br><br>", unsafe_allow_html=True) 

dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f'<div class="count-box"><div style="font-size:14px; color:#666; margin-bottom:5px;">{datetime.now().year}년 누적</div><div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)

with dash_col2:
    if st.session_state.collection:
        # ✅ 복구: "분야별(장르별) 통계" 문구 (image_f5ddbe.png 근거)
        st.markdown("<div class='genre-title'>분야별(장르별) 통계</div>", unsafe_allow_html=True)
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card'><b>{g}</b><br><span style='color:#666;'>{c}권</span></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 도서 검색 섹션 (가로 4개 정렬) ---
st.markdown("<span class='section-title'>🔍 책 검색 및 추가</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력창", placeholder="추가할 책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        if items:
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
                        url = img_m.group(); genre = genre_m[-1] if genre_m else "미지정"
                        with row_cols[j]:
                            _, inner, _ = st.columns([0.1, 0.8, 0.1])
                            with inner:
                                st.image(url); st.caption(title[:14])
                                sel_genre = st.text_input("장르 수정", value=genre, key=f"search_g_{idx}")
                                with st.expander("📅 독서 기간"):
                                    ds = st.date_input("시작일", value=date.today(), key=f"ds_{idx}")
                                    de = st.date_input("종료일", value=date.today(), key=f"de_{idx}")
                                b_r, b_w = st.columns(2)
                                if b_r.button("📖 읽음", key=f"btn_r_{idx}", use_container_width=True):
                                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "genre": sel_genre, "title": title, "start": ds.isoformat(), "end": de.isoformat()})
                                    save_all(); st.rerun()
                                if b_w.button("🩵 위시", key=f"btn_w_{idx}", use_container_width=True):
                                    st.session_state.wishlist.append({"url": url, "genre": sel_genre, "title": title}); save_all(); st.rerun()
    except: pass

# --- 📚 6. 내 서재 및 위시리스트 (탭 구조 유지) ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재 (분야별 목록)", "🩵 위시리스트"])

with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화", key="toggle_edit")
        
        # ✅ 장르별 그룹화 로직 (image_f5ddbe.png 근거)
        grouped = defaultdict(list)
        for idx, item in enumerate(st.session_state.collection):
            grouped[item.get('genre', '미지정')].append((idx, item))
        
        # ✅ 장르별 섹션 출력
        for g_name, g_items in grouped.items():
            # ✅ 복구: 분야별 중제목 (예: 에세이 (2권))
            st.markdown(f"<div class='genre-subtitle'>{g_name} ({len(g_items)}권)</div>", unsafe_allow_html=True)
            
            # 한 줄에 5개씩 배치
            item_rows = [g_items[k:k+5] for k in range(0, len(g_items), 5)]
            for row in item_rows:
                cols = st.columns(5)
                for c_idx, (orig_idx, itm) in enumerate(row):
                    with cols[c_idx]:
                        st.image(itm["img"], use_container_width=True)
                        st.caption(f"**{itm['title'][:10]}**")
                        st.write(f"<span style='font-size:12px; color:#666;'>📅 {itm.get('end')}</span>", unsafe_allow_html=True)
                        if edit_mode and st.button("❌ 삭제", key=f"del_lib_{orig_idx}", use_container_width=True):
                            st.session_state.collection.pop(orig_idx); save_all(); st.rerun()

with tab2:
    if st.session_state.wishlist:
        w_edit = st.toggle("제거 모드 활성화", key="toggle_wish")
        w_cols = st.columns(5)
        for idx, itm in enumerate(st.session_state.wishlist):
            with w_cols[idx % 5]:
                try:
                    w_r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if w_r.status_code == 200:
                        st.image(Image.open(io.BytesIO(w_r.content)), use_container_width=True)
                        st.caption(itm["title"][:10])
                        if w_edit and st.button("🗑️ 제거", key=f"del_wish_{idx}", use_container_width=True):
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                except: pass