import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정 (세로 4cm 기준)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (가장 안정적인 파싱 로직) ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터, 불편한 편의점")

def get_books_stable(search_query):
    """지저분한 코드 없이 책 정보만 확실하게 가져옵니다."""
    # PC보다 변화가 적은 모바일 검색 페이지 활용
    url = f"https://www.aladin.co.kr/m/msearch.aspx?SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        # 💡 HTML 구조를 직접 쪼개서 제목과 이미지만 추출 (코드 잔재 방지)
        items = res.text.split('<div class="ms_book_box">')
        for item in items[1:9]:
            try:
                # 이미지 URL 추출
                img_start = item.find('src="') + 5
                img_end = item.find('"', img_start)
                img_url = item[img_start:img_end].replace("cover200", "cover500")
                
                # 제목 추출 및 불순물 제거
                title_start = item.find('class="tit">') + 12
                title_end = item.find('<', title_start)
                clean_title = re.sub(r'<.*?>', '', item[title_start:title_end]).strip()
                
                if "http" in img_url:
                    results.append({"title": clean_title, "url": img_url})
            except: continue
    except: pass
    return results

if query:
    with st.spinner("알라딘에서 정보를 가져오는 중..."):
        books = get_books_stable(query)
        if books:
            st.subheader(f"📍 '{query}' 검색 결과")
            cols = st.columns(4)
            for idx, book in enumerate(books):
                with cols[idx % 4]:
                    st.image(book['url'], use_container_width=True)
                    # 💡 제목만 깔끔하게 표시 (코드 잔재 소탕)
                    st.write(f"**{book['title']}**")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                        r = requests.get(book['url'])
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append(img)
                        st.toast("인쇄판에 추가되었습니다!")
                    if c2.button("💛 위시", key=f"wi_{idx}"):
                        if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"title