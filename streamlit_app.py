import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정 (4cm 규격)
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록 메이커", page_icon="📖", layout="wide")

# 세션 상태 유지
if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (코드 박멸을 위한 모바일 파싱 로직) ---
query = st.text_input("책 제목을 입력하고 Enter를 누르세요!", placeholder="예: 해리포터, 불편한 편의점")

def get_clean_books(search_query):
    """지저분한 코드 잔재() 없이 순수한 제목과 이미지만 가져옵니다."""
    # 💡 성공의 열쇠: PC 버전보다 구조가 훨씬 단순한 모바일 검색 페이지 활용
    url = f"https://www.aladin.co.kr/m/msearch.aspx?SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        html = res.text
        
        # HTML 태그 기반의 안정적인 추출 (정규표현식 활용)
        img_urls = re.findall(r'src="(https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+)"', html)
        # 💡 HTML 태그 찌꺼기() 제거를 위한 강력한 제목 추출 로직
        raw_titles = re.findall(r'class="tit">(.*?)<', html)
        
        for i in range(min(len(img_urls), 8)): # 상위 8개만
            try:
                # 💡 남아있는 불순물 코드() 완전 소탕
                clean_title = re.sub(r'<.*?>', '', raw_titles[i]).strip()
                # 고화질 이미지로 변환
                img_url_hd = img_urls[i].replace("cover200", "cover500")
                if "http" in img_url_hd:
                    results.append({"title": clean_title, "url": img_url_hd})
            except:
                continue
    except:
        st.error("서버 연결 실패")
    return results

if query:
    with st.spinner(f"'{query}' 찾는 중..."):
        books = get_clean_books(query)
        if books:
            st.subheader(f"📍 '{query}' 검색 결과")
            cols = st.columns(4)
            for idx, book in enumerate(books):
                with cols[idx % 4]:
                    st.image(book['url'], use_container_width=True)
                    # 💡 이미지 밑에 코드 대신 깔끔한 제목만 표시
                    st.write(f"**{book['title']}**")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                        img_res = requests.get(book['url'])
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        st.session_state.collection.append(img)
                        st.toast("스티커 담기 완료!")
                    if c2.button("💛 위시", key=f"wi_{idx}"):
                        # 위시리스트에는 제목과 이미지 URL 모두 저장 (에러 방지)
                        if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"title": book['title'], "url": book['url'], "done": False})
                            st.toast("위시리스트 저장!")
        else:
            st.warning("결과가 없습니다.")

# --- 🎨 1:1 레이아웃 배분 ---
st.divider()
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        if st.button("🗑️ 전체 지우기"):
            st.session_state.collection = []
            st.rerun()
        
        # A4 용지 생성 로직 (300 DPI 기준)
        a4_w, a4_h = int((210/25.4)*DPI), int((297/25.4)*DPI)
        sheet = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
        curr_x, curr_y = 120, 120
        
        for img in st.session_state.collection:
            ratio = TARGET_H_PX / float(img.size[1])
            img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
            
            # 줄바꿈 로직
            if curr_x + img_res.size[0] > a4_w - 120:
                curr_x = 120
                curr_y += TARGET_H_PX + 40
            
            sheet.paste(img_res, (curr_x, curr_y))
            curr_x += img_res.size[0] + 40
            
        st.image(sheet, use_container_width=True)
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        st.download_button("📥 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")
    else:
        st.info("검색 결과에서 표지를 선택해 보세요.")

with right_col:
    st.header("📚 위시리스트 (읽을 책)")
    if not st.session_state.wishlist:
        st.info("비어있습니다.")
    else:
        for i, item in enumerate(st.session_state.wishlist):
            with st.container(border=True):
                # 💡 요청 2: 위시리스트에도 이미지 표시
                c_img, c_done, c_del = st.columns([1, 3, 1])
                c_img.image(item['url'], use_container_width=True)
                
                # 💡 요청 3: 읽음 체크박스 기능 추가
                check_label = f"chk_{i}"
                is_done = c_done.checkbox(f"{item['title']}", value=item['done'], key=check_label)
                st.session_state.wishlist[i]['done'] = is_done
                
                if is_done:
                    c_done.info("✅ 이 책을 읽었습니다!")
                
                if c_del.button("삭제", key=f"del_wish_{i}"):
                    st.session_state.wishlist.pop(i)
                    st.rerun()