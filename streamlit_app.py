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

# --- 🎨 2. [UI] 스타일 (검색창 좌측 정렬 및 중앙 배치 제어) ---
st.markdown(f"""
    <style>
    /* ✅ 검색창 좌측 정렬 고정 */
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ text-align: left !important; border: none !important; background-color: #f0f2f6 !important; }}

    /* 이미지 크기 고정 및 둥근 모서리 */
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        border-radius: 8px;
    }}

    /* 입력창 및 텍스트 중앙 정렬 */
    [data-testid="column"] input {{ text-align: center !important; }}
    .stCaption {{ text-align: center !important; width: 100% !important; }}
    
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin: 20px 0 10px 0; text-align: left !important; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 10px; padding: 8px 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    [data-testid="stSidebar"] {{ background-color: #f8f9fb; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 및 세션 관리 ---
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

# --- ⬅️ 4. 사이드바 (기능 복구) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user_id = ""; st.query_params.clear(); st.rerun()
    if st.button("⚠️ 데이터 초기화", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

# --- 🏠 5. 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
c1, c2 = st.columns([1, 4])
with c1:
    st.markdown(f"<div style='text-align:center; padding-top:15px;'><div style='font-size:14px; color:#666;'>{datetime.now().year}년 누적</div><div style='font-size:42px; font-weight:bold; color:#87CEEB;'>✨{len(st.session_state.collection)}권✨</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_html = "".join([f"<div style='display:inline-block; margin: 0 10px 10px 0;' class='genre-card'><div style='font-size:11px; color:#999;'>{g}</div><div style='font-size:15px; font-weight:bold;'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div>{genre_html}</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 6. 책 검색 (물리적 중앙 배치 및 검색 결과 출력 복구) ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색창", placeholder="제목/저자 입력...", label_visibility="collapsed") 

if q:
    try:
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
        
        # 검색 결과 테이블 파싱
        items = re.findall(r'<table.*?>(.*?)</table>', res, re.DOTALL)
        
        if items:
            valid_count = 0
            for item_html in items:
                if valid_count >= 4: break # 상위 4개만 표시
                
                img_match = re.search(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', item_html)
                genre_matches = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', item_html)
                
                if img_match:
                    url = img_match.group()
                    found_genre = genre_matches[-1] if genre_matches else "미지정"
                    
                    # ✅ 물리적 중앙 정렬 배치 (1:1.5:1 비율)
                    sp_l, center, sp_r = st.columns([1, 1.5, 1])
                    with center:
                        st.image(url)
                        sel_genre = st.text_input("장르", value=found_genre, key=f"sg_{url}_{valid_count}", label_visibility="collapsed")
                        b1, b2 = st.columns(2)
                        if b1.button("📖 읽음", key=f"r_{url}_{valid_count}", use_container_width=True):
                            img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                "url": url, 
                                "start": date.today().isoformat(), 
                                "end": date.today().isoformat(), 
                                "genre": sel_genre
                            })
                            save_all(); st.rerun()
                        if b2.button("🩵 위시", key=f"w_{url}_{valid_count}", use_container_width=True):
                            st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                            save_all(); st.rerun()
                    st.divider()
                    valid_count += 1
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")

# --- 📚 7. 목록 및 삭제 (기능 복구) ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        read_del = st.toggle("개별 삭제 모드", key="tg_r")
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                st.caption(f"{itm.get('genre', '미지정')}")
                if read_del and st.button("❌ 삭제", key=f"dr_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wish_del = st.toggle("개별 삭제 모드", key="tg_w")
        wcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.wishlist):
            with wcols[idx % 3]:
                try:
                    w_img_res = requests.get(itm['url'], headers={"User-Agent": "Mozilla/5.0"})
                    if w_img_res.status_code == 200:
                        st.image(Image.open(io.BytesIO(w_img_res.content)), use_container_width=True)
                        st.caption(f"{itm.get('genre', '미지정')}")
                        if wish_del and st.button("🗑️ 삭제", key=f"dw_{idx}", use_container_width=True):
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                except: pass