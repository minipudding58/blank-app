import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 기본 설정
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# CSS: 회색 찌꺼기 글자 투명 처리 + 위시리스트 슬림 디자인
st.markdown("""
    <style>
    /* 검색결과 아래 회색 글자 투명화 */
    .stCaption { color: rgba(0,0,0,0) !important; height: 0px; margin-bottom: -10px; }
    
    /* 위시리스트 슬림 카드 디자인 */
    .wish-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 저장소 초기화
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (기존 로직 유지) ---
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
                st.caption(book['title']) # 투명 처리됨
                
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                    r = requests.get(book['url'])
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append(img)
                    st.toast("인쇄판 추가!")
                if c2.button("💛 위시", key=f"wi_{idx}"):
                    # 중복 체크 후 추가 (여러 권 담기 가능)
                    if not any(d['url'] == book['url'] for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"url": book['url'], "done": False})
                        st.toast("위시리스트에 담았습니다!")

st.divider()
l_col, r_col = st.columns([1, 1])

# --- 🖨️ 왼쪽: 인쇄용 스티커 판 ---
with l_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        del_mode = st.toggle("개별 삭제 모드")
        if del_mode:
            c_del = st.columns(5)
            for i, img in enumerate(st.session_state.collection):
                with c_del[i % 5]:
                    st.image(img, use_container_width=True)
                    if st.button("❌", key=f"del_st_{i}"):
                        st.session_state.collection.pop(i)
                        st.rerun()
        else:
            if st.button("🗑️ 전체 비우기"):
                st.session_state.collection = []
                st.rerun()
            
            a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
            sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
            x, y = 120, 120
            for img in st.session_state.collection:
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > a4_w - 120:
                    x = 120; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            st.image(sheet, use_container_width=True)
            buf = io.BytesIO(); sheet.save(buf, format="PNG")
            st.download_button("📥 다운로드", buf.getvalue(), "books.png", "image/png")

# --- 📚 오른쪽: 위시리스트 (슬림 버전) ---
with r_col:
    st.header("📚 위시리스트")
    if not st.session_state.wishlist:
        st.write("위시리스트가 비어있습니다.")
    
    for i, item in enumerate(st.session_state.wishlist):
        # 작은 네모칸 구현
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.image(item['url'], width=80)
            with c2:
                # 체크박스 (동그라미 이모지 버튼)
                if st.button("⚪" if not item['done'] else "✅", key=f"chk_{i}"):
                    st.session_state.wishlist[i]['done'] = not item['done']
                    st.rerun()
            with c3:
                # 쓰레기통 삭제 버튼
                if st.button("🗑️", key=f"del_wi_{i}"):
                    st.session_state.wishlist.pop(i)
                    st.rerun()