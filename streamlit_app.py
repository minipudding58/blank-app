import streamlit as st
import requests
from PIL import Image
import io

# 📏 인쇄 규격 (세로 4cm 고정)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}

def get_aladdin_cover(isbn13):
    """ISBN을 알면 알라딘 고화질 서버에서 직접 이미지를 가져올 수 있습니다."""
    # 알라딘의 고화질 표지 저장 규칙: cover500 경로 사용
    url = f"https://image.aladin.co.kr/product/{isbn13[:5]}/{isbn13[5:7]}/cover500/{isbn13}.jpg"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return Image.open(io.BytesIO(res.content)).convert("RGB")
    except:
        return None

def search_books_deep(query):
    """구글 데이터에서 ISBN만 쏙 뽑아내어 국내 서점 서버로 연결합니다."""
    api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&country=KR"
    results = []
    try:
        res = requests.get(api_url).json()
        for item in res.get("items", []):
            info = item.get("volumeInfo", {})
            ids = info.get("industryIdentifiers", [])
            isbn13 = next((i["identifier"] for i in ids if i["type"] == "ISBN_13"), None)
            
            if isbn13:
                results.append({"isbn": isbn13, "title": info.get("title")})
    except:
        pass
    return results

st.title("📖 나의 독서 기록")
st.markdown("💡 **국내 서점(알라딘) 서버**에서 직접 표지를 가져옵니다.")

# 🎨 이름/예시 반영
query = st.text_input("책 제목을 입력하세요!", placeholder="예: 파친코 / 불편한 편의점")

if query:
    with st.spinner('국내 서점 서버 연결 중...'):
        books = search_books_deep(query)
        
        if not books:
            st.warning("결과가 없습니다. 제목을 정확히 입력해주세요.")
        else:
            cols = st.columns(4)
            for idx, b in enumerate(books):
                with cols[idx % 4]:
                    # 💡 여기서 알라딘 서버로 직접 접속합니다!
                    img = get_aladdin_cover(b['isbn'])
                    if img:
                        st.image(img, use_container_width=True)
                        st.caption(b['title'])
                        if st.button("선택", key=f"sel_{idx}"):
                            st.session_state.selected_images[b['title']] = img
                            st.toast("보관함에 담았습니다!")

# 🖨️ 인쇄판 제작
if st.session_state.selected_images:
    st.divider()
    if st.button("세로 4cm 스티커 판 만들기 (A4) ✨"):
        # A4 용지 생성
        a4 = Image.new('RGB', (int(210/25.4*300), int(297/25.4*300)), (255,255,255))
        x, y = 150, 150
        
        for title, img in st.session_state.selected_images.items():
            ratio = TARGET_H_PX / img.size[1]
            w = int(img.size[0] * ratio)
            img_res = img.resize((w, TARGET_H_PX), Image.LANCZOS)
            
            if x + w > a4.size[0] - 150:
                x, y = 150, y + TARGET_H_PX + 50
            
            a4.paste(img_res, (x, y))
            x += w + 50
            
        st.image(a4, caption="완성된 스티커 판")
        buf = io.BytesIO()
        a4.save(buf, format="PNG")
        st.download_button("📥 이미지 다운로드", buf.getvalue(), "stickers.png")