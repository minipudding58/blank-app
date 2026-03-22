import streamlit as st
import requests
from PIL import Image
import io

# 📏 인쇄 규격 설정 (300 DPI 기준 세로 4cm는 약 472픽셀)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_korean_covers(title):
    """국내 도서 표지 검색 성공률을 극대화합니다."""
    clean_title = title.strip()
    # 구글 API를 기본으로 하되 한국 지역 설정을 강화합니다.
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=12&country=KR"
    results = []
    try:
        res = requests.get(url, timeout=5).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            # 고화질 이미지부터 확인
            img_url = links.get("extraLarge") or links.get("large") or links.get("medium") or links.get("thumbnail")
            
            if img_url:
                img_url = img_url.replace("http://", "https://")
                # 구글 이미지일 경우 fife=w800 옵션으로 고화질 강제 전환
                if "google" in img_url:
                    img_url = img_url.split("&")[0] + "&fife=w800"
                
                results.append({
                    "url": img_url,
                    "title": info.get("title", "제목 없음"),
                    "date": info.get("publishedDate", "날짜 미상")[:4]
                })
    except:
        pass
    return results

st.title("📖 나만의 독서 스티커 메이커")

# --- 💡 요청 반영: 예시 목록을 입력창 위로 배치 ---
st.markdown("💡 **입력 예시:** `불편한 편의점 / 해리포터 / 슬램덩크` (구분은 **/** 로)")

# --- 💡 요청 반영: 엔터 치면 검색되는 한 줄 입력창 ---
titles_input = st.text_input("책 제목을 입력하고 **Enter**를 누르세요!", placeholder="여기에 제목 입력...")

if titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('표지를 찾는 중...'):
        st.session_state.temp_results = {title: get_korean_covers(title) for title in titles}

# 🔍 표지 선택 섹션
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과 (원하는 버전을 고르세요)")
        if not results:
            st.error(f"'{title}' 결과를 찾지 못했습니다. 작가 이름을 붙여보세요! (예: {title} 김호연)")
            continue
        
        cols = st.columns(5)
        for idx, res in enumerate(results):
            with cols[idx % 5]:
                try:
                    st.image(res['url'], use_container_width=True)
                    st.caption(f"{res['date']}년판")
                    if st.button("선택", key=f"btn_{title}_{idx}"):
                        st.session_state.selected_images[title] = res['url']
                        st.toast(f"'{title}' 담기 완료!")
                except:
                    st.write("이미지 로딩 실패")

# 🖨️ A4 세로 4cm 정렬 섹션 (최종 목적)
if st.session_state.selected_images:
    st.divider()
    st.subheader("✅ 담은 스티커 목록")
    st.write(", ".join(st.session_state.selected_images.keys()))
    
    if st.button("세로 4cm 스티커 판 만들기 (인쇄용 A4) ✨"):
        # A4 사이즈 정의 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        
        # 시작 좌표 및 간격
        curr_x, curr_y = 100, 100
        margin = 40
        
        with st.spinner('A4 용지에 세로 4cm로 배치하는 중...'):
            for title, url in st.session_state.selected_images.items():
                img_res = requests.get(url)
                img = Image.open(io.BytesIO(img_res.content))
                
                # --- 세로 4cm 고정 로직 ---
                ratio = TARGET_H_PX / float(img.size[1])
                target_w_px = int(img.size[0] * ratio)
                img_resized = img.resize((target_w_px, TARGET_H_PX), Image.LANCZOS)
                
                # 다음 줄로 넘기기 체크
                if curr_x + target_w_px > a4_w - 100:
                    curr_x = 100
                    curr_y += TARGET_H_PX + margin
                
                sheet.paste(img_resized, (curr_x, curr_y))
                curr_x += target_w_px + margin
            
        st.image(sheet, caption="인쇄용 미리보기 (A4)", use_container_width=True)
        
        # 다운로드 버튼
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")