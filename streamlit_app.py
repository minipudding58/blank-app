import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import time

# 📏 설정 (세로 3cm 규격)
DPI = 300
TARGET_H_PX = int((30 / 25.4) * DPI) # 릴스처럼 세로 3cm로 설정

st.set_page_config(page_title="알라딘 책 표지 자동 수집기", page_icon="📚")

# 스타일 설정 (릴스 느낌 UI)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 알라딘 책 표지 자동 수집기")
st.write("책 제목을 입력하면 세로 **3cm**에 맞춰진 인쇄용 파일을 만들어줍니다!")

# 세션 상태 저장
if 'ready_images' not in st.session_state:
    st.session_state.ready_images = []

# 입력창
titles_raw = st.text_area("책 제목을 한 줄에 하나씩 입력하세요:", placeholder="불편한 편의점\n파친코\n해리포터", height=150)

def search_aladdin_direct(title):
    """알라딘 검색 결과 페이지에서 실제 표지 주소를 추출합니다."""
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={title}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 알라딘 검색 결과에서 첫 번째 책 이미지 태그 찾기
        img_tag = soup.select_one(".ss_book_box img.front_cover")
        if img_tag:
            return img_tag['src'].replace("cover200", "cover500") # 고화질로 변경
    except:
        return None
    return None

if st.button("🚀 PDF/이미지 만들기 시작!"):
    if not titles_raw.strip():
        st.warning("제목을 입력해주세요!")
    else:
        titles = [t.strip() for t in titles_raw.split('\n') if t.strip()]
        st.session_state.ready_images = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, title in enumerate(titles):
            status_text.text(f"'{title}' 표지 찾는 중... ({idx+1}/{len(titles)})")
            img_url = search_aladdin_direct(title)
            
            if img_url:
                try:
                    img_res = requests.get(img_url, timeout=5)
                    img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                    st.session_state.ready_images.append(img)
                except:
                    st.write(f"❌ {title}: 이미지를 불러올 수 없습니다.")
            else:
                st.write(f"❌ {title}: 검색 결과가 없습니다.")
            
            progress_bar.progress((idx + 1) / len(titles))
            time.sleep(0.5) # 서버 부하 방지
            
        status_text.text("✅ 수집 완료!")

# 결과물 정렬 및 다운로드
if st.session_state.ready_images:
    st.divider()
    # A4 용지 생성
    a4_w, a4_h = int(210/25.4*DPI), int(297/25.4*DPI)
    sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
    curr_x, curr_y = 100, 100
    margin = 40
    
    for img in st.session_state.ready_images:
        ratio = TARGET_H_PX / float(img.size[1])
        w = int(img.size[0] * ratio)
        img_resized = img.resize((w, TARGET_H_PX), Image.LANCZOS)
        
        if curr_x + w > a4_w - 100:
            curr_x = 100
            curr_y += TARGET_H_PX + margin
        
        sheet.paste(img_resized, (curr_x, curr_y))
        curr_x += w + margin
    
    st.image(sheet, caption="인쇄 미리보기")
    
    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    st.download_button("📥 인쇄용 파일 다운로드", buf.getvalue(), "book_stickers.png", "image/png")