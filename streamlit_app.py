import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date

# ==========================================
# ⚙️ 1. 페이지 설정 및 데이터 관리
# ==========================================
st.set_page_config(page_title="나의 독서 기록장", layout="wide", initial_sidebar_state="collapsed")

if 'user_id' not in st.session_state:
    if "user" in st.query_params: 
        st.session_state.user_id = st.query_params["user"]
    else:
        st.title("📖 독서 기록장")
        u_input = st.text_input("닉네임을 입력하세요")
        if st.button("입장하기") and u_input:
            st.session_state.user_id = u_input
            st.query_params["user"] = u_input
            st.rerun()
        st.stop()

USER_DATA_PATH = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                st.session_state.wishlist = loaded.get("wishlist", [])
                for item in loaded.get("collection", []):
                    try:
                        resp = requests.get(item["url"], timeout=5).content
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(resp)).convert("RGB"),
                            "url": item["url"],
                            "start": item.get("start"),
                            "end": item.get("end"),
                            "genre": item.get("genre", "미지정")
                        })
                    except: continue
        except: pass

def commit_changes():
    payload = {
        "wishlist": st.session_state.wishlist,
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i["genre"]} for i in st.session_state.collection]
    }
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

# ==========================================
# 🎨 2. CSS 스타일 (탭 디자인 & 버튼 정렬 핵심)
# ==========================================
st.markdown("""
    <style>
    /* 탭 디자인: 폰트 키우고 볼드 처리, 선택 시 하단 바 강조 */
    button[data-baseweb="tab"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #1E1E1E !important; /* 선택 여부 상관없이 진한 색 유지 */
        padding: 12px 40px !important;
        border: none !important;
    }
    
    /* 선택된 탭 하단 막대기 (길고 여유롭게) */
    div[data-baseweb="tab-highlight"] {
        background-color: #FF4B4B !important; 
        height: 5px !important;
        border-radius: 10px !important;
    }

    /* 버튼 수평 정렬 강제 */
    div[data-testid="stHorizontalBlock"] {
        gap: 10px !important;
        align-items: center !important;
    }

    /* 버튼 크기 고정 및 텍스트 정렬 */
    .stButton button {
        width: 100% !important;
        height: 42px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        font-size: 15px !important;
    }

    /* 삭제 버튼 전용 스타일 */
    .del-btn button {
        border: 1px solid #FF6B6B !important;
        color: #FF6B6B !important;
        background-color: white !important;
    }

    /* 타이틀 및 이미지 스타일 */
    .main-title { font-size: 42px; font-weight: 900; margin-bottom: 40px; color: #1E1E1E; }
    [data-testid="stImage"] img { border-radius: 15px; height: 240px !important; object-fit: contain !important; border: 1px solid #F0F0F0; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔍 3. 상단 제목 및 검색 기능
# ==========================================
st.markdown(f"<div class='main-title'>{st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

search_q = st.text_input("🔍 제목이나 저자로 책을 찾아보세요", placeholder="예: 불편한 편의점")
if search_q:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_q}").text
        imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res)))[:4]
        
        if imgs:
            cols = st.columns(4)
            for i, url in enumerate(imgs):
                with cols[i]:
                    st.image(url)
                    # 검색 결과 버튼 수평 정렬
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("📖 읽음", key=f"s_add_{i}"):
                            img_raw = requests.get(url).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(img_raw)).convert("RGB"),
                                "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": "미지정"
                            })
                            commit_changes(); st.rerun()
                    with b2:
                        if st.button("🩵 위시", key=f"s_wish_{i}"):
                            st.session_state.wishlist.append({"url": url, "genre": "미지정"})
                            commit_changes(); st.rerun()
    except: st.error("검색 중 오류가 발생했습니다.")

st.divider()

# ==========================================
# 📚 4. 메인 탭 영역 (내 서재 & 위시리스트)
# ==========================================
# 요구하신 대로 탭 스타일 적용
tab_lib, tab_wish = st.tabs(["내 서재", "위시리스트"])

with tab_lib:
    edit_mode = st.toggle("편집 모드 활성화")
    if st.session_state.collection:
        lib_cols = st.columns(4)
        for i, itm in enumerate(st.session_state.collection):
            with lib_cols[i % 4]:
                st.image(itm["img"])
                if edit_mode:
                    new_genre = st.text_input("장르", itm['genre'], key=f"edit_g_{i}", label_visibility="collapsed")
                    # 편집 모드 버튼 수평 정렬
                    eb1, eb2 = st.columns(2)
                    with eb1:
                        if st.button("저장", key=f"sv_btn_{i}"):
                            st.session_state.collection[i]["genre"] = new_genre
                            commit_changes(); st.rerun()
                    with eb2:
                        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"del_btn_{i}"):
                            st.session_state.collection.pop(i)
                            commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{itm['genre']}**")
                    st.caption(f"완독일: {itm['end']}")
    else:
        st.info("아직 기록된 책이 없습니다. 위에서 검색해 보세요!")

with tab_wish:
    if st.session_state.wishlist:
        wish_cols = st.columns(4)
        for i, itm in enumerate(st.session_state.wishlist):
            with wish_cols[i % 4]:
                st.image(itm['url'])
                # 위시리스트 버튼 수평 정렬
                wb1, wb2 = st.columns(2)
                with wb1:
                    if st.button("📖 완료", key=f"w_done_{i}"):
                        img_raw = requests.get(itm['url']).content
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(img_raw)).convert("RGB"),
                            "url": itm['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": itm['genre']
                        })
                        st.session_state.wishlist.pop(i)
                        commit_changes(); st.rerun()
                with wb2:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ 삭제", key=f"w_del_{i}"):
                        st.session_state.wishlist.pop(i)
                        commit_changes(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("위시리스트가 비어 있습니다.")