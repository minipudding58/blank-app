import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date

# --- ⚙️ 1. 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180

# --- 🎨 2. [UI] CSS 스타일 (원본 레이아웃 유지) ---
st.markdown(f"""
    <style>
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ 
        text-align: left !important; border: none !important; 
        background-color: #f0f2f6 !important; border-radius: 10px !important;
    }}
    .search-card {{
        background-color: #f8f9fb; border-radius: 15px; padding: 20px;
        display: flex; flex-direction: column; align-items: center !important; 
        justify-content: center; margin-bottom: 10px; min-height: 230px; width: 100%;
    }}
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important; width: auto !important;
        object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }}
    .no-title-text {{
        color: rgba(0,0,0,0) !important; font-size: 0px !important;
        line-height: 0px !important; user-select: none;
    }}
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; display: flex; flex-direction: column; justify-content: center; }}
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
                            "url": itm["url"]
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"]} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 상단 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.markdown(f'<div class="count-box"><div style="font-size:14px; color:#666;">누적 기록</div><div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 검색 섹션 (장르 제외, 이미지 중심) ---
st.markdown("### 🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        html = res.text
        
        # 장르/제목 매칭 없이 'cover' 이미지만 추출 (가장 확실한 방법)
        imgs = re.findall(r'src="(https://image\.aladin\.co\.kr/[^"]+cover[^"]+)"', html)
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
                            
                            b_r, b_w = st.columns(2)
                            if b_r.button("📖 읽음", key=f"s_br_{idx}", use_container_width=True):
                                r = requests.get(img_url)
                                img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                                st.session_state.collection.append({"img": img_obj, "url": img_url})
                                save_all(); st.rerun()
                            if b_w.button("🩵 위시", key=f"s_bw_{idx}", use_container_width=True):
                                st.session_state.wishlist.append({"url": img_url})
                                save_all(); st.rerun()
        else:
            st.warning("검색 결과 이미지를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")

# --- 📚 6. 내 서재 목록 ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재", "🩵 위시리스트"])
with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화")
        k = 0
        for i in range(0, len(st.session_state.collection), 5):
            cols = st.columns(5)
            for j in range(5):
                idx = i + j
                if idx < len(st.session_state.collection):
                    itm = st.session_state.collection[idx]
                    with cols[j]:
                        st.image(itm["img"], use_container_width=True)
                        if edit_mode and st.button("❌", key=f"del_{idx}"):
                            st.session_state.collection.pop(idx); save_all(); st.rerun()
    else:
        st.info("아직 기록된 책이 없습니다.")

with tab2:
    if st.session_state.wishlist:
        wcols = st.columns(5)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 5]:
                st.image(item['url'], use_container_width=True)
                if st.button("🗑️", key=f"wd_{i}"):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()