import streamlit as st
import requests
from PIL import Image
import io
import time

# 📏 인쇄 규격 (300 DPI 기준 세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

# 🎨 이름 변경 반영
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_valid_image(url):
    """이미지 통로가 막혔을 때 우회해서 가져오는 로직"""
    try:
        # 가짜 브라우저처럼 위장해서 접근 (보안 차단 회피)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            return img
    except:
        pass
    return None

def search_books(title):
    """구글 도서관이 응답하지 않을 때를 대비해 여러 번 시도합니다."""
    clean_title = title.strip()
    # 한국 도서 우선 검색 옵션 강화
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=8&country=KR"
    
    for _ in range(2): # 실패 시 2번까지 재시도
        try:
            res = requests.get(url, timeout=5).json()
            items = res.get("items", [])
            if items:
                results = []
                for item in items:
                    info = item.get("volumeInfo", {})
                    links = info.get("imageLinks", {})
                    img_url = links.get("extraLarge") or links.get("large") or links.get("thumbnail")
                    if img_url:
                        img_url = img_url.replace("http://", "https://")
                        if "google" in img_url: img_url = img_url.split("&")[0] + "&fife=w800"
                        results.append({"url": img_url, "title": info.get("title", title), "date": info.get("publishedDate", "미상")[:4]})
                return results
        except:
            time.sleep(1) # 1초 쉬고 다시 시도
    return []

# 🎨 타이틀 및 예시 수정
st.title("📖 나의 독서 기록")
st.markdown("💡 **입력 예시:** `불편한 편의점 / 해리포터 / 파친코` (구분은 **/** 로)")

titles_input = st.text_input("책 제목을 입력하고 **Enter**를 누르세요!", placeholder="예: 파친코")

if titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('끈질기게 표지를 찾아오는 중...'):
        # 검색 결과가 하나라도 나올 때까지 시도
        st.session_state.temp_results = {title: search_books(title) for title in titles}

# 🔍 검색 결과 표시
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과")
        if not results:
            st.warning(f"'{title}' 결과를 가져오지 못했습니다. 잠시 후 다시 엔터를 쳐보세요!")
            continue
        
        cols = st.columns(4)
        for idx, res in enumerate(results):
            with cols[idx % 4]:
                img_obj = get_valid_image(res['url'])
                if img_obj:
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"{res['date']}년판")
                    if st.button("선택", key=f"btn_{title}_{idx}"):
                        st.session_state.selected_images[title] = img_obj
                        st.toast(f"'{title}' 담기 완료!")

# 🖨️ 인쇄판 생성 (A4 정렬)
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
            
        st.image(sheet, caption="인쇄용 미리보기 (세로 4cm 고정)", use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")