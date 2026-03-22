import streamlit as st
import requests
from PIL import Image
import io

# 📏 인쇄 규격 (세로 4cm)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}

def search_books(query):
    """차단 가능성을 최소화한 검색 로직"""
    # 국내 도서 검색을 위해 'langRestrict=ko' 옵션을 추가했습니다.
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&langRestrict=ko"
    try:
        res = requests.get(url, timeout=5).json()
        return res.get('items', [])
    except:
        return []

st.title("📖 나의 독서 기록")
st.markdown("💡 검색창에 책 제목을 입력하고 **Enter**를 눌러주세요.")

# 검색창
query = st.text_input("책 제목을 입력하세요", placeholder="예: 불편한 편의점")

if query:
    with st.spinner('표지를 검색하고 있습니다...'):
        items = search_books(query)
        
        if not items:
            st.error("⚠️ 검색 결과를 가져오지 못했습니다. 제목을 더 짧게 입력하거나 잠시 후 다시 시도해 주세요.")
        else:
            cols = st.columns(4)
            for idx, item in enumerate(items):
                info = item.get('volumeInfo', {})
                img_links = info.get('imageLinks', {})
                img_url = img_links.get('thumbnail')
                
                if img_url:
                    img_url = img_url.replace("http://", "https://")
                    with cols[idx % 4]:
                        try:
                            # 이미지를 불러와서 화면에 표시
                            img_res = requests.get(img_url)
                            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                            st.image(img, use_container_width=True)
                            st.caption(info.get('title', '제목 없음'))
                            
                            if st.button("선택", key=f"btn_{idx}"):
                                st.session_state.selected_images[info.get('title')] = img
                                st.toast("추가되었습니다!")
                        except:
                            st.write("이미지 로드 실패")

# 인쇄판 생성
if st.session_state.selected_images:
    st.divider()
    if st.button("✨ 세로 4cm 스티커 판 만들기 (A4)"):
        a4_w, a4_h = int(210/25.4*DPI), int(297/25.4*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y = 100, 100
        
        for title, img in st.session_state.selected_images.items():
            ratio = TARGET_H_PX / float(img.size[1])
            w = int(img.size[0] * ratio)
            img_res = img.resize((w, TARGET_H_PX), Image.LANCZOS)
            
            if curr_x + w > a4_w - 100:
                curr_x = 100
                curr_y += TARGET_H_PX + 40
            
            sheet.paste(img_res, (curr_x, curr_y))
            curr_x += w + 40
            
        st.image(sheet, caption="최종 인쇄용 미리보기")
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")