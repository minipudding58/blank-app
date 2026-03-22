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

# 1. 태극기 '건(☰)' 모양 버튼은 Streamlit 기본 사이드바 기능을 활용합니다.
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide", initial_sidebar_state="expanded")

# --- 🔗 URL 닉네임 인식 시스템 ---
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

# --- 💾 데이터 관리 함수 ---
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
                        r = requests.get(url, timeout=5)
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img, "url": url})
                    except: continue
        except: pass

if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

# --- 🎨 4번 문제 해결: CSS 스타일 (텍스트 크기 및 줄바꿈 방지) ---
st.markdown("""
    <style>
    .stCaption { display:none; }
    /* 버튼 내부 텍스트 최적화 */
    div.stButton > button p, div.stDownloadButton > button p {
        font-size: 13px !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    /* 버튼 박스 크기 조절 */
    div.stButton > button {
        height: 38px !important;
        padding: 0px 5px !important;
    }
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 1번 해결: 사이드바 구성 (접기 기능 포함) ---
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        st.session_state.user_id = ""; st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()
    st.write("---")
    st.warning("⚠️ 데이터 삭제 버튼")
    if st.button("🔥 내 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE):
            os.remove(USER_DATA_FILE)
            st.query_params.clear()
            st.session_state.user_id = ""; st.session_state.collection = []; st.session_state.wishlist = []; st.rerun()

st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 🔍 책 검색 및 2번 해결: 버튼명 변경 ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")
if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=10)
        imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        if imgs:
            cols = st.columns(4)
            for i, img_url in enumerate(imgs[:8]):
                with cols[i % 4]:
                    st.image(img_url, use_container_width=True)
                    c1, c2 = st.columns(2)
                    # 2번 해결: '스티커'를 '읽은 책'으로 변경
                    if c1.button("📖 읽은 책", key=f"s_{i}"):
                        r = requests.get(img_url, headers=headers)
                        img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img_obj, "url": img_url})
                        save_all(); st.rerun()
                    if c2.button("🩵 위시", key=f"w_{i}"):
                        if not any(d['url'] == img_url for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"url": img_url, "done": False})
                            save_all(); st.rerun()
    except: st.error("검색 에러")

st.divider()
left_col, right_col = st.columns(2)

# --- 🖨️ 3번 해결: 세 항목 정렬 ---
with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        # 3번 해결: 컬럼 비중을 조절하여 한 줄로 정렬
        b1, b2, b3 = st.columns([1, 1, 1.2])
        with b1:
            if st.button("🗑️ 비우기", use_container_width=True):
                st.session_state.collection = []; save_all(); st.rerun()
        with b2:
            del_mode = st.toggle("개별 삭제", value=False)
        with b3:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120
            for itm in st.session_state.collection:
                img = itm['img']
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 120: x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            pdf_buf = io.BytesIO(); sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button("📥 PDF 다운로드", pdf_buf.getvalue(), f"{st.session_state.user_id}_books.pdf", "application/pdf", use_container_width=True)
        
        st.write("---")
        if del_mode:
            dcols = st.columns(4)
            for idx, itm in enumerate(st.session_state.collection):
                with dcols[idx % 4]:
                    st.image(itm['img'], use_container_width=True)
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
        else:
            st.image(sheet, use_container_width=True)
    else: st.info("기록이 없습니다.")

# --- 📚 4번 해결: 위시리스트 버튼 크기 및 텍스트 맞춤 ---
with right_col:
    st.header("🩵 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                with st.container(border=True):
                    st.image(item['url'], use_container_width=True)
                    ic1, ic2 = st.columns(2)
                    label = "✅ 완료" if item['done'] else "📖 선택"
                    if ic1.button(label, key=f"chk_{i}", use_container_width=True):
                        item['done'] = not item['done']
                        if item['done']:
                            r = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"})
                            img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                            st.session_state.collection.append({"img": img_obj, "url": item['url']})
                        save_all(); st.rerun()
                    if ic2.button("🗑️ 삭제", key=f"dw_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()