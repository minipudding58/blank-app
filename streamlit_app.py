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

# --- 🎨 2. [UI] CSS 스타일 ---
st.markdown(f"""
    <style>
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ 
        text-align: left !important; border: none !important; 
        background-color: #f0f2f6 !important; border-radius: 10px !important;
    }}
    .search-card {{
        background-color: #f8f9fb; border-radius: 15px; padding: 20px;
        display: flex; flex-direction: column; align-items: center; 
        justify-content: center; margin-bottom: 10px; min-height: 230px; width: 100%;
    }}
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important; width: auto !important;
        object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }}
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 10px; text-align: center; min-width: 80px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; }}
    .genre-subtitle {{ font-size: 18px !important; font-weight: 800 !important; border-bottom: 3px solid #87CEEB; padding-bottom: 5px; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 ---
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
                            "url": itm["url"], "genre": itm.get("genre", "미정")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "genre": i.get("genre", "미정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 사이드바 ---
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.divider()
    if st.button("🔥 내 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 🏠 5. 상단 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f'<div class="count-box"><div style="font-size:14px; color:#666;">누적 기록</div><div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)
with dash_col2:
    if st.session_state.collection:
        st.markdown("<div style='font-size:15px; font-weight:700;'>분야별 통계</div>", unsafe_allow_html=True)
        counts = Counter([itm.get("genre", "미정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card'><b>{g}</b><br><span style='color:#666;'>{c}권</span></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
st.divider()

# --- 🔍 6. 검색 섹션 (하얀 박스 완전 차단 로직) ---
st.markdown("### 🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        html = res.text
        
        # ✅ 하얀 빈 박스 완벽 차단 로직 ✅
        # 검색 결과 본문('ss_book_box' 클래스) 안에 'cover' 단어가 포함된 <img> 태그만 추출합니다.
        # 이미지 태그를 포함하지 않는 빈 레이아웃(하얀 박스)은 여기서 모두 걸러집니다.
        imgs = re.findall(r'<div[^>]*class="ss_book_box".*?src="(https://image\.aladin.co.kr/product/\d+/\d+/cover[^"]+)"', html, re.DOTALL)
        
        # 중복 제거
        imgs = list(dict.fromkeys(imgs))

        if imgs:
            for i in range(0, min(12, len(imgs)), 4):
                cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx < len(imgs):
                        img_url = imgs[idx]
                        with cols[j]:
                            st.markdown('<div class="search-card">', unsafe_allow_html=True)
                            st.image(img_url)
                            st.markdown('</div>', unsafe_allow_html=True)
                            g_input = st.text_input("장르", value="미정", key=f"s_gen_{idx}", label_visibility="collapsed")
                            
                            b_r, b_w = st.columns(2)
                            if b_r.button("📖 읽음", key=f"s_br_{idx}", use_container_width=True):
                                r = requests.get(img_url)
                                img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                                st.session_state.collection.append({"img": img_obj, "url": img_url, "genre": g_input})
                                save_all(); st.rerun()
                            if b_w.button("🩵 위시", key=f"s_bw_{idx}", use_container_width=True):
                                st.session_state.wishlist.append({"url": img_url, "genre": g_input})
                                save_all(); st.rerun()
        else:
            st.warning("결과를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"오류: {e}")

# --- 📚 7. 내 서재 목록 ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재", "🩵 위시리스트"])
with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화")
        grouped = defaultdict(list)
        for idx, itm in enumerate(st.session_state.collection):
            grouped[itm.get('genre', '미정')].append((idx, itm))
        
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='genre-subtitle'>{g_name}</div>", unsafe_allow_html=True)
            for k in range(0, len(g_items), 5):
                cols = st.columns(5)
                for c_idx, (orig_idx, itm) in enumerate(g_items[k:k+5]):
                    with cols[c_idx]:
                        st.image(itm["img"], use_container_width=True)
                        if edit_mode and st.button("❌", key=f"del_{orig_idx}"):
                            st.session_state.collection.pop(orig_idx); save_all(); st.rerun()