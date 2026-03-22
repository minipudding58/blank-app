import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os

# 📏 인쇄 규격 설정 (세로 4cm 기준 고해상도 A4)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) # 스티커 세로 40mm
A4_W_PX = int((210 / 25.4) * DPI) # A4 가로 210mm
A4_H_PX = int((297 / 25.4) * DPI) # A4 세로 297mm

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 💾 데이터 저장/불러오기 로직 (새로고침 방지) ---
DATA_FILE = "read_books_data.json"

# 세션 상태 초기화
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

def save_data():
    """담은 책 모음과 위시리스트 데이터를 로컬 파일에 저장합니다."""
    data = {
        # 담은 책 모음은 이미지 URL만 저장
        "collection_urls": [item["url"] for item in st.session_state.collection],
        "wishlist": st.session_state.wishlist
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    """로컬 파일에서 데이터를 불러와 세션 상태를 복구합니다."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 1. 담은 책 모음 이미지 로딩 및 복구 (URL 기반)
                st.session_state.collection = []
                for url in data.get("collection_urls", []):
                    img_res = requests.get(url, timeout=5)
                    img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                    # 개별 삭제 시 URL 기반 중복 체크를 위해 URL도 함께 저장
                    st.session_state.collection.append({"img": img, "url": url})
                
                # 2. 위시리스트 복구
                st.session_state.wishlist = data.get("wishlist", [])
        except:
            pass

# 초기 로딩 시 데이터 복구
if not st.session_state.collection and not st.session_state.wishlist:
    with st.spinner("이전 독서 기록을 불러오는 중..."):
        load_data()

# CSS 주입: 불필요한 태그 제거 및 디자인 최적화
st.markdown("""
    <style>
    .stCaption { color: rgba(0,0,0,0) !important; height: 0px; margin-bottom: -10px; }
    .stDownloadButton button { background-color: #2196F3; color: white; border-radius: 8px; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (강력한 파싱 로직) ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터")

def get_books_cleaned(search_query):
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        img_urls = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', res.text)
        
        for i in range(min(len(img_urls), 8)):
            try:
                raw_title = titles[i]
                # 불필요한 태그 및 찌꺼기 코드($4336"><table>$ 등) 완벽 제거
                clean_title = re.sub(r'<.*?>', '', raw_title).replace('<b>', '').replace('</b>', '').strip()
                if '>' in clean_title: clean_title = clean_title.split('>')[1].strip()
                results.append({"title": clean_title, "url": img_urls[i]})
            except: continue
    except: pass
    return results

if query:
    books = get_books_cleaned(query)
    if books:
        st.subheader(f"📍 '{query}' 검색 결과")
        cols = st.columns(4)
        for idx, book in enumerate(books):
            with cols[idx % 4]:
                st.image(book['url'], use_container_width=True)
                st.write(f"**{book['title']}**")
                
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                    img_res = requests.get(book['url'])
                    img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                    # URL 기반 중복 체크
                    if not any(d['url'] == book['url'] for d in st.session_state.collection):
                        st.session_state.collection.append({"img": img, "url": book['url']})
                        save_data() # 데이터 저장
                        st.toast("인쇄판 추가!")
                    else: st.warning("이미 담겨있습니다.")
                if c2.button("💛 위시", key=f"wi_{idx}"):
                    if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"title": book['title'], "url": book['url'], "done": False})
                        save_data() # 데이터 저장
                        st.toast("위시리스트 저장!")
    else: st.warning("결과가 없습니다.")

# --- 🎨 1:1 이분할 레이아웃 배치 ---
st.divider()
left_col, right_col = st.columns([1, 1])

# --- 🖼️ 요청 반영: 읽은 책 모음 (개별 삭제 기능 부활) ---
with left_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    st.write(f"현재 총 **{len(st.session_state.collection)}개** 담김")
    
    if st.session_state.collection:
        # 삭제 모드 토글 스위치 (요청 1)
        del_cols = st.columns([4, 1])
        with del_cols[0]:
            if st.button("🗑️ 전체 비우기"):
                st.session_state.collection = []
                save_data() # 데이터 저장
                st.rerun()
        with del_cols[1]:
            # 💡 개별 삭제 모드 토글 (요청 1)
            delete_mode = st.toggle("개별 삭제 모드")

        if delete_mode:
            st.warning("스티커를 클릭하면 인쇄판에서 삭제됩니다.")
            cols_del = st.columns(6)
            for idx, item in enumerate(st.session_state.collection):
                img = item["img"]
                with cols_del[idx % 6]:
                    st.image(img, use_container_width=True)
                    # 💡 개별 삭제 버튼 부활 (요청 1)
                    if st.button("❌", key=f"del_sticker_{idx}"):
                        st.session_state.collection.pop(idx)
                        save_data() # 데이터 저장
                        st.rerun()
        else:
            # 인쇄용 고해상도 A4 캔버스 생성 및 붙이기 로직
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 120, 120 # 시작 여백
            margin = 40 # 스티커 간 여백
            
            for item in st.session_state.collection:
                img = item["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                w = int(img.size[0] * ratio)
                img_res = img.resize((w, TARGET_H_PX), Image.LANCZOS)
                
                # 줄바꿈 로직
                if x + w > A4_W_PX - 120:
                    x = 120; y += TARGET_H_PX + margin
                sheet.paste(img_res, (x, y))
                x += w + margin
            
            # 인쇄 미리보기 화면에 출력
            st.image(sheet, use_container_width=True, caption="인쇄 미리보기")
            
            # --- 📄 요청 반영: PDF 다운로드 버튼 (요청 2) ---
            pdf_buf = io.BytesIO()
            # 💡 고해상도 PDF 생성 (깨짐 방지)
            sheet.save(pdf_buf, format="PDF", resolution=DPI)
            st.download_button(
                label="📄 PDF 저장 (인쇄용)",
                data=pdf_buf.getvalue(),
                file_name="my_book_stickers.pdf",
                mime="application/pdf"
            )

# --- 📚 오른쪽: 위시리스트 (슬림 버전) ---
with right_col:
    st.header("📚 위시리스트")
    if not st.session_state.wishlist:
        st.write("위시리스트가 비어있습니다.")
    else:
        for i, item in enumerate(st.session_state.wishlist):
            with st.container(border=True):
                # 💡 요청 2: 위시리스트 이미지 표시
                c_img, c_done, c_del = st.columns([1, 4, 1])
                
                with c_img:
                    st.image(item['url'], use_container_width=True)
                
                with c_done:
                    # 💡 제목 출력 및 HTML 태그 완전 소탕
                    st.write(f"**{item['title']}**")
                    # 💡 요청 3: 읽음 체크박스 기능
                    check_label = f"chk_{i}"
                    is_done = st.checkbox("📖 읽음 체크", value=item['done'], key=check_label)
                    st.session_state.wishlist[i]['done'] = is_done
                    if is_done: st.success("✅ 읽기 완료!")
                
                with c_del:
                    # 💡 요청 2: 삭제 버튼 배치 최적화
                    if st.button("🗑️ 삭제", key=f"del_wish_{i}"):
                        st.session_state.wishlist.pop(i)
                        save_data() # 데이터 저장
                        st.rerun()