import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정 (4cm 규격)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 유지
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (강력한 추출 로직으로 교체) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

def get_books_fixed(search_query):
    """코드 잔재()를 완벽히 제거하고 검색 결과를 복구합니다."""
    # 모바일 페이지가 데이터 구조가 훨씬 깔끔하여 이를 활용합니다.
    url = f"https://www.aladin.co.kr/m/msearch.aspx?SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        html = res.text
        
        # 1. 도서 블록 단위로 쪼개기
        items = html.split('<div class="ms_book_box">')
        for item in items[1:9]:  # 최대 8개
            try:
                # 이미지 추출 (코드 찌꺼기 없는 순수 URL)
                img_match = re.search(r'src="(https://image.aladin.co.kr/product/[^"]+)"', item)
                img_url = img_match.group(1).replace("cover200", "cover500") if img_match else ""
                
                # 제목 추출 (HTML 태그와 불필요한 숫자들 제거)
                title_match = re.search(r'class="tit">(.*?)<', item)
                title = title_match.group(1).strip() if title_match else "제목 없음"
                # 💡 지저분한 HTML 코드() 완전 소탕
                title = re.sub(r'<.*?>', '', title)
                
                if img_url:
                    results.append({"title": title, "url": img_url})
            except:
                continue
    except:
        st.error("알라딘 서버 연결에 실패했습니다.")
    return results

if query:
    with st.spinner("책 정보를 불러오는 중..."):
        books = get_books_fixed(query)
        if books:
            st.subheader(f"📍 '{query}' 검색 결과")
            cols = st.columns(4)
            for idx, book in enumerate(books):
                with cols[idx % 4]:
                    st.image(book['url'], use_container_width=True)
                    # 💡 이미지 하단에 코드 잔재가 절대 나오지 않게 처리
                    st.write(f"**{book['title']}**")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                        img_res = requests.get(book['url'])
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        st.session_state.collection.append(img)
                        st.toast("스티커 판에 추가되었습니다!")
                    if c2.button("💛 위시", key=f"wi_{idx}"):
                        if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"title": book['title'], "url": book['url'], "done": False})
                            st.toast("위시리스트에 담았습니다!")
        else:
            st.warning("검색 결과가 없습니다. 제목을 다시 확인해 주세요.")

# --- 🎨 1:1 이분할 레이아웃 ---
st.divider()
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        if st.button("🗑️ 전체 비우기"):
            st.session_state.collection = []
            st.rerun()
        
        # A4 캔버스 생성
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        x, y = 120, 120
        
        for img in st.session_state.collection:
            ratio = TARGET_H_PX / float(img.size[1])
            img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
            if x + img_res.size[0] > a4_w - 120:
                x = 120
                y += TARGET_H_PX + 40
            sheet.paste(img_res, (x, y))
            x += img_res.size[0] + 40
            
        st.image(sheet, use_container_width=True)
        buf = io.BytesIO(); sheet.save(buf, format="PNG")
        st.download_button("📥 이미지 다운로드", buf.getvalue(), "stickers.png", "image/png")
    else:
        st.info("검색 결과에서 '스티커' 버튼을 눌러보세요.")

with right_col:
    st.header("📚 읽고 싶은 책 (위시리스트)")
    if not st.session_state.wishlist:
        st.info("나중에 읽을 책을 위시리스트에 담아보세요.")
    else:
        for i, item in enumerate(st.session_state.wishlist):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                # 💡 위시리스트에도 책 표지가 나오도록 수정
                c1.image(item['url'], width=65)
                
                # 💡 읽음 체크박스 기능
                check_label = f" {item['title']}"
                is_done = c2.checkbox(check_label, value=item['done'], key=f"chk_{i}")
                st.session_state.wishlist[i]['done'] = is_done
                
                if is_done:
                    c2.info("✅ 이 책을 읽었습니다!")
                
                if c3.button("삭제", key=f"del_{i}"):
                    st.session_state.wishlist.pop(i)
                    st.rerun()