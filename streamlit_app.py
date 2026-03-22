import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os

# 📏 설정 (A4 고화질 & 스티커 40mm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 💾 데이터 관리 ---
DATA_FILE = "my_reading_data.json"
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

def save_all():
    data = {
        "wishlist": st.session_state.wishlist,
        "col_urls": [item["url"] for item in st.session_state.collection]
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_all():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.wishlist = data.get("wishlist", [])
                st.session_state.collection = []
                for url in data.get("col_urls", []):
                    r = requests.get(url, timeout=5)
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": url})
        except: pass

if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

# CSS: 찌꺼기 텍스트 투명화
st.markdown("<style>.stCaption { color: rgba(0,0,0,0) !important; }</style>", unsafe_allow_html=True)

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 (안정화 버전) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

def search_books(q):
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    # 이미지와 제목을 가져오는 가장 원초적이고 확실한 방법
    imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
    return [{"url": u} for u in imgs[:8]]

if query:
    results = search_books(query)
    if results:
        cols = st.columns(4)
        for i, book in enumerate(results):
            with cols[i % 4]:
                st.image(book['url'], use_container_width=True)
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"s_{i}"):
                    r = requests.get(book['url'])
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": book['url']})
                    save_all(); st.rerun()
                if c2.button("💛 위시", key=f"w_{i}"):
                    st.session_state.wishlist.append({"url": book['url'], "done": False})
                    save_all(); st.rerun()
    else:
        st.error("검색 결과가 없습니다. 제목을 확인해 주세요!")

st.divider()
left, right = st.columns(2)

# --- 🖨️ 인쇄판 (PDF & 개별삭제) ---
with left:
    st.header("🖨️ 인쇄용 스티커 판")
    if st.session_state.collection:
        col_btn = st.columns(2)
        if col_btn[0].button("🗑️ 전체 비우기"):
            st.session_state.collection = []; save_all(); st.rerun()
        del_mode = col_btn[1].toggle("개별 삭제 모드")

        if del_mode:
            dcols = st.columns(4)
            for idx, itm in enumerate(st.session_state.collection):
                with dcols[idx % 4]:
                    st.image(itm['img'], use_container_width=True)
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
        else:
            # A4 캔버스 생성
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120
            for itm in st.session_state.collection:
                img = itm['img']
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 120:
                    x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            
            st.image(sheet, use_container_width=True)
            # PDF 저장 버튼
            pdf_buf = io.BytesIO()
            sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button("📄 고화질 PDF 다운로드", pdf_buf.getvalue(), "books.pdf", "application/pdf")

# --- 📚 위시리스트 (아이콘 하단 배치) ---
with right:
    st.header("📚 위시리스트")
    wcols = st.columns(3)
    for i, item in enumerate(st.session_state.wishlist):
        with wcols[i % 3]:
            with st.container(border=True):
                st.image(item['url'], use_container_width=True)
                ic1, ic2 = st.columns(2)
                if ic1.button("⚪" if not item['done'] else "✅", key=f"chk_{i}"):
                    st.session_state.wishlist[i]['done'] = not item['done']; save_all(); st.rerun()
                if ic2.button("🗑️", key=f"dw_{i}"):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()