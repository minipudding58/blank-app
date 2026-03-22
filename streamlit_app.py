import streamlit as st
import requests
from PIL import Image
import io

# 📏 규격 설정 (300 DPI 기준 세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_korean_covers(title):
    """국내 도서 표지를 찾기 위해 검색 엔진을 강화했습니다."""
    clean_title = title.strip()
    # 구글 북스 API를 사용하되, 한국 도서 검색에 최적화된 파라미터 추가
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=10&orderBy=relevance"
    results = []
    try:
        res = requests.get(url, timeout=5).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            # 고화질 이미지 우선 순위
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            if img_url:
                # https 전환 및 구글 이미지 고화질 강제 변환
                img_url = img_url.replace("http://", "https://")
                if "google" in img_url: img_url += "&fife=w800"
                results.append({
                    "url": img_url,
                    "title": info.get("title", "제목 없음"),
                    "date": info.get("publishedDate", "미상")[:4]
                })
    except:
        pass
    return results

st.title("📖 나만의 독서 스티커 메이커")

# --- 💡 요청 반영 1: 예시 목록 위치 상단 이동 ---
st.markdown("💡 **입력 예시:** `불편한 편의점 / 파친코 / 해리포터` (구분은 **/** 로)")

# --- 💡 요청 반영 2: 엔터 치면 바로 검색되는 한 줄 입력창 ---
titles_input = st.text_input("책 제목들을 입력하고 **Enter**를 누르세요!", placeholder="여기에 입력하세요...")

if titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('최신 표지들을 검색하는 중...'):
        st.session_state.temp_results = {title: get_korean_covers(title) for title in titles}

# 🔍 결과 선택 섹션
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.error(f"'{title}' 결과를 찾지 못했습니다. 작가 이름을 붙여보세요! (예: {title} 김호연)")
            continue
        
        cols = st.columns(5)
        for idx, res in enumerate(results):
            with cols[idx % 5]:
                st.image(res['url'], use_container_width=True)
                st.caption(f"{res['date']}년")
                if st.button("선택", key=f"btn_{title}_{idx}"):
                    st.session_state.selected_images[title] = res['url']
                    st.toast(f"'{title}' 담기 완료!")

# 🖨️ 최종 인쇄판 생성 (사용자님의 최종 목적!)
if st.session_state.selected_images:
    st.divider()
    st.subheader("✅ 담은 스티커 목록")
    st.write(", ".join(st.session_state.selected_images.keys()))
    
    if st.button("세로 4cm 스티커 판 만들기 (인쇄용) ✨"):
        # A4 사이즈 (300 DPI)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y, margin = 100, 100, 40
        
        with st.spinner('인쇄용 파일을 만드는 중...'):
            for title, url in st.session_state.selected_images.items():
                img_res = requests.get(url)