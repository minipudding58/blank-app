import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os

# 📏 인쇄 규격 설정
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🔗 URL에서 사용자 이름 가져오기 ---
query_params = st.query_params
url_user = query_params.get("user", "")

if 'user_id' not in st.session_state:
    st.session_state.user_id = url_user

# --- 🔑 로그인/접속 화면 ---
if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    st.write("나만의 닉네임을 입력하면 고유한 저장 링크가 생깁니다.")
    user_input = st.text_input("닉네임 입력 (예: 치이카와)", placeholder="영문, 숫자, 한글 모두 가능합니다.")
    
    if st.button("내 기록장 만들기/열기"):
        if user_input:
            st.query_params["user"] = user_input
            st.session_state.user_id = user_input
            st.rerun()
        else:
            st.warning("닉네임을 입력해주세요!")
    st.stop()

# 해당 사용자의 개별 데이터 파일
USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

def save_all():
    data = {
        "wishlist": st.session_state.wishlist,
        "col_urls": [item["url"] for item in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_all():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.wishlist = data.get("wishlist", [])
                st.session_state.collection = []
                for url in data.get("col_urls", []):
                    try:
                        r = requests.get(url, timeout=5)
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img, "url": url})
                    except: continue
        except: pass

if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

# --- 🎨 스타일 설정 (정렬 및 투명 배경) ---
st.markdown("""
    <style>
    .stCaption { display:none; }
    div.stButton > button p, div.stDownloadButton > button p, div[data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
    }
    div.stDownloadButton > button {
        width: 100%; background-color: transparent !important; color: #333333 !important;
        border: 1px solid #ccc !important; border-radius: 4px; height: 38px !important;
    }
    div.stButton > button { height: 38px !important; background-color: transparent !important; border: 1px solid #ccc !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("로그아웃 (다른 이름으로 접속)"):
        st.query_params.clear()
        st.session_state.user_id = ""
        st.session_state.collection = []
        st.session_state.wishlist = []
        st.rerun()

# --- ✨ 요청하신 타이틀 변경 부분 ---
# 입력한 닉네임에 따라 자동으로 제목이 바뀝니다.
st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 🔍 책 검색 엔진 ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=1