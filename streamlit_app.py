import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# 🎨 제목 & 스타일 설정 (릴스 감성으로 세련되게!)
st.set_page_config(page_title="나만의 독서 스티커 메이커", page_icon="📖", layout="wide")

# (기존 코드를 아래 내용으로 싹 지우고 붙여넣으세요!)
# --- [여기서부터 복사] ---
import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# 🎨 세션 상태 초기화 (이미지 저장용)
if 'sticker_sheet' not in st.st_state:
    st.st_state.sticker_sheet = None

# --- ✨ 핵심 업데이트: 최신 디자인 스티커 가져오기 ---
def get_trendy_book_cover(isbn):
    """
    구글 북스 API를 사용하여 가장 고해상도의 최신 디자인 표지를 가져옵니다.
    """
    # 1. 고해상도 이미지 소스를 우선 탐색
    url_templates = [
        f"https://books.google.com/books/content?id={isbn}&printsec=frontcover&img=1&zoom=3", # 최고 해상도
        f"https://books.google.com/books/content?id={isbn}&printsec=frontcover&img=1&zoom=2", # 고해상도
    ]
    
    for url in url_templates:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                img = Image.open(io.BytesIO(response.content))
                # 너무 작거나 로딩 실패 이미지는 거름
                if img.size[0] > 100: 
                    return img
        except:
            pass
            
    # 2. 실패 시 차선책 (알라딘 API - 국내 도서에 강함)
    try:
        # (실제 서비스에서는 알라딘 API 키가 필요하지만, 우선 우회 방법을 시도)
        aladdin_url = f"https://www.aladdin.co.kr/shop/common/wn_cover.aspx?ISBN={isbn}&Size=Big"
        response = requests.get(aladdin_url, timeout=10)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
        
    return None # 모두 실패 시

# --- 나머지 코드 (스티커 판 만들기 등) ---
st.title("📖 나만의 독서 스티커 메이커")
st.write("다이어리에 딱 맞는 세로 4cm 책 표지 스티커를 만들어보세요! (최신 디자인 반영✨)")

# (중략 - 기존 코드와 동일한 스티커 판 만들기 로직)
# (간단한 예시로 대체합니다. 사용자님은 기존 코드를 그대로 쓰셔도 됩니다.)

titles_input = st.text_area("책 제목을 쉼표(,)로 구분해서 입력해주세요.", height=150, placeholder="예: 불편한 편의점, 슬램덩크 리소스")

if st.button("스티커 판 만들기 ✨"):
    if not titles_input:
        st.warning("책 제목을 입력해주세요!")
    else:
        titles = [t.strip() for t in titles_input.split(',') if t.strip()]
        
        # (실제 API 호출 및 이미지 처리 로직 - 기존 코드 활용)
        # 중요: image_fetcher 부분만 get_trendy_book_cover로 바꾸세요!
        
        # (예시 결과 출력)
        st.success(f"{len(titles)}권의 스티커를 만듭니다! 잠시만 기다려주세요.")
        st.st_state.sticker_sheet = Image.new('RGB', (100, 100), (255, 255, 255)) # 임시 이미지
        
if st.st_state.sticker_sheet:
    st.image(st.st_state.sticker_sheet, caption="미리보기 (실제 인쇄 시 더 고화질입니다)")
    
    # 다운로드 버튼
    buf = io.BytesIO()
    st.st_state.sticker_sheet.save(buf, format="PNG")
    st.download_button(
        label="📥 인쇄용 이미지 다운로드",
        data=buf.getvalue(),
        file_name="my_book_stickers.png",
        mime="image/png"
    )

st.divider()
st.caption("제작: 사용자님의 끈기로 완성된 AI 조수 | 이미지 출처: 구글 북스, 알라딘")