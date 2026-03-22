import streamlit as st
import requests
from PIL import Image
import io
import time

# 📏 규격 설정 (세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'my_collection' not in st.session_state:
    st.session_state.my_collection = []
if 'wishlist' not in st.session_state:
    st.session_state.wishlist = []

# --- UI 상단 ---
st.title("📖 나의 독서 기록")
st.write("표지를 골라 **인쇄용 스티커**를 만들거나, **읽고 싶은 책**을 보관함에 담으세요.")

# --- 섹션 1: 검색 ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터, 불편한 편의점")

def get_aladdin_covers(search_query):
    """알라딘에서 정보를 가져오며 지저분한 코드를 정제합니다."""
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        text = res.text
        parts = text.split('<div class="ss_book_box"')
        for part in parts[1:11]:
            try:
                # 이미지 주소 추출
                img_start = part.find('https://image.aladin.co.kr/product/')
                img_end = part.find('"', img_start)
                img_url = part[img_start:img_end].replace("cover200", "cover500")
                
                # 제목 추출 (지저분한 태그 제거)
                title_start = part.find('class="bo3"><b>') + 15
                title_end = part.find('</b>', title_start)
                raw_title = part[title_start:title_end]
                # HTML 태그 등 찌꺼기 제거
                clean_title = raw_title.replace("<b>", "").replace("</b>", "").strip()
                
                if img_start != -1:
                    results.append({"title": clean_title, "url": img_url})
            except:
                continue
    except:
        st.error("서버 연결 실패")
    return results

if query:
    with st.spinner(f"'{query}' 찾는 중..."):
        books = get_aladdin_covers(query)
        
        if not books:
            st.warning("결과가 없습니다.")
        else:
            st.subheader(f"📍 '{query}' 검색 결과")
            cols = st.columns(5)
            for idx, book in enumerate(books):
                with cols[idx % 5]:
                    try:
                        img_res = requests.get(book['url'], timeout=5)
                        img_data = img_res.content
                        img = Image.open(io.BytesIO(img_data)).convert("RGB")
                        
                        st.image(img, use_container_width=True)
                        # 제목 출력 (이미지 밑에 지저분한 텍스트 없이 깔끔하게)
                        display_title = (book['title'][:15] + '..') if len(book['title']) > 15 else book['title']
                        st.caption(display_title)
                        
                        # 버튼 2종 세트
                        if st.button("🖼️ 스티커 담기", key=f"sticker_{idx}"):
                            st.session_state.my_collection.append(img)
                            st.toast("스티커 판에 추가되었습니다!")
                        
                        if st.button("💛 위시리스트", key=f"wish_{idx}"):
                            if book['title'] not in st.session_state.wishlist:
                                st.session_state.wishlist.append(book['title'])
                                st.toast("읽고 싶은 책 보관함에 저장!")
                    except:
                        continue

# --- 섹션 2: 보관함 공간 ---
st.divider()
tab1, tab2 = st.tabs(["🖨️ 인쇄용 스티커 판", "📚 읽고 싶은 책 보관함"])

with tab1:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.write(f"현재 **{len(st.session_state.my_collection)}개** 담김")
        if st.button("🗑️ 판 비우기"):
            st.session_state.my_collection = []
            st.rerun()
    
    with col_b:
        if st.session_state.my_collection:
            a4_w, a4_h = int(210/25.4*DPI), int(297/25.4*DPI)
            sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
            curr_x, curr_y = 120, 120
            
            for pic in st.session_state.my_collection:
                ratio = TARGET_H_PX / float(pic.size[1])
                w = int(pic.size[0] * ratio)
                pic_res = pic.resize((w, TARGET_H_PX), Image.LANCZOS)
                
                if curr_x + w > a4_w - 120:
                    curr_x = 120
                    curr_y += TARGET_H_PX + 50
                
                if curr_y + TARGET_H_PX < a4_h - 120:
                    sheet.paste(pic_res, (curr_x, curr_y))
                    curr_x += w + 50
            
            st.image(sheet, use_container_width=True)
            buf = io.BytesIO()
            sheet.save(buf, format="PNG")
            st.download_button("📥 스티커 판 다운로드", buf.getvalue(), "stickers.png", "image/png")

with tab2:
    st.subheader("📝 나의 독서 위시리스트")
    if not st.session_state.wishlist:
        st.info("나중에 읽고 싶은 책을 검색 결과에서 담아보세요!")
    else:
        for i, book_name in enumerate(st.session_state.wishlist):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{i+1}. {book_name}")
            if c2.button("삭제", key=f"del_wish_{i}"):
                st.session_state.wishlist.pop(i)
                st.rerun()