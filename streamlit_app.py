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

# --- 🔗 URL 닉네임 인식 시스템 ---
query_params = st.query_params
url_user = query_params.get("user", "")

if 'user_id' not in st.session_state:
    st.session_state.user_id = url_user

# --- 🔑 입장 화면 (닉네임 설정) ---
if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    st.write("나만의 닉네임을 입력하면 고유한 저장 링크가 생깁니다.")
    user_input = st.text_input("닉네임 입력 (예: 치이카와)", placeholder="닉네임을 입력하고 아래 버튼을 눌러주세요.")
    
    if st.button("내 기록장 만들기/열기"):
        if user_input:
            st.query_params["user"] = user_input
            st.session_state.user_id = user_input
            st.rerun()
        else:
            st.warning("닉네임을 입력해주세요!")
    st.stop()

# 사용자별 데이터 파일 경로
USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

# --- 💾 데이터 저장/로드 함수 ---
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

# 데이터 초기 로드
if not st.session_state.collection and not st.session_state.wishlist:
    load_all()

# --- 🎨 스타일 설정 (투명 버튼 및 정렬) ---
st.markdown("""
    <style>
    .stCaption { display:none; }
    /* 버튼 글자 크기 통일 */
    div.stButton > button p, div.stDownloadButton > button p, div[data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        white-space: nowrap !important;
    }
    /* PDF 다운로드 버튼: 투명 배경색 적용 */
    div.stDownloadButton > button {
        width: 100%;
        background-color: transparent !important;
        color: #333333 !important;
        border: 1px solid #ccc !important;
        border-radius: 4px;
        height: 38px !important;
    }
    /* 전체 비우기 버튼: 높이 맞춤 */
    div.stButton > button {
        height: 38px !important;
        background-color: transparent !important;
        border: 1px solid #ccc !important;
    }
    /* 수평 정렬 중앙 맞춤 */
    div[data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 메인 화면 구성 ---
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("로그아웃"):
        st.query_params.clear()
        st.session_state.user_id = ""
        st.session_state.collection = []
        st.session_state.wishlist = []
        st.rerun()

# 닉네임 반영 타이틀
st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 🔍 책 검색 섹션 (에러 방지용 헤더 추가) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        # User-Agent를 정확히 설정하여 403 에러 방지
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        
        if imgs:
            cols = st.columns(4)
            for i, img_url in enumerate(imgs[:8]):
                with cols[i % 4]:
                    st.image(img_url, use_container_width=True)
                    c1, c2 = st.columns(2)
                    if c1.button("📖 스티커", key=f"s_{i}"):
                        r = requests.get(img_url, headers=headers)
                        img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({"img": img_obj, "url": img_url})
                        save_all(); st.rerun()
                    if c2.button("🩵 위시", key=f"w_{i}"):
                        if not any(d['url'] == img_url for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"url": img_url, "done": False})
                            save_all(); st.rerun()
    except Exception as e:
        st.error(f"검색 중 에러가 발생했습니다: {e}")

st.divider()
left_col, right_col = st.columns(2)

# --- 🖨️ 왼쪽: 읽은 책 모음 (A4 레이아웃) ---
with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        b1, b2, b3 = st.columns([1, 1.2, 1.3])
        with b1:
            if st.button("🗑️ 전체 비우기", use_container_width=True):
                st.session_state.collection = []; save_all(); st.rerun()
        with b2:
            st.write(""); st.write("") # 간격 조정
            del_mode = st.toggle("개별 삭제 모드")
        with b3:
            # A4 캔버스 생성 및 스티커 배치
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
                file_name=f"{st.session_state.user_id}_reading_list.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        st.write("---")
        if del_mode:
            dcols = st.columns(4)
            for idx, itm in enumerate(st.session_state.collection):
                with dcols[idx % 4]:
                    st.image(itm['img'], use_container_width=True)
                    if st.button("❌ 삭제", key=f"del_{idx}"):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
        else:
            st.image(sheet, use_container_width=True, caption="인쇄 미리보기 (A4)")
    else:
        st.info("읽은 책을 추가해 보세요!")

# --- 📚 오른쪽: 위시리스트 ---
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
                            headers = {"User-Agent": "Mozilla/5.0"}
                            r = requests.get(item['url'], headers=headers)
                            img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                            if not any(d['url'] == item['url'] for d in st.session_state.collection):
                                st.session_state.collection.append({"img": img_obj, "url": item['url']})
                        save_all(); st.rerun()
                    if ic2.button("🗑️ 삭제", key=f"dw_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
    else:
        st.write("위시리스트가 비어있습니다.")