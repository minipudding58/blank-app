import streamlit as st
import requests
import re
from PIL import Image
import io
from datetime import date

# --- ⚙️ 1. 페이지 설정 ---
st.set_page_config(page_title="독서 기록장", layout="wide")

# --- 🎨 2. 상단 및 사이드바 고정 CSS ---
st.markdown("""
    <style>
    /* 상단 헤더 고정 */
    [data-testid="stHeader"] {
        position: fixed;
        top: 0;
        background-color: white;
        z-index: 999;
    }
    
    /* 검색창 및 입력창 배경색 */
    div[data-baseweb="input"] {
        background-color: #f0f2f6 !important;
        border-radius: 10px !important;
    }

    /* 검색 결과 카드 디자인 (회색 배경) */
    .search-item {
        background-color: #f8f9fb;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* 이미지 높이 제한 */
    .search-item img {
        height: 180px;
        object-fit: contain;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ⬅️ 3. 사이드바 (고정 영역) ---
with st.sidebar:
    st.title("📂 메뉴")
    st.write(f"**사용자:** {st.query_params.get('user', 'Guest')}")
    st.divider()
    st.button("내 서재 바로가기")
    st.button("위시리스트")

# --- 🔍 4. 상단 검색바 및 결과 (메인 영역) ---
st.title("🔍 책 검색")
q = st.text_input("검색어를 입력하세요...", placeholder="책 제목 입력", label_visibility="collapsed")

if q:
    try:
        # 알라딘 검색 로직 (강력한 패턴 매칭)
        url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        html = res.text
        
        # 이미지, 제목, 장르 추출
        imgs = re.findall(r'src="(https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+)"', html)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', html)
        
        books = []
        seen = set()
        for i in range(min(len(imgs), len(titles))):
            if imgs[i] not in seen:
                # 장르 파싱
                seg = html.split(imgs[i])[1].split('</table>')[0]
                genre = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', seg)
                books.append({"url": imgs[i], "title": titles[i], "genre": genre[-1] if genre else "미정"})
                seen.add(imgs[i])

        if books:
            # 검색 결과 출력 (화면 너비에 따라 자동 조절)
            cols = st.columns(4) 
            for idx, book in enumerate(books[:12]):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="search-item">
                        <img src="{book['url']}">
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 기능 버튼들
                    new_genre = st.text_input("분야", value=book['genre'], key=f"g_{idx}")
                    with st.expander("기록 설정"):
                        st.date_input("날짜", value=date.today(), key=f"d_{idx}")
                    
                    c1, c2 = st.columns(2)
                    c1.button("📖 읽음", key=f"r_{idx}", use_container_width=True)
                    c2.button("🩵 위시", key=f"w_{idx}", use_container_width=True)
        else:
            st.warning("결과를 찾을 수 없습니다.")
    except Exception as e:
        st.error("데이터를 가져오는 중 오류가 발생했습니다.")