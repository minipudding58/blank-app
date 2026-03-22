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
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return Image.open(io.BytesIO(res.content))
    except:
        return None

def search_books_refined(title):
    """검색 정확도를 높이기 위해 도서 전용 카테고리를 강화합니다."""
    clean_title = title.strip()
    results = []
    
    # 도서 검색에 특화된 쿼리 파라미터 적용 (printType=books 추가)
    api_url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&printType=books&maxResults=15&country=KR"
    
    try:
        res = requests.get(api_url, timeout=5).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            # 검색어와 제목이 너무 다르면 제외하는 간단한 필터링
            book_title = info.get("title", "")
            if clean_title.replace(" ", "") not in book_title.replace(" ", "") and len(results) > 0:
                continue

            links = info.get("imageLinks", {})
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            
            if img_url:
                img_url = img_url.replace("http://", "https://")
                if "google" in img_url: img_url = img_url.split("&")[0] + "&fife=w800"
                
                results.append({
                    "url": img_url,
                    "title": book_title,
                    "date": info.get("publishedDate", "미상")[:4]
                })
    except:
        pass
    return results

st.title("📖 나의 독서 기록")
st.markdown("💡 **입력 예시:** `불편한 편의점 / 해리포터 / 파친코` (구분은 **/** 로)")

with st.form("search_form"):
    titles_input = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터와 마법사의 돌")
    submit_button = st.form_submit_button("정확한 표지 찾기 🔍")

if submit_button and titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('정확한 도서 데이터를 필터링 중...'):
        st.session_state.temp_results = {title: search_books_refined(title) for title in titles}

if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.error(f"'{title}' 정보를 찾지 못했습니다.")
            continue
        
        cols = st.columns(5)
        for idx, res in enumerate(results):
            with cols[idx % 5]:
                img_obj = get_image_safe(res['url'])
                if img_obj:
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"{res['title'][:15]}... ({res['date']})")
                    if st.button("이 표지 선택", key=f"btn_{title}_{idx}"):
                        st.session_state.selected_images[title] = img_obj
                        st.toast("보관함에 담겼습니다!")

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
                curr_x, curr_y = 100, curr_y + TARGET_H_PX + margin
            sheet.paste(img_resized, (curr_x, curr_y))
            curr_x += target_w_px + margin
            
        st.image(sheet, caption="최종 인쇄용 미리보기", use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 파일 다운로드", buf.getvalue(), "book_stickers.png", "image/png")