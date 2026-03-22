import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os

# 📏 인쇄 규격 설정 (DPI=300, 세로 40mm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 데이터 저장소 초기화
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

# --- 🎨 스타일 설정 ---
st.markdown("""
    <style>
    .stCaption { display:none; }
    div.stDownloadButton > button {
        width: 100%;
        background-color: #FDEDED !important;
        color: #333333 !important;
        font-weight: bold;
        border: 1px solid #f0d0d0;
        border-radius: 8px;
    }
    div.stDownloadButton > button:hover {
        background-color: #fce1e1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📖 나의 독서 기록 관리")

# --- 🔍 책 검색 엔진 (안정화 버전) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

if query:
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
    
    if imgs:
        cols = st.columns(4)
        for i, img_url in enumerate(imgs[:8]):
            with cols[i % 4]:
                st.image(img_url, use_container_width=True)
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"s_{i}"):
                    r = requests.get(img_url)
                    img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({"img": img_obj, "url": img_url})
                    save_all(); st.rerun()
                if c2.button("💛 위시", key=f"w_{i}"):
                    if not any(d['url'] == img_url for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"url": img_url, "done": False})
                        save_all(); st.rerun()
    else:
        st.error("검색 결과가 없습니다!")

st.divider()
left_col, right_col = st.columns(2)

# --- 🖨️ 왼쪽: 읽은 책 모음 ---
with left_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        del_cols = st.columns([4, 1])
        with del_cols[0]:
            if st.button("🗑️ 전체 비우기"):
                st.session_state.collection = []; save_all(); st.rerun()
        with del_cols[1]: del_mode = st.toggle("개별 삭제 모드")
            
        if del_mode:
            st.info("❌ 버튼을 누르면 인쇄판에서 삭제됩니다.")
            cols_del = st.columns(5)
            for idx, itm in enumerate(st.session_state.collection):
                with cols_del[idx % 5]:
                    st.image(itm['img'], use_container_width=True)
                    if st.button("❌ 삭제", key=f"del_{idx}"):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
        else:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120
            for itm in st.session_state.collection:
                img = itm['img']
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 120:
                    x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            
            st.image(sheet, use_container_width=True, caption="인쇄 미리보기 (A4)")
            pdf_buf = io.BytesIO()
            sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button(
                label="📥 PDF 다운로드",
                data=pdf_buf.getvalue(),
                file_name="my_stickers.pdf",
                mime="application/pdf"
            )

# --- 📚 요청 반영: 위시리스트 (아이콘 -> 글자 버튼) ---
with right_col:
    st.header("📚 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                # 💡 요청사항 반영: 작은 슬림 카드 디자인
                with st.container(border=True):
                    # 🖼️ 책 이미지 (상단)
                    st.image(item['url'], use_container_width=True)
                    
                    # 💡 요청 반영: 아이콘 대신 글자가 들어간 버튼으로 교체
                    c_btn1, c_btn2 = st.columns(2)
                    
                    with c_btn1:
                        # ⚪ 동그라미 대신 **[📖 선택]** 버튼
                        if not item['done']:
                            if st.button("📖 선택", key=f"chk_{i}", use_container_width=True):
                                st.session_state.wishlist[i]['done'] = True
                                # 선택 시 자동으로 읽은 책 모음에 추가
                                requests.get(item['url']) # 에러 방지용
                                img_res = requests.get(item['url'])
                                img_obj = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                                st.session_state.collection.append({"img": img_obj, "url": item['url']})
                                st.toast("💕 위시에서 인쇄판으로 담았습니다!")
                                save_all(); st.rerun()
                        else:
                            # ✅ 체크 대신 **[✅ 완료]** 버튼 (클릭 시 취소)
                            if st.button("✅ 완료", key=f"chk_done_{i}", use_container_width=True):
                                st.session_state.wishlist[i]['done'] = False
                                save_all(); st.rerun()
                    with c_btn2:
                        # 🗑️ 쓰레기통 대신 **[🗑️ 삭제]** 버튼
                        if st.button("🗑️ 삭제", key=f"del_wi_{i}", use_container_width=True):
                            st.session_state.wishlist.pop(i)
                            save_all(); st.