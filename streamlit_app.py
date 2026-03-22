import streamlit as st
import requests
from PIL import Image
import io

# 📏 규격 설정 (300 DPI 기준 세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖")

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_korean_book_covers(title):
    """국내 도서 검색에 최적화된 알라딘/구글 혼합 검색"""
    clean_title = title.strip()
    results = []
    seen_urls = set()
    
    # 1. 알라딘 검색 (국내 도서 최신 표지용)
    # 알라딘 오픈 API는 키가 필요하므로, 공개된 이미지 서버 경로를 우선 탐색합니다.
    search_url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=10&country=KR"
    
    try:
        res = requests.get(search_url, timeout=5).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            # ISBN 추출
            isbns = info.get("industryIdentifiers", [])
            isbn13 = next((i["identifier"] for i in isbns if i["type"] == "ISBN_13"), None)
            
            # ISBN이 있다면 알라딘 고화질 서버 주소 생성
            if isbn13:
                # 알라딘 대형 표지 주소 규칙
                img_url = f"https://image.aladin.co.kr/product/{isbn13[:5]}/{isbn13[5:7]}/cover500/{isbn13}.jpg"
                # 주소가 유효한지 확인
                check = requests.head(img_url, timeout=2)
                if check.status_code != 200: # 알라딘에 없으면 구글 이미지로 대체
                    links = info.get("imageLinks", {})
                    img_url = links.get("extraLarge") or links.get("large") or links.get("thumbnail")
            else:
                links = info.get("imageLinks", {})
                img_url = links.get("extraLarge") or links.get("large") or links.get("thumbnail")

            if img_url and img_url not in seen_urls:
                final_url = img_url.replace("http://", "https://")
                # 구글 이미지일 경우 화질 높이기
                if "google" in final_url: final_url += "&fife=w800"
                
                results.append({
                    "url": final_url,
                    "title": info.get("title", "제목 없음"),
                    "date": info.get("publishedDate", "미상")[:4]
                })
                seen_urls.add(img_url)
    except:
        pass
    return results

st.title("📖 나만의 독서 스티커 메이커")

# --- 💡 요청 반영 1: 예시 목록 위치 상단으로 ---
st.markdown("💡 **입력 예시:** `불편한 편의점 / 파친코 / 슬램덩크` (구분은 **/** 로)")

# --- 💡 요청 반영 2: 엔터 치면 바로 검색되는 한 줄 입력창 ---
# on_change를 쓰지 않아도 text_input은 엔터 치면 폼이 제출됩니다.
titles_input = st.text_input("책 제목들을 입력하고 **Enter**를 누르세요!", placeholder="여기에 입력하세요...")

if titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    # 검색 버튼을 누르거나 엔터를 쳤을 때만 새로 검색
    with st.spinner('국내 도서관에서 최신 표지를 찾는 중...'):
        st.session_state.temp_results = {title: get_search_results(title) if 'get_search_results' in globals() else get_korean_book_covers(title) for title in titles}

# 결과 선택창
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.error(f"'{title}' 결과를 찾지 못했습니다. 작가 이름을 같이 써보세요!")
            continue
        
        cols = st.columns(4)
        for idx, res in enumerate(results):
            with cols[idx % 4]:
                st.image(res['url'], use_container_width=True)
                st.caption(f"{res['date']}년")
                if st.button("선택", key=f"btn_{title}_{idx}"):
                    st.session_state.selected_images[title] = res['url']
                    st.toast(f"'{title}' 담기 완료!")

# 최종 스티커 생성 (세로 4cm)
if st.session_state.selected_images:
    st.divider()
    if st.button("세로 4cm 스티커 판 만들기 ✨"):
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y, margin = 100, 100, 40
        
        for title, url in st.session_state.selected_images.items():
            img_res = requests.get(url)
            img = Image.open(io.BytesIO(img_res.content))
            ratio = TARGET_H_PX / float(img.size[1])
            img_resized = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
            
            if curr_x + img_resized.size[0] > a4_w - 100:
                curr_x = 100
                curr_y += TARGET_H_PX + margin
            sheet.paste(img_resized, (curr_x, curr_y))
            curr_x += img_resized.size[0] + margin
            
        st.image(sheet, caption="인쇄용 미리보기 (A4)", use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")