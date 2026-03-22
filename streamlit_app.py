import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")
TARGET_H_PX = 200 # ✅ 이미지 세로 높이 고정

# --- 🎨 [UI] 스타일 설정 (좌측 정렬 복구 + 이미지/버튼 중앙 정렬) ---
st.markdown(f"""
    <style>
    /* 검색창 빨간 테두리 제거 */
    div[data-baseweb="input"], input {{
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        background-color: #f0f2f6 !important;
    }}
    .stTextInput > div > div {{ border: none !important; }}
    
    /* ✅ 타이틀은 다시 좌측 정렬 */
    .section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 12px; 
        display: block; 
        text-align: left !important; 
    }}

    /* ✅ 이미지와 그 하단 요소(장르칸, 버튼)는 열 내에서 중앙 정렬 */
    [data-testid="stImage"] img {{
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 5px;
    }}
    
    /* 장르 입력창 및 캡션 중앙 정렬 */
    [data-testid="column"] [data-testid="stTextInput"], 
    [data-testid="column"] .stCaption,
    [data-testid="column"] [data-testid="stVerticalBlock"] > div {{
        text-align: center !important;
    }}

    /* 사이드바 스타일 유지 (절대 고정) */
    [data-testid="stSidebar"] {{ background-color: #f8f9fb; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 닉네임 설정 및 데이터 관리 (절대 유지) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

def logout():
    st.session_state.user_id = ""
    st.query_params.clear()
    st.rerun()

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("사용하실 닉네임을 입력해주세요", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
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
                            "url": itm["url"], "start": itm.get("start"), "end": itm.get("end"), "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- ⬅️ 사이드바 (절대 고정) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True): logout()
    if st.button("⚠️ 데이터 초기화", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

# --- 🏠 상단 영역 (절대 고정) ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.write(""); st.write("")

t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    st.markdown(f"<div style='text-align:center;'><div style='font-size:14px; color:#666;'>{datetime.now().year}년 누적</div><div style='font-size:40px; font-weight:bold; color:#87CEEB;'>✨{len(st.session_state.collection)}권✨</div></div>", unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_html = "".join([f"<div style='display:inline-block; margin-right:10px;' class='genre-card'><div style='font-size:12px; color:#888;'>{g}</div><div style='font-size:16px; font-weight:bold;'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div>{genre_html}</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 [수정] 도서 분야(장르) 추출 로직 강화 ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색창", placeholder="제목/저자 입력...", label_visibility="collapsed")

if q:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
    
    # ✅ 도서 결과 블록별로 더 정밀하게 장르 추출
    items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
    
    if items:
        scols = st.columns(4)
        count = 0
        for item_html in items:
            if count >= 4: break
            
            img_match = re.search(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', item_html)
            # ✅ 분야 정보 추출 로직 보강
            genre_match = re.search(r'\[<a[^>]+>([^<]+)</a>\]', item_html)
            
            if img_match:
                url = img_match.group()
                found_genre = genre_match.group(1) if genre_match else "미지정"
                
                with scols[count]:
                    st.image(url, use_container_width=True)
                    sel_genre = st.text_input("장르", value=found_genre, key=f"sg_{count}", label_visibility="collapsed")
                    
                    b_cols = st.columns(2)
                    if b_cols[0].button("📖 읽음", key=f"r_{count}", use_container_width=True):
                        img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                        save_all(); st.rerun()
                    if b_cols[1].button("🩵 위시", key=f"w_{count}", use_container_width=True):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()
                count += 1

st.divider()

# --- 📚 하단 기록 목록 ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        del_m = st.toggle("개별 삭제 모드")
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                if del_m and st.button("❌ 삭제", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                try:
                    r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    st.image(Image.open(io.BytesIO(r_img)), use_container_width=True)
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    if st.button("🗑️ 삭제", key=f"w_d_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                except: pass