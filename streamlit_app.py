import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from collections import Counter

# --- ⚙️ 1. 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180

# --- 🎨 2. [UI] 핵심 스타일 ---
st.markdown(f"""
    <style>
    div[data-baseweb="input"], input {{ 
        border: none !important; background-color: #f0f2f6 !important; border-radius: 10px !important;
    }}
    .search-card {{
        background-color: #f8f9fb; border-radius: 15px; padding: 15px;
        display: flex; flex-direction: column; align-items: center; 
        justify-content: center; margin-bottom: 10px; min-height: 200px;
    }}
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important; width: auto !important;
        object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }}
    .count-box {{ text-align: center; padding: 20px; background: #f8f9fb; border-radius: 15px; border: 1px solid #eee; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 (긴급 복구 로직) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임 입력", placeholder="예: 치이카와")
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
                    # ✅ 핵심 복구: 데이터 형식이 'genre'를 포함하든 안 하든 상관없이 불러옴
                    try:
                        r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code == 200:
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                                "url": itm["url"]
                            })
                    except: continue
        except: pass

def save_all():
    # 저장할 때도 가장 단순한 구조로 저장해서 충돌 방지
    data = {
        "wishlist": [{"url": i["url"]} for i in st.session_state.wishlist], 
        "collection": [{"url": i["url"]} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 사이드바 ---
with st.sidebar:
    st.write(f"👤 **{st.session_state.user_id}** 님")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    st.divider()
    if st.button("🔥 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# --- 🏠 5. 메인 화면 ---
st.title(f"📖 {st.session_state.user_id}의 서재")
st.markdown(f'<div class="count-box"><div style="font-size:32px; font-weight:bold; color:#87CEEB;">✨ {len(st.session_state.collection)}권 읽음 ✨</div></div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 6. 검색 (정밀 필터 적용) ---
q = st.text_input("🔍 책 제목 검색 (예: 먼작귀)", placeholder="검색어를 입력하세요", label_visibility="collapsed") 

if q:
    try:
        url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res.encoding = 'utf-8'
        
        # ✅ 'cover'와 'product'가 명확히 포함된 진짜 이미지 주소만 추출 (빈 박스 방지)
        imgs = re.findall(r'src="(https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover(?:200|500)[^"]+)"', res.text)
        imgs = list(dict.fromkeys(imgs))

        if imgs:
            cols = st.columns(4)
            for i, img_url in enumerate(imgs[:12]):
                with cols[i % 4]:
                    st.markdown('<div class="search-card">', unsafe_allow_html=True)
                    st.image(img_url)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    b1, b2 = st.columns(2)
                    if b1.button("📖 읽음", key=f"r_{i}", use_container_width=True):
                        r = requests.get(img_url)
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": img_url})
                        save_all(); st.rerun()
                    if b2.button("🩵 위시", key=f"w_{i}", use_container_width=True):
                        st.session_state.wishlist.append({"url": img_url})
                        save_all(); st.rerun()
        else:
            st.warning("이미지를 찾을 수 없습니다.")
    except: st.error("검색 중 오류 발생")

# --- 📚 7. 내 서재 목록 ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재", "🩵 위시"])
with tab1:
    if st.session_state.collection:
        del_m = st.toggle("삭제 모드")
        for i in range(0, len(st.session_state.collection), 5):
            cols = st.columns(5)
            for j in range(5):
                idx = i + j
                if idx < len(st.session_state.collection):
                    itm = st.session_state.collection[idx]
                    with cols[j]:
                        st.image(itm["img"], use_container_width=True)
                        if del_m and st.button("❌", key=f"d_{idx}"):
                            st.session_state.collection.pop(idx); save_all(); st.rerun()
    else: st.info("기록이 없습니다.")

with tab2:
    if st.session_state.wishlist:
        for i in range(0, len(st.session_state.wishlist), 5):
            wcols = st.columns(5)
            for j in range(5):
                idx = i + j
                if idx < len(st.session_state.wishlist):
                    with wcols[j]:
                        st.image(st.session_state.wishlist[idx]['url'], use_container_width=True)
                        if st.button("🗑️", key=f"wd_{idx}"):
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()