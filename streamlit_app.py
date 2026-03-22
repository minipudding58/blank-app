import streamlit as st
import requests
from PIL import Image
import io

st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖")

# 세션 상태 초기화
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_search_results(title):
    """구글 API를 통해 더 넓은 범위로 검색합니다."""
    # 제목 앞뒤 공백 제거 및 검색 최적화
    clean_title = title.strip()
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=8&orderBy=relevance"
    try:
        res = requests.get(url, timeout=10).json()
        results = []
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            # 최대한 큰 이미지를 찾고, 없으면 기본 썸네일
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            if img_url:
                # 고화질 변환 및 보안 연결
                img_url = img_url.replace("http://", "https://") + "&fife=w800"
                results.append({
                    "url": img_url, 
                    "title": info.get("title", "제목 없음"), 
                    "date": info.get("publishedDate", "날짜 미상")[:4] # 년도만 표시
                })
        return results
    except:
        return []

st.title("📖 나만의 독서 스티커 메이커")
st.write("원하는 표지를 직접 선택하세요! 책 구분은 **슬래시(/)**로 해주시면 됩니다.")

# 1. 입력창 (이제 / 로 구분합니다!)
titles_input = st.text_area("책 제목들을 입력하세요 (예: 불편한 편의점 / 슬램덩크 / 파친코)", height=100)

# 2. 검색 섹션
if st.button("표지 검색 시작 🔍"):
    if titles_input:
        # 쉼표가 아닌 슬래시(/)로 나눕니다.
        titles = [t.strip() for t in titles_input.split("/") if t.strip()]
        with st.spinner('최신 표지들을 찾는 중...'):
            st.session_state.temp_results = {title: get_search_results(title) for title in titles}
    else:
        st.error("책 제목을 입력해주세요!")

# 3. 결과 선택창
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.warning(f"'{title}'에 대한 검색 결과가 없습니다. 제목을 정확하게 입력하거나 작가 이름을 포함해보세요.")
            continue
        
        # 4열로 이미지 배치
        cols = st.columns(4)
        for idx, res in enumerate(results):
            with cols[idx % 4]:
                st.image(res['url'], use_container_width=True)
                st.caption(f"{res['date']}년 버전")
                if st.button("선택", key=f"btn_{title}_{idx}"):
                    st.session_state.selected_images[title] = res['url']
                    st.toast(f"'{title}' 표지 담기 완료!")

# 4.