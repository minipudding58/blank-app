import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# DPI 설정 (300 DPI 기준, 인쇄 시 고화질 보장)
DPI = 300
# 세로 4cm를 픽셀로 변환 (약 472픽셀)
TARGET_H_PX = int((40 / 25.4) * DPI)

# 🎨 제목 & 스타일 설정 (사용자 선택 기능 강조!)
st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖", layout="wide")

# (기존 코드를 아래 내용으로 싹 지우고 붙여넣으세요!)
# --- [여기서부터 복사] ---
import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# 🎨 세션 상태 초기화 (검색 결과 및 선택 이미지 저장용)
if 'search_results' not in st.session_state:
    st.session_state.search_results = {} # {제목: [이미지1, 이미지2, ...]}
if 'selected_covers' not in st.session_state:
    st.session_state.selected_covers = {} # {제목: 선택된_이미지}

# --- ✨ 핵심 업데이트 1: 고해상도 이미지 가져오기 ---
def get_high_res_image(isbn):
    """
    구글 북스 API를 사용하여 ISBN 기반의 고해상도 이미지를 가져옵니다.
    """
    # 1. 고해상도 이미지 소스를 우선 탐색
    url_templates = [
        f"https://books.google.com/books/content?id={isbn}&printsec=frontcover&img=1&zoom=3", # 최고 해상도
        f"https://books.google.com/books/content?id={isbn}&printsec=frontcover&img=1&zoom=2", # 고해상도
    ]
    
    for url in url_templates:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                img = Image.open(io.BytesIO(response.content))
                # 너무 작거나 로딩 실패 이미지는 거름
                if img.size[0] > 100: 
                    return img
        except:
            pass
            
    # 2. 실패 시 차선책 (알라딘 API - 국내 도서에 강함)
    try:
        # (실제 서비스에서는 알라딘 API 키가 필요하지만, 우선 우회 방법을 시도)
        aladdin_url = f"https://www.aladdin.co.kr/shop/common/wn_cover.aspx?ISBN={isbn}&Size=Big"
        response = requests.get(aladdin_url, timeout=10)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
        
    return None # 모두 실패 시

# --- ✨ 핵심 업데이트 2: 다중 검색 결과 가져오기 ---
def search_book_covers(title):
    """
    구글 북스 API를 통해 제목으로 검색하고, 여러 표지 이미지를 가져옵니다.
    """
    # API 키 없이 검색 (결과 수가 제한적일 수 있음)
    search_url = f"https://www.googleapis.com/books/v1/volumes?q={title}"
    try:
        response = requests.get(search_url, timeout=10).json()
        covers = []
        if 'items' in response:
            for item in response['items'][:5]: # 상위 5개 결과만
                volume_info = item.get('volumeInfo', {})
                isbn = volume_info.get('industryIdentifiers', [{}])[0].get('identifier', None)
                if isbn:
                    img = get_high_res_image(isbn)
                    if img:
                        covers.append({'isbn': isbn, 'image': img, 'title': volume_info.get('title', title), 'publishedDate': volume_info.get('publishedDate', '날짜 정보 없음')})
        return covers
    except:
        pass
    return []

# --- 나머지 코드 (스티커 판 만들기 등) ---
st.title("📖 나만의 독서 스티커 메이커")
st.write("다이어리에 딱 맞는 세로 4cm 책 표지 스티커를 만들어보세요! (최신 버전 & 다중 선택 기능✨)")

titles_input = st.text_area("책 제목을 쉼표(,)로 구분해서 입력해주세요.", height=150, placeholder="예: 불편한 편의점, 슬램덩크 리소스")

# 🔍 책 표지 검색 및 선택 섹션
if st.button("책 표지 검색 🔍"):
    if not titles_input:
        st.warning("책 제목을 입력해주세요!")
    else:
        titles = [t.strip() for t in titles_input.split(',') if t.strip()]
        st.session_state.search_results = {} # 검색 결과 초기화
        for title in titles:
            st.session_state.search_results[title] = search_book_covers(title)

if st.session_state.search_results:
    st.divider()
    st.subheader("🖼️ 검색 결과 (원하는 표지를 선택하세요)")
    
    for title, results in st.session_state.search_results.items():
        st.markdown(f"**📍 '{title}' 검색 결과**")
        if not results:
            st.error(f"'{title}' 결과를 찾지 못했습니다. 제목을 더 정확하게 써보시겠어요?")
            continue
            
        cols = st.columns(len(results))
        for idx, res in enumerate(results):
            with cols[idx]:
                st.image(res['image'], use_container_width=True)
                st.caption(f"{res['publishedDate']}")
                if st.button("이 표지 선택", key=f"btn_{res['isbn']}"):
                    st.session_state.selected_covers[title] = res['image']
                    st.success(f"'{title}' 표지 선택 완료!")
    
    st.divider()

# 🖨️ 스티커 판 생성 및 인쇄 섹션
st.subheader("✅ 선택된 표지 목록")
if st.session_state.selected_covers:
    selected_cols = st.columns(len(st.session_state.selected_covers))
    for idx, (title, img) in enumerate(st.session_state.selected_covers.items()):
        with selected_cols[idx]:
            st.image(img, caption=title, use_container_width=True)
else:
    st.write("아직 선택된 표지가 없습니다.")

if st.button("선택된 표지로 스티커 판 만들기 ✨"):
    if not st.session_state.selected_covers:
        st.error("먼저 표지를 하나 이상 선택해주세요!")
    else:
        # A4 사이즈 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        
        curr_x, curr_y = 100, 100 # 여백
        margin = 40
        
        with st.spinner('세로 4cm로 예쁘게 정렬하는 중...'):
            for title, img in st.session_state.selected_covers.items():
                # 세로 4cm 고정 이미지 처리
                ratio = TARGET_H_PX / float(img.size[1])
                target_w_px = int(float(img.size[0]) * ratio)
                img_resized = img.resize((target_w_px, TARGET_H_PX), Image.LANCZOS)
                
                # 다음 줄로 넘기기
                if curr_x + target_w_px > a4_w - 100:
                    curr_x = 100
                    curr_y += TARGET_H_PX + margin
                    
                sheet.paste(img_resized, (curr_x, curr_y))
                curr_x += target_w_px + margin
            
        # 결과 보여주기
        st.balloons()
        st.image(sheet, caption="인쇄용 미리보기 (A4)", use_container_width=True)
        
        # 다운로드 버튼
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button(
            label="📥 인쇄용 이미지 다운로드",
            data=buf.getvalue(),
            file_name="my_stickers.png",
            mime="image/png"
        )

st.divider()
st.caption("제작: 사용자님의 끈기로 완성된 AI 조수 | 이미지 출처: 구글 북스, 알라딘")
# --- [여기까지 복사] ---