import streamlit as st
import requests
from PIL import Image
import io

# 📏 인쇄 규격 설정 (300 DPI 기준 세로 4cm는 약 472픽셀)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

# 🎨 이름 변경 1: 페이지 제목 설정
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {} # {제목: 실제이미지데이타}
if 'temp_results' not in st.session_state:
    st.session_state.temp_results = {}

def get_valid_image(url):
    """URL에서 이미지를 안전하게 가져옵니다. 엑박 방지 핵심 로직!"""
    try:
        # http 주소라면 https로 강제 변경
        secure_url = url.replace("http://", "https://")
        response = requests.get(secure_url, timeout=10, verify=False) # 보안 인증 우회 (임시)
        if response.status_code == 200:
            # 가져온 데이터가 진짜 이미지인지 PIL로 확인
            img = Image.open(io.BytesIO(response.content))
            return img # 성공 시 PIL 이미지 객체 반환
    except Exception as e:
        print(f"이미지 로드 실패: {url}, 에러: {e}")
    return None # 실패 시 None 반환

def search_book_covers(title):
    clean_title = title.strip()
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=10&country=KR"
    results = []
    try:
        res = requests.get(url, timeout=10).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            links = info.get("imageLinks", {})
            img_url = links.get("extraLarge") or links.get("large") or links.get("thumbnail")
            
            if img_url:
                # 구글 이미지일 경우 고화질 옵션 추가
                if "google" in img_url:
                    img_url = img_url.split("&")[0] + "&fife=w800"
                
                results.append({
                    "url": img_url,
                    "title": info.get("title", "제목 없음"),
                    "date": info.get("publishedDate", "미상")[:4]
                })
    except:
        pass
    return results

# 🎨 이름 변경 2: 메인 화면 타이틀
st.title("📖 나의 독서 기록")

# --- 🎨 요청 반영: 입력 예시 수정 (슬램덩크 삭제) ---
st.markdown("💡 **입력 예시:** `불편한 편의점 / 해리포터 / 파친코` (구분은 **/** 로)")

titles_input = st.text_input("책 제목을 입력하고 **Enter**를 누르세요!", placeholder="여기에 제목 입력...")

if titles_input:
    titles = [t.strip() for t in titles_input.split("/") if t.strip()]
    with st.spinner('최신 표지를 검색하는 중... (엑박은 자동으로 걸러집니다)'):
        st.session_state.temp_results = {title: search_book_covers(title) for title in titles}

# 🔍 표지 선택 섹션
if st.session_state.temp_results:
    for title, results in st.session_state.temp_results.items():
        st.markdown(f"### 📍 '{title}' 검색 결과 (원하는 버전을 고르세요)")
        if not results:
            st.error(f"❌ '{title}' 결과를 찾지 못했습니다.")
            continue
        
        cols = st.columns(5)
        for idx, res in enumerate(results):
            with cols[idx % 5]:
                # 💡 핵심 해결책: 이미지를 화면에 보여주기 전에 실제 데이터를 가져와 봅니다.
                img_obj = get_valid_image(res['url'])
                
                if img_obj: # 진짜 이미지일 때만 보여줌 (엑박 방지)
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"{res['date']}년판")
                    if st.button("선택", key=f"btn_{title}_{idx}"):
                        # 💡 핵심 해결책: 선택 시 URL이 아니라 실제 이미지 객체를 저장합니다. (image_6.png 에러 방지)
                        st.session_state.selected_images[title] = img_obj
                        st.toast(f"'{title}' 담기 완료!")
                # img_obj가 None이면(엑박이면) 그 결과는 아예 화면에 안 뜹니다.

# 🖨️ A4 인쇄판 생성 섹션
if st.session_state.selected_images:
    st.divider()
    st.subheader("✅ 담은 스티커 목록")
    st.write(", ".join(st.session_state.selected_images.keys()))
    
    if st.button("세로 4cm 스티커 판 만들기 (인쇄용 A4) ✨"):
        # A4 사이즈 정의 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        
        curr_x, curr_y, margin = 100, 100, 40
        
        with st.spinner('A4 용지에 세로 4cm로 배치하는 중...'):
            # 💡 핵심 해결책: 이제 selected_images에는 URL이 아니라 실제 이미지 객체가 들어있어서 에러가 안 납니다.
            for title, img in st.session_state.selected_images.items():
                # 세로 4cm 고정 비율 계산
                ratio = TARGET_H_PX / float(img.size[1])
                target_w_px = int(img.size[0] * ratio)
                img_resized = img.resize((target_w_px, TARGET_H_PX), Image.LANCZOS)
                
                if curr_x + target_w_px > a4_w - 100:
                    curr_x = 100
                    curr_y += TARGET_H_PX + margin
                sheet.paste(img_resized, (curr_x, curr_y))
                curr_x += target_w_px + margin
            
        st.balloons()
        st.image(sheet, caption="인쇄용 미리보기 (A4)", use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")