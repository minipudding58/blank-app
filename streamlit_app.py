import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os

# 📏 인쇄 설정 (300 DPI 기준 A4 사이즈)
DPI = 300
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)
TARGET_H_PX = int((40 / 25.4) * DPI) # 스티커 높이 40mm

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 💾 데이터 저장/불러오기 로직 ---
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # URL 기반 데이터 복구
            st.session_state.wishlist = data.get("wishlist", [])
            # 이미지는 URL로 저장했다가 다시 로드
            if "collection_urls" in data:
                st.session_state.collection = []
                for url in data["collection_urls"]:
                    r = requests.get(url)
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": url})
    else:
        st.session_state.collection = []
        st.session_state.wishlist = []

def save_data():
    data = {
        "wishlist": st.session_state.wishlist,
        "collection_urls": [item["url"] for item in st.session_state.collection]
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 초기 실행 시 데이터 로드
if 'collection' not in st.session_state:
    load_data()

# CSS 주입
st.markdown("""
    <style>
    .stCaption { color: rgba(0,0,0,0) !important; height: 0px; margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (원본 유지) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

def get_data_original(search_query):
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        img_urls = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', res.text)
        for i in range(min(len(img_urls), 8)):
            t = titles[i] if i < len(titles) else "제목 없음"
            results.append({"title": t, "url": img_urls[i]})
    except: pass
    return results

if query:
    books = get_data_original(query)
    if books:
        st.subheader(f"📍 '{query}' 검색 결과")
        cols = st.columns(4)
        for idx, book in enumerate(books):
            with cols[idx % 4]:
                st.image(book['url'], use_container_width=True)
                st.caption(book['title'])
                
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                    r = requests.get(book['url'])
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": book['url']})
                    save_data()
                    st.toast("인쇄판 추가!")
                if c2.button("💛 위시", key=f"wi_{idx}"):
                    if not any(d['url'] == book['url'] for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"url": book['url'], "done": False})
                        save_data()
                        st.toast("위시리스트 추가!")

st.divider()
l_col, r_col = st.columns([1, 1])

# --- 🖨️ 왼쪽: 인쇄용 스티커 판 (PDF 기능 추가) ---
with l_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        if st.button("🗑️ 전체 비우기"):
            st.session_state.collection = []
            save_data()
            st.rerun()
            
        # A4 시트 생성 (고화질)
        sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
        x, y = 120, 120
        for item in st.session_state.collection:
            img = item["img"]
            ratio = TARGET_H_PX / float(img.size[1])
            img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
            if x + img_res.size[0] > A4_W_PX - 120:
                x = 120; y += TARGET_H_PX + 40
            sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
        
        st.image(sheet, use_container_width=True, caption="인쇄 미리보기")
        
        # 📄 PDF 저장 로직 (깨짐 방지)
        pdf_buf = io.BytesIO()
        sheet.save(pdf_buf, format="PDF", resolution=300.0)
        st.download_button(
            label="📥 고화질 PDF로 저장하기 (인쇄용)",
            data=pdf_buf.getvalue(),
            file_name="my_book_stickers.pdf",
            mime="application/pdf"
        )

# --- 📚 오른쪽: 위시리스트 ---
with r_col:
    st.header("📚 위시리스트")
    cols_wish = st.columns(3)
    for i, item in enumerate(st.session_state.wishlist):
        with cols_wish[i % 3]:
            with st.container(border=True):
                st.image(item['url'], use_container_width=True)
                c_icon1, c_icon2 = st.columns(2)
                if c_icon1.button("⚪" if not item['done'] else "✅", key=f"chk_{i}"):
                    st.session_state.wishlist[i]['done'] = not item['done']
                    save_data()
                    st.rerun()
                if c_icon2.button("🗑️", key=f"del_wi_{i}"):
                    st.session_state.wishlist.pop(i)
                    save_data()
                    st.rerun()