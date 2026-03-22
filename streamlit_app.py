import streamlit as st
import requests
from PIL import Image
import io
import re

# 📏 인쇄 설정
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'collection' not in st.session_state: st.session_state.collection = []
if 'wishlist' not in st.session_state: st.session_state.wishlist = []

st.title("📖 나의 독서 기록 관리")

# --- 🔍 검색 엔진 (가장 원시적이고 확실한 방식) ---
query = st.text_input("책 제목을 입력하고 Enter!", placeholder="예: 해리포터")

def get_data_raw(search_query):
    # 아까 잘 나왔던 PC 버전 주소로 다시 돌아갑니다.
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        # 복잡한 필터 없이 이미지와 제목을 최대한 많이 긁어옵니다.
        img_urls = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+', res.text)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', res.text)
        
        for i in range(min(len(img_urls), 8)):
            # 코드가 조금 섞이더라도 제목을 최대한 살립니다.
            t = titles[i] if i < len(titles) else "제목 없음"
            results.append({"title": t, "url": img_urls[i]})
    except:
        st.error("알라딘 서버와 통신이 원활하지 않습니다.")
    return results

if query:
    books = get_data_raw(query)
    if books:
        st.subheader(f"📍 '{query}' 검색 결과")
        cols = st.columns(4)
        for idx, book in enumerate(books):
            with cols[idx % 4]:
                st.image(book['url'], use_container_width=True)
                # 제목 아래 코드가 보일 수 있지만, 검색 결과를 우선시했습니다.
                st.caption(book['title']) 
                
                c1, c2 = st.columns(2)
                if c1.button("🖼️ 스티커", key=f"st_{idx}"):
                    img_res = requests.get(book['url'])
                    img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                    st.session_state.collection.append(img)
                    st.toast("인쇄판 추가!")
                if c2.button("💛 위시", key=f"wi_{idx}"):
                    if not any(d['title'] == book['title'] for d in st.session_state.wishlist):
                        st.session_state.wishlist.append({"title": book['title'], "url": book['url'], "done": False})
                        st.toast("위시리스트 추가!")
    else:
        st.warning("검색 결과가 없습니다. 다시 검색해 보세요.")

# --- 🎨 1:1 레이아웃 ---
st.divider()
l_col, r_col = st.columns([1, 1])

with l_col:
    st.header("🖨️ 읽은 책 모음 (A4)")
    if st.session_state.collection:
        if st.button("🗑️ 전체 비우기"):
            st.session_state.collection = []
            st.rerun()
        
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
        st.download_button("📥 다운로드", buf.getvalue(), "books.png", "image/png")

with r_col:
    st.header("📚 위시리스트")
    if not st.session_state.wishlist:
        st.info("비어있습니다.")
    else:
        for i, item in enumerate(st.session_state.wishlist):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                # 🖼️ 위시리스트에도 이미지 표시
                c1.image(item['url'], width=60)
                # ✅ 읽음 체크 기능
                is_done = c2.checkbox(f"{item['title']}", value=item['done'], key=f"chk_{i}")
                st.session_state.wishlist[i]['done'] = is_done
                if is_done: c2.write("✅ 읽기 완료!")
                
                if c3.button("삭제", key=f"del_{i}"):
                    st.session_state.wishlist.pop(i)
                    st.rerun()