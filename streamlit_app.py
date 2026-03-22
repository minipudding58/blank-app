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

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide", initial_sidebar_state="expanded")

# --- 🔗 URL 닉네임 인식 ---
query_params = st.query_params
url_user = query_params.get("user", "")
if 'user_id' not in st.session_state:
    st.session_state.user_id = url_user

# --- 🔑 입장 화면 ---
if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    user_input = st.text_input("나만의 닉네임 입력", placeholder="닉네임을 입력해주세요.")
    if st.button("기록장 열기"):
        if user_input:
            st.query_params["user"] = user_input
            st.session_state.user_id = user_input
            st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

# --- 💾 데이터 관리 ---
def save_all():
    data = {"wishlist": st.session_state.wishlist, "col_urls": [item["url"] for item in st.session_state.collection]}
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
                        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code == 200:
                            img = Image.open(io.BytesIO(r.content)).convert("RGB")
                            st.session_state.collection.append({"img": img, "url": url})
                    except: continue
        except: pass

if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

st.markdown("""
    <style>
    div.stButton > button p, div.stDownloadButton > button p { font-size: 13px !important; white-space: nowrap !important; }
    div.stButton > button { height: 38px !important; padding: 0px 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 사이드바 ---
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        st.session_state.user_id = ""; st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()
    st.write("---")
    if st.button("🔥 내 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear()
        st.session_state.user_id = ""; st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 🔍 검색 엔진 (먼작귀 3권 엑박 해결 로직) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 먼작귀")
if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        
        # 이미지 URL 추출 패턴 개선 (먼작귀 3권의 특수 패턴 대응)
        raw_imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover\d*[^"\'\s>]+', res.text)
        
        # 중복 제거 및 유효성 검사
        imgs = []
        for url in list(dict.fromkeys(raw_imgs)):
            if 'cover' in url and url not in imgs:
                imgs.append(url)

        if imgs:
            cols = st.columns(4)
            for i, img_url in enumerate(imgs[:8]):
                # 유효한 이미지인지 한 번 더 확인
                try:
                    with cols[i % 4]:
                        st.image(img_url, use_container_width=True)
                        c1, c2 = st.columns(2)
                        if c1.button("📖 읽은 책", key=f"s_{i}"):
                            r = requests.get(img_url, headers=headers)
                            img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                            st.session_state.collection.append({"img": img_obj, "url": img_url})
                            save_all(); st.rerun()
                        if c2.button("🩵 위시", key=f"w_{i}"):
                            if not any(d['url'] == img_url for d in st.session_state.wishlist):
                                st.session_state.wishlist.append({"url": img_url, "done": False})
                                save_all(); st.rerun()
                except: continue
    except: st.error("검색 결과를 가져오는 중 문제가 발생했습니다.")

st.divider()
left_col, right_col = st.columns(2)

# --- 🖨️ 왼쪽: 읽은 책 모음 ---
with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        b1, b2, b3 = st.columns([1, 1, 1.2])
        with b1:
            if st.button("🗑️ 비우기", use_container_width=True):
                st.session_state.collection = []; save_all(); st.rerun()
        with b2: del_mode = st.toggle("개별 삭제")
        with b3:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120
            for itm in st.session_state.collection:
                img = itm['img']
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 120: x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            pdf_buf = io.BytesIO(); sheet.save(pdf_buf, format="