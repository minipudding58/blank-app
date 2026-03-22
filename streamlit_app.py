import streamlit as st
import requests
from PIL import Image
import io

# 📏 인쇄 규격 (300 DPI 기준 세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_image_safe(url):
    """이미지 보안 차단을 우회하여 가져옵니다."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return Image.open(io.BytesIO(res.content))
    except:
        return None

def search_aladdin_style(title):
    """알라딘 검색 엔진을 흉내 내어 국내 도서 표지를 찾습니다."""
    clean_title = title.strip()
    results = []
    
    # 1. 알라딘 검색 인덱스를 활용한 우회 검색
    # 국내 도서 검색에 가장 최적화된 경로입니다.
    search_url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&country=KR&maxResults=10"
    
    try:
        res = requests.get(search_url, timeout=5).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            # ISBN을 찾아서 알라딘 고화질 서버 주소로 변환 시도
            isbns = info.get("industryIdentifiers", [])
            isbn13 = next((i["identifier"] for i in isbns if i["type"] == "ISBN_13"), None)
            
            img_url = None
            if isbn13:
                # 알라딘 고화질 표지 서버 주소 규칙 적용
                img_url = f"https://image.aladin.co.kr/product/{isbn13[:5]}/{isbn13[5:7]}/cover500/{isbn13}.jpg"
            else:
                links = info.get("imageLinks", {})
                img_url = links.get("extraLarge") or links.get("large") or links.get("thumbnail")

            if img_url:
                img_url = img_url.replace("http://", "https://")
                results.append({
                    "url": img_url,
                    "title": info.get("title", title),
                    "date": info.get("publishedDate", "미상")[:4]
                })
    except:
        pass
    return results

st.title("📖 나의 독서 기록")
st.markdown("💡 **입력 예시:** `불편한 편의점 / 해리포터 / 파친코` (구분은 **/** 로)")

# 엔터 검색을 위한 폼
with st.form("search_form"):
    titles_input = st.text_input("책 제목을 입력하고 **Enter**를 누르세요!", placeholder="예: 파친코")
    submit_button = st.form_submit_button("표지 찾기 🔍")

if submit_button and titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('국내 서점 데이터를 연결 중...'):
        st.session_state.temp_results = {title: search_aladdin_style(title) for title in titles}

# 🔍 결과 표시
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.error(f"'{title}' 정보를 찾지 못했습니다. 제목을 더 정확히 입력해보세요.")
            continue
        
        cols = st.columns(5)
        for idx, res in enumerate(results):
            with cols[idx % 5]:
                img_obj = get_image_safe(res['url'])
                if img_obj:
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"{res['date']}년판")
                    if st.button("선택", key=f"btn_{title}_{idx}"):
                        st.session_state.selected_images[title] = img_obj
                        st.toast(f"'{title}' 완료!")

# 🖨️ 세로 4cm 인쇄판
if st.session_state.selected_images:
    st.divider()
    if st.button("세로 4cm 스티커 판 만들기 (인쇄용 A4) ✨"):
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y, margin = 100, 100, 40
        
        for title, img in st.session_state.selected_images.items():
            ratio = TARGET_H_PX / float(img.size[1])
            target_w_px = int(img.size[0] * ratio)
            img_resized = img.resize((target_w_px, TARGET_H_PX), Image.LANCZOS)
            
            if curr_x + target_w_px > a4_w - 100:
                curr_x, curr_y = 10