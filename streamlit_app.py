import streamlit as st
import requests
from PIL import Image
import io

st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖")

# 세션 상태 초기화 (이미지 선택 데이터 저장)
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}

def get_search_results(title):
    """구글 북스에서 여러 개의 검색 결과를 가져옵니다."""
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}&maxResults=5"
    try:
        res = requests.get(url).json()
        results = []
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            if img_url:
                # 고화질 변환 팁
                img_url = img_url.replace("http://", "https://") + "&fife=w800-h1200"
                results.append({"url": img_url, "title": info.get("title"), "date": info.get("publishedDate", "날짜미상")})
        return results
    except:
        return []

st.title("📖 나만의 독서 스티커 메이커")
st.write("원하는 표지 버전을 직접 선택해서 스티커를 만드세요!")

# 1. 제목 입력
titles_input = st.text_area("책 제목들 (쉼표로 구분)", "불편한 편의점, 슬램덩크", height=100)
titles = [t.strip() for t in titles_input.split(",") if t.strip()]

# 2. 검색 및 선택 섹션
if st.button("표지 찾기 🔍"):
    st.session_state.temp_results = {title: get_search_results(title) for title in titles}

if 'temp_results' in st.session_state:
    for title, results in st.session_state.temp_results.items():
        st.subheader(f"📍 '{title}' 검색 결과")
        if not results:
            st.write("결과가 없습니다.")
            continue
        
        cols = st.columns(len(results))
        for idx, res in enumerate(results):
            with cols[idx]:
                st.image(res['url'], caption=f"{res['date']}판")
                if st.button("이걸로 선택", key=f"{title}_{idx}"):
                    st.session_state.selected_images[title] = res['url']
                    st.success(f"선택 완료!")

# 3. 최종 스티커 판 생성
st.divider()
if st.button("선택한 표지들로 스티커 판 만들기 ✨"):
    if not st.session_state.selected_images:
        st.error("먼저 표지를 하나 이상 선택해주세요!")
    else:
        # 선택된 이미지들을 모아서 보여줌
        final_cols = st.columns(4)
        for i, (t, url) in enumerate(st.session_state.selected_images.items()):
            with final_cols[i % 4]:
                img_res = requests.get(url)
                img = Image.open(io.BytesIO(img_res.content))
                st.image(img, use_container_width=True)
                
        st.balloons()
        st.success("모든 스티커가 준비되었습니다! 이제 인쇄하세요.")
    