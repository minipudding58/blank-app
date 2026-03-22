import streamlit as st
import requests
from PIL import Image
import io
import time

# 📏 인쇄 설정 (세로 3cm)
DPI = 300
TARGET_H_PX = int((30 / 25.4) * DPI)

st.set_page_config(page_title="알라딘 책 표지 수집기", page_icon="📚")

st.title("📚 알라딘 책 표지 자동 수집기")
st.write("추가 도구 설치 없이 **기본 기능**으로만 작동하는 버전입니다.")

if 'ready_images' not in st.session_state:
    st.session_state.ready_images = []

# 릴스 스타일 입력창
titles_raw = st.text_area("책 제목을 한 줄에 하나씩 입력하세요:", placeholder="불편한 편의점\n파친코", height=150)

def search_aladdin_no_bs4(title):
    """도구(bs4) 없이 알라딘 서버에서 이미지 주소를 직접 낚아챕니다."""
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={title}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(search_url, headers=headers, timeout=5)
        text = res.text
        # 이미지 주소 패턴을 직접 찾습니다.
        if 'image.aladin.co.kr/product/' in text:
            start_key = 'https://image.aladin.co.kr/product/'
            start_idx = text.find(start_key)
            if start_idx == -1:
                start_key = 'http://image.aladin.co.kr/product/'
                start_idx = text.find(start_key)
            
            end_idx = text.find('"', start_idx)
            img_url = text[start_idx:end_idx]
            # 고화질 변환 로직 적용
            return img_url.replace("cover200", "cover500")
    except:
        return None
    return None

if st.button("🚀 스티커 판 만들기 시작!"):
    if not titles_raw.strip():
        st.warning("제목을 입력해주세요!")
    else:
        titles = [t.strip() for t in titles_raw.split('\n') if t.strip()]
        st.session_state.ready_images = []
        
        status = st.empty()
        for idx, title in enumerate(titles):
            status.text(f"🔍 '{title}' 찾는 중... ({idx+1}/{len(titles)})")
            img_url = search_aladdin_no_bs4(title)
            
            if img_url:
                try:
                    img_res = requests.get(img_url, timeout=5)
                    img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                    st.session_state.ready_images.append(img)
                except:
                    st.write(f"❌ {title}: 이미지 로드 실패")
            else:
                st.write(f"❌ {title}: 표지를 찾을 수 없음")
            time.sleep(0.3)
            
        status.text("✅ 모든 표지 수집 완료!")

# 결과물 정렬 및 다운로드
if st.session_state.ready_images:
    st.divider()
    a4_w, a4_h = int(210/25.4*DPI), int(297/25.4*DPI)
    sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
    curr_x, curr_y = 100, 100
    
    for img in st.session_state.ready_images:
        ratio = TARGET_H_PX / float(img.size[1])
        w = int(img.size[0] * ratio)
        img_resized = img.resize((w, TARGET_H_PX), Image.LANCZOS)
        
        if curr_x + w > a4_w - 100:
            curr_x = 100
            curr_y += TARGET_H_PX + 40
        
        sheet.paste(img_resized, (curr_x, curr_y))
        curr_x += w + 40
    
    st.image(sheet, caption="A4 인쇄 미리보기")
    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    st.download_button("📥 파일 다운로드", buf.getvalue(), "my_stickers.png", "image/png")