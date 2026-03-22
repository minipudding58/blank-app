import streamlit as st
import requests
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖")

# 4cm 규격 설정 (300 DPI 기준 약 472픽셀)
TARGET_H_MM = 40 
DPI = 300
TARGET_H_PX = int((TARGET_H_MM / 25.4) * DPI)

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_search_results(title):
    clean_title = title.strip()
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=8"
    try:
        res = requests.get(url, timeout=5).json()
        results = []
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            if img_url:
                img_url = img_url.replace("http://", "https://") + "&fife=w800"
                results.append({"url": img_url, "title": info.get("title", "제목 없음"), "date": info.get("publishedDate", "미상")[:4]})
        return results
    except:
        return []

st.title("📖 나만의 독서 스티커 메이커")
st.write("책 구분은 **슬래시(/)**로 해주세요. 결과물은 **세로 4cm**로 자동 조절됩니다.")

titles_input = st.text_area("책 제목들 (/ 로 구분)", "불편한 편의점 / 파친코 / 슬램덩크", height=80)

if st.button("표지 검색 시작 🔍"):
    if titles_input:
        titles = [t.strip() for t in titles_input.split("/") if t.strip()]
        st.session_state.temp_results = {title: get_search_results(title) for title in titles}
    else:
        st.error("책 제목을 입력해주세요!")

# 검색 결과 선택
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"#### 📍 '{title}' 결과")
        if not results:
            st.write("결과 없음")
            continue
        cols = st.columns(4)
        for idx, res in enumerate(results):
            with cols[idx % 4]:
                st.image(res['url'], use_container_width=True)
                if st.button("선택", key=f"btn_{title}_{idx}"):
                    st.session_state.selected_images[title] = res['url']
                    st.toast(f"'{title}' 담기 완료!")

# 🖨️ 스티커 판 생성 (핵심 기능!)
if st.session_state.selected_images:
    st.divider()
    if st.button("세로 4cm 스티커 판 만들기 (인쇄용) ✨"):
        # A4 사이즈 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        
        curr_x, curr_y = 100, 100 # 여백
        margin = 40
        
        for title, url in st.session_state.selected_images.items():
            img_res = requests.get(url)
            img = Image.open(io.BytesIO(img_res.content))
            
            # 세로 4cm 고정 비율 조정
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
        st.image(sheet, caption="인쇄용 미리보기 (A4)", use_container_width=True)
        
        # 다운로드 버튼
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")