import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정 (세로 4cm 기준)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# 세션 상태 초기화
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (가장 안정적인 파싱 로직) ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터, 불편한 편의점")

def get_books_stable(search_query):
    """지저분한 코드 없이 책 정보만 확실하게 가져옵니다."""
    # PC보다 변화가 적은 모바일 검색 페이지 활용
    url = f"https://www.aladin.co.kr/m/msearch.aspx?SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        # 💡 HTML 구조를 직접 쪼개서 제목과 이미지만 추출 (코드 잔재 방지)
        items = res.text.split('<div class="ms_book_box">')
        for item in items[1:9]:
            try:
                # 이미지 URL 추출
                img_start = item.find('src="') + 5
                img_end = item.find('"', img_start)
                img_url = item[img_start:img_end].replace("cover200", "cover500")
                
                # 제목 추출 및 불순물 제거
                title_start = item.find('class="tit">') + 12
                title_end = item.find('<', title_start)
                clean_title = re.sub(r'<.*?>', '', item[title_start:title_end]).strip()
                
                if "http" in img_url:
                    results.append({"title": clean_title, "url": img_url})
            except: continue
    except: pass
    return results

if query:
    with st.spinner("알라딘에서 정보를 가져오는 중..."):
        books = get_books_stable(query)
        if books:
            st.subheader(f"📍 '{query}' 검색 결과")
            cols = st.columns(4)
            for idx, book in enumerate(books):
                with cols[idx % 4]:
                    st.image(book['url'], use_container_width=True)
                    # 💡 제목만 깔끔하게 표시 (코드 잔재 소탕)
                    st.write(f"**{book['title']}**")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                        r = requests.get(book['url'])
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append(img)
                        st.toast("인쇄판에 추가되었습니다!")
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
    st.header("🖨️ 읽은 책 모음 (인쇄용 A4)")
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
        st.download_button("📥 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")
    else:
        st.info("검색 결과에서 '스티커'를 누르면 여기에 담깁니다.")

with right_col:
    st.header("📚 읽고 싶은 책 (위시리스트)")
    if not st.session_state.wishlist:
        st.info("나중에 읽을 책을 보관하세요.")
    else:
        for i, item in enumerate(st.session_state.wishlist):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                # ✅ 위시리스트 책 이미지 표시
                c1.image(item['url'], width=65)
                # ✅ 읽음 체크박스 기능
                is_done = c2.checkbox(f"{item['title']}", value=item['done'], key=f"chk_{i}")
                st.session_state.wishlist[i]['done'] = is_done
                if is_done: c2.success("✅ 읽기 완료!")
                
                if c3.button("삭제", key=f"del_{i}"):
                    st.session_state.wishlist.pop(i)
                    st.rerun()