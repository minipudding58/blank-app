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
                    try:
                        r = requests.get(url, timeout=5)
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img, "url": url})
                    except: continue
        except: pass

if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

# --- 🎨 스타일 설정 (PDF 버튼 색상 #B0FFFA 및 위시리스트 버튼 폰트 조절) ---
st.markdown("""
    <style>
    .stCaption { display:none; }
    /* PDF 다운로드 버튼 커스텀 */
    div.stDownloadButton > button {
        width: 100%;
        background-color: #B0FFFA !important;
        color: #333333 !important;
        font-weight: bold;
        border: 1px solid #90e0db;
        border-radius: 8px;
    }
    div.stDownloadButton > button:hover {
        background-color: #98f5ef !important;
    }
    /* 위시리스트 버튼 글자 크기 축소 (줄바꿈 방지) */
    div[data-testid="stHorizontalBlock"] button p {
        font-size: 13px !important;
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📖 나의 독서 기록 관리")

# --- 🔍 책 검색 섹션 ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        
        if imgs:
            cols = st.columns(4)
            for i, img_url in enumerate(imgs[:8]):
                with cols[i % 4]:
                    st.image(img_url, use_container_width=True)
                    c1, c2 = st.columns(2)
                    if c1.button("📖 스티커", key=f"s_{i}"):
                        r = requests.get(img_url)
                        img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img_obj, "url": img_url})
                        save_all()
                        st.rerun()
                    if c2.button("🩵 위시", key=f"w_{i}"):
                        if not any(d['url'] == img_url for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"url": img_url, "done": False})
                            save_all()
                            st.rerun()
    except: st.error("검색 중 오류가 발생했습니다.")

st.divider()
left_col, right_col = st.columns(2)

# --- 🖨️ 왼쪽: 읽은 책 모음 ---
with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
        with btn_col1:
            if st.button("🗑️ 전체 비우기"):
                st.session_state.collection = []
                save_all()
                st.rerun()
        with btn_col2:
            del_mode = st.toggle("개별 삭제 모드")
        with btn_col3:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120
            for itm in st.session_state.collection:
                img = itm['img']
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 120:
                    x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            
            pdf_buf = io.BytesIO()
            sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button(
                label="📥 PDF 다운로드",
                data=pdf_buf.getvalue(),
                file_name="my_stickers.pdf",
                mime="application/pdf"
            )
        st.write("---")
        if del_mode:
            dcols = st.columns(4)
            for idx, itm in enumerate(st.session_state.collection):
                with dcols[idx % 4]:
                    st.image(itm['img'], use_container_width=True)
                    if st.button("❌ 삭제", key=f"del_{idx}"):
                        st.session_state.collection.pop(idx)
                        save_all()
                        st.rerun()
        else:
            st.image(sheet, use_container_width=True, caption="인쇄 미리보기 (A4)")
    else: st.info("읽은 책을 추가해 보세요!")

# --- 📚 오른쪽: 위시리스트 (아이콘 및 줄바꿈 최적화) ---
with right_col:
    st.header("🩵 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                with st.container(border=True):
                    st.image(item['url'], use_container_width=True)
                    ic1, ic2 = st.columns(2)
                    
                    # 💡 선택 버튼 (폰트 조절로 줄바꿈 방지)
                    btn_label = "✅ 완료" if item['done'] else "📖 선택"
                    if ic1.button(btn_label, key=f"chk_{i}", use_container_width=True):
                        new_status = not item['done']
                        st.session_state.wishlist[i]['done'] = new_status
                        if new_status:
                            r = requests.get(item['url'])
                            img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                            if not any(d['url'] == item['url'] for d in st.session_state.collection):
                                st.session_state.collection.append({"img": img_obj, "url": item['url']})
                        save_all()
                        st.rerun()
                        
                    # 💡 삭제 버튼
                    if ic2.button("🗑️ 삭제", key=f"del_w_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i)
                        save_all()
                        st.rerun()
    else: st.write("위시리스트가 비어있습니다.")