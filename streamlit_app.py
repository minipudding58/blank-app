import streamlit as st
import requests
from PIL import Image
import io
import time

# 📏 규격 설정 (세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화 (담은 스티커 목록)
if 'my_collection' not in st.session_state:
    st.session_state.my_collection = []

# --- UI 상단 ---
st.title("📖 나의 독서 기록")
st.write("원하는 책을 검색하고, 마음에 드는 표지를 선택해 A4 인쇄판을 만드세요!")

# --- 섹션 1: 검색 (엔터 치면 바로 실행) ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터와 마법사의 돌")

def get_aladdin_covers(search_query):
    """알라딘에서 검색어와 일치하는 모든 책의 표지와 정보를 가져옵니다."""
    # 알라딘 오픈 API 대용 검색 결과 파싱 (안전한 패턴 매칭 방식)
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        text = res.text
        # 검색 결과 내에서 상품 아이디(ISBN/ItemID)와 제목 패턴 추출
        parts = text.split('<div class="ss_book_box"')
        for part in parts[1:11]: # 상위 10개만 추출
            try:
                # 이미지 주소 추출
                img_start = part.find('https://image.aladin.co.kr/product/')
                img_end = part.find('"', img_start)
                img_url = part[img_start:img_end].replace("cover200", "cover500")
                
                # 제목 추출
                title_start = part.find('class="bo3"><b>') + 15
                title_end = part.find('</b>', title_start)
                title = part[title_start:title_end]
                
                if img_start != -1:
                    results.append({"title": title, "url": img_url})
            except:
                continue
    except:
        st.error("검색 서버에 연결할 수 없습니다.")
    return results

if query:
    with st.spinner(f"'{query}'의 모든 판본을 찾는 중..."):
        books = get_aladdin_covers(query)
        
        if not books:
            st.warning("검색 결과가 없습니다. 제목을 정확히 입력해 주세요.")
        else:
            st.subheader(f"📍 '{query}' 검색 결과 (원하는 표지를 고르세요)")
            cols = st.columns(5)
            for idx, book in enumerate(books):
                with cols[idx % 5]:
                    try:
                        img_res = requests.get(book['url'], timeout=5)
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        st.image(img, use_container_width=True)
                        # 제목이 너무 길면 자르기
                        short_title = (book['title'][:15] + '..') if len(book['title']) > 15 else book['title']
                        st.caption(short_title)
                        
                        if st.button("이 표지 선택", key=f"select_{idx}"):
                            st.session_state.my_collection.append(img)
                            st.toast(f"'{short_title}' 보관함에 추가!")
                    except:
                        continue

# --- 섹션 2: 보관함 및 A4 미리보기 ---
st.divider()
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("✅ 담은 스티커 목록")
    st.write(f"현재 총 **{len(st.session_state.my_collection)}개** 선택됨")
    if st.button("🗑️ 전체 비우기"):
        st.session_state.my_collection = []
        st.rerun()

with col_right:
    st.subheader("🖨️ A4 인쇄 미리보기")
    if not st.session_state.my_collection:
        st.info("검색 결과에서 표지를 선택하면 여기에 A4 용지가 생성됩니다.")
    else:
        # A4 용지 생성 (300 DPI)
        a4_w, a4_h = int(210/25.4*DPI), int(297/25.4*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y = 120, 120
        margin = 50
        
        for img in st.session_state.my_collection:
            ratio = TARGET_H_PX / float(img.size[1])
            w = int(img.size[0] * ratio)
            img_res = img.resize((w, TARGET_H_PX), Image.LANCZOS)
            
            # 줄바꿈 로직
            if curr_x + w > a4_w - 120:
                curr_x = 120
                curr_y += TARGET_H_PX + margin
            
            # 용지 범위를 벗어나지 않을 때만 붙이기
            if curr_y + TARGET_H_PX < a4_h - 120:
                sheet.paste(img_res, (curr_x, curr_y))
                curr_x += w + margin
        
        st.image(sheet, use_container_width=True)
        
        # 다운로드 버튼
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_book_stickers.png", "image/png")