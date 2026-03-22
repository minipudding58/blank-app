import streamlit as st
import requests
from PIL import Image
import io
import time

# 📏 인쇄 규격 설정 (세로 4cm 기준)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화 (담은 책 모음 및 위시리스트)
if 'collection' not in st.session_state:
    st.session_state.collection = []
if 'wishlist' not in st.session_state:
    st.session_state.wishlist = []

# --- 🎨 UI 전면 개편: 1:1 이분할 레이아웃 ---
st.title("📖 나의 독서 기록 관리")
st.write("표지를 골라 **읽은 책 모음**을 만들거나, **읽고 싶은 책**을 위시리스트에 담으세요.")

# 검색 섹션 (엔터 치면 즉시 검색)
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터")

def get_aladdin_refined(search_query):
    """지저분한 코드() 없이 실제 정보만 정확히 추출합니다."""
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        text = res.text
        
        # 💡 지저분한 코드() 제거의 핵심 로직: 도서 상자별로 명확히 분리
        parts = text.split('<div class="ss_book_box"')
        for part in parts[1:11]: # 상위 10개만
            try:
                # 1. 이미지 주소 추출
                img_start = part.find('https://image.aladin.co.kr/product/')
                img_end = part.find('"', img_start)
                img_url = part[img_start:img_end].replace("cover200", "cover500")
                
                # 2. 제목 추출 (HTML 태그 및 코드 찌꺼기 제거)
                title_start = part.find('class="bo3"><b>') + 15
                title_end = part.find('</b>', title_start)
                raw_title = part[title_start:title_end]
                
                # 💡 HTML 태그() 제거
                clean_title = raw_title.replace("<b>", "").replace("</b>", "").strip()
                
                # 가끔 제목 뒤에 나오는 불필요한 공백/코드 제거
                if '>' in clean_title: clean_title = clean_title.split('>')[1].strip()

                if img_start != -1:
                    results.append({"title": clean_title, "url": img_url})
            except:
                continue
    except:
        st.error("서버 연결 실패")
    return results

if query:
    with st.spinner(f"'{query}'의 모든 정보를 찾는 중..."):
        books = get_aladdin_refined(query)
        
        if not books:
            st.warning("결과가 없습니다.")
        else:
            st.subheader(f"📍 '{query}' 검색 결과")
            # 💡 지저분한 코드() 제거 확인을 위해 한 줄에 4개씩 깔끔하게 배치
            cols = st.columns(4)
            for idx, book in enumerate(books):
                with cols[idx % 4]:
                    try:
                        img_res = requests.get(book['url'], timeout=5)
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        
                        st.image(img, use_container_width=True)
                        # 제목 출력 (이미지 밑에 코드 없이 깔끔하게)
                        st.caption(book['title'][:25] + '..' if len(book['title']) > 25 else book['title'])
                        
                        # 버튼 배치: 이분할 화면에 맞춰 깔끔하게
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("🖼️ 스티커", key=f"sticker_{idx}"):
                                st.session_state.collection.append(img)
                                st.toast("읽은 책 모음에 추가!")
                        with b2:
                            if st.button("💛 위시", key=f"wish_{idx}"):
                                # 위시리스트에는 제목만 저장 (에러 방지)
                                if book['title'] not in st.session_state.wishlist:
                                    st.session_state.wishlist.append(book['title'])
                                    st.toast("위시리스트에 저장!")
                    except:
                        continue

# --- 🎨 요청 반영: 1:1 이분할 레이아웃 배치 ---
st.divider()
# 💡 공간 비율을 1:1로 수정
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("🖨️ 읽은 책 모음 (인쇄용 A4)")
    st.write(f"현재 총 **{len(st.session_state.collection)}개** 담김")
    
    # 지우기 버튼을 오른쪽 상단으로 배치
    if st.session_state.collection:
        c1, c2 = st.columns([4, 1])
        if c2.button("🗑️ 전체 지우기"):
            st.session_state.collection = []
            st.rerun()
        
        # A4 용지 생성 로직 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y = 120, 120
        margin = 40
        
        for img in st.session_state.collection:
            ratio = TARGET_H_PX / float(img.size[1])
            w = int(img.size[0] * ratio)
            img_res = img.resize((w, TARGET_H_PX), Image.LANCZOS)
            
            # 줄바꿈 로직
            if curr_x + w > a4_w - 120:
                curr_x = 120
                curr_y += TARGET_H_PX + margin
            
            sheet.paste(img_res, (curr_x, curr_y))
            curr_x += w + margin
            
        st.image(sheet, use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_book_stickers.png", "image/png")
    else:
        st.info("검색 결과에서 표지를 선택하면 여기에 A4 인쇄판이 생성됩니다.")

with right_col:
    st.header("📚 읽고 싶은 책 (위시리스트)")
    if not st.session_state.wishlist:
        st.info("나중에 읽고 싶은 책을 위시리스트에 담아보세요!")
    else:
        # 💡 위시리스트 코드() 대신 깔끔한 제목 목록으로 수정
        for i, wish_title in enumerate(st.session_state.wishlist):
            c1, c2 = st.columns([4, 1])
            # 💡 지저분한 HTML 코드 없이 실제 제목만 출력
            c1.write(f"{i+1}. {wish_title}")
            if c2.button("삭제", key=f"del_wish_{i}"):
                st.session_state.wishlist.pop(i)
                st.rerun()