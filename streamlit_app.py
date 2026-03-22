import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# CSS 주입: 회색 캡션 글자(찌꺼기 코드)를 투명하게 만듭니다.
st.markdown("""
    <style>
    .stCaption {
        color: rgba(0,0,0,0) !important;
        height: 0px;
        margin-bottom: -10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (아까 잘 되던 원본 로직으로 복구) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

def get_data_original(search_query):
    # 가장 잘 작동했던 원본 주소입니다.
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        # 이미지와 제목을 가져오는 가장 확실한 규칙
        img_urls = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', res.text)
        
        for i in range(min(len(img_urls), 8)):
            t = titles[i] if i < len(titles) else "제목 없음"
            results.append({"title": t, "url": img_urls[i]})
    except:
        pass
    return results

if query:
    books = get_data_original(query)
    if books:
        st.subheader(f"📍 '{query}' 검색 결과")
        cols = st.columns(4)
        for idx, book in enumerate(books):
            with cols[idx % 4]:
                st.image(book['url'], use_container_width=True)
                # 💡 핵심: 캡션으로 넣어서 CSS가 투명하게 처리하도록 함
                st.caption(book['title']) 
                
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                    r = requests.get(book['url'])
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append(img)
                    st.toast("인쇄판 추가!")
                if c2.button("💛 위시", key=f"wi_{idx}"):
                    if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"title": book['title'], "url": book['url'], "done": False})
                        st.toast("위시리스트 추가!")

# --- 🎨 하단 레이아웃 (개별 삭제 기능 유지) ---
st.divider()
l_col, r_col = st.columns([1, 1])

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
            
            # A4 생성
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

with r_col:
    st.header("📚 위시리스트")
    for i, item in enumerate(st.session_state.wishlist):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 1])
            c1.image(item['url'], use_container_width=True)
            # 그림처럼 체크박스(버튼) 구현
            if c1.button("⚪" if not item['done'] else "✅", key=f"chk_{i}"):
                st.session_state.wishlist[i]['done'] = not item['done']
                st.rerun()
            c2.write(f"**{item['title']}**")
            if c3.button("삭제", key=f"del_wi_{i}"):
                st.session_state.wishlist.pop(i)
                st.rerun()