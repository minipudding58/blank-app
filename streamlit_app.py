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
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 [UI] 빨간 테두리 및 포커스 효과 완전 제거 ---
st.markdown("""
    <style>
    /* 모든 입력창의 기본 테두리와 포커스 시 발생하는 빨간 테두리 제거 */
    div[data-baseweb="input"] {
        border: none !important;
        box-shadow: none !important;
        background-color: #f0f2f6 !important; /* 약간의 회색 배경으로 구분감 부여 */
    }
    input {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput > div > div {
        border: none !important;
    }
    /* 버튼 및 기타 요소 간격 조정 */
    .block-container { padding-top: 1.5rem !important; }
    .section-title { font-size: 18px !important; font-weight: bold !important; margin-bottom: 12px; display: block; }
    /* 이미지 높이 200px 고정 */
    [data-testid="stImage"] img { height: 200px !important; object-fit: contain !important; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 닉네임 설정 및 로그아웃 기능 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

def logout():
    st.session_state.user_id = ""
    st.query_params.clear()
    st.rerun()

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("사용하실 닉네임을 입력해주세요 (테두리 없음)", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

# --- 💾 데이터 관리 ---
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
                            "url": itm["url"],
                            "start": itm.get("start"), 
                            "end": itm.get("end"), 
                            "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 메인 화면 헤더 ---
h_left, h_right = st.columns([5, 1])
with h_left:
    st.title(f"📖 {st.session_state.user_id}의 독서 기록")
with h_right:
    if st.button("로그아웃"): logout()

st.write("") # 타이틀 하단 공백

# --- 📊 상단 독서 현황 ---
t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    st.markdown(f"""
        <div style='text-align:center;'>
            <div style='font-size:14px; color:#666;'>{datetime.now().year}년 누적</div>
            <div style='font-size:40px; font-weight:bold; color:#87CEEB;'>✨{len(st.session_state.collection)}권✨</div>
        </div>
    """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_html = "".join([
            f"<div style='display:inline-block; margin-right:10px; background:#f8f9fa; border:1px solid #eee; border-radius:8px; padding:5px 12px; text-align:center;'>"
            f"<div style='font-size:12px; color:#888;'>{g}</div>"
            f"<div style='font-size:16px; font-weight:bold;'>{c}권</div></div>" 
            for g, c in counts.items()
        ])
        st.markdown(f"<div>{genre_html}</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 책 검색 및 장르 자동 연동 ---
st.markdown("<span class='section-title'>🔍 책 검색 (장르 자동 연동)</span>", unsafe_allow_html=True)
q = st.text_input("검색창 (테두리 없음)", placeholder="제목/저자 입력...", label_visibility="collapsed")

if q:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    
    # 이미지와 장르 정보 추출
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # ✅ 알라딘 검색 결과의 카테고리 [ ] 안의 텍스트를 정밀 추출
    raw_genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
    
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                # 추출된 장르 중 해당 순번의 장르 매칭 (실패 시 미지정)
                found_genre = raw_genres[i] if i < len(raw_genres) else "미지정"
                sel_genre = st.text_input("장르 확인/수정", value=found_genre, key=f"sg_{i}", label_visibility="collapsed")
                
                b_cols = st.columns(2)
                if b_cols[0].button("📖 읽음", key=f"r_{i}", use_container_width=True):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                        "url": url, 
                        "start": date.today().isoformat(), 
                        "end": date.today().isoformat(), 
                        "genre": sel_genre
                    })
                    save_all(); st.rerun()
                if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                    save_all(); st.rerun()

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
                if del_m:
                    if st.button("❌ 삭제", key=f"dc_{idx}", use_container_width=True):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                try:
                    r_img = requests.get(item['url'], timeout=5, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.image(Image.open(io.BytesIO(r_img)), use_container_width=True)
                except: st.write("이미지 로드 실패")
                st.caption(f"예정 장르: {item.get('genre', '미지정')}")
                if st.button("🗑️ 삭제", key=f"w_d_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()