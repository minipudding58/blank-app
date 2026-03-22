import streamlit as st
import requests
import re
from PIL import Image
import io
import json
import os
from datetime import date

# --- ⚙️ 1. 페이지 설정 (수정 금지) ---
st.set_page_config(page_title="나의 독서 기록장", layout="wide")

# --- 🎨 2. UI 스타일 (사용자 가이드라인 고정) ---
st.markdown("""
    <style>
    /* 상단 및 입력창 디자인 고정 */
    div[data-baseweb="input"] {
        background-color: #f0f2f6 !important;
        border-radius: 10px !important;
    }
    /* 검색 결과 카드 디자인 */
    .search-card {
        background-color: #f8f9fb;
        border-radius: 15px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 250px;
        margin-bottom: 10px;
    }
    [data-testid="stImage"] img {
        height: 180px !important;
        object-fit: contain !important;
    }
    .field-left { 
        width: 100%; text-align: left; font-size: 14px; 
        color: #444; font-weight: 600; margin-top: 10px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- ⬅️ 3. 사이드바 (사용자 요청 구조 고정) ---
with st.sidebar:
    st.title("📖 MENU")
    u_id = st.query_params.get("user", "Guest")
    st.write(f"**사용자:** {u_id}")
    st.divider()
    st.button("📚 내 서재", use_container_width=True)
    st.button("🩵 위시리스트", use_container_width=True)

# --- 🔝 4. 상단 헤더 (사용자 요청 구조 고정) ---
st.title("🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed")

# --- 🔍 5. 검색 결과 출력 (로직만 최신으로 교체) ---
if q:
    try:
        # 알라딘 검색 우회 로직 (결과 누락 방지)
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        html = res.text
        
        # 이미지와 제목 파싱
        imgs = re.findall(r'src="(https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+)"', html)
        titles = re.findall(r'class="bo3"><b>(.*?)</b>', html)
        
        valid_books = []
        seen = set()
        for i in range(min(len(imgs), len(titles))):
            if imgs[i] not in seen:
                # 장르 추출
                try:
                    seg = html.split(imgs[i])[1].split('</table>')[0]
                    genre_m = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', seg)
                    genre = genre_m[-1] if genre_m else "미정"
                except: genre = "미정"
                
                valid_books.append({"url": imgs[i], "title": titles[i], "genre": genre})
                seen.add(imgs[i])

        if valid_books:
            # 가로 4열 배치 출력
            cols = st.columns(4)
            for idx, book in enumerate(valid_books[:12]):
                with cols[idx % 4]:
                    st.markdown('<div class="search-card">', unsafe_allow_html=True)
                    st.image(book["url"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("<div class='field-left'>분야</div>", unsafe_allow_html=True)
                    g_val = st.text_input("분야", value=book["genre"], key=f"gen_{idx}", label_visibility="collapsed")
                    
                    c1, c2 = st.columns(2)
                    c1.button("📖 읽음", key=f"r_{idx}", use_container_width=True)
                    c2.button("🩵 위시", key=f"w_{idx}", use_container_width=True)
        else:
            st.warning("검색 결과가 없습니다.")
    except Exception as e:
        st.error(f"검색 실패: {e}")

st.divider()
st.subheader("📚 나의 서재")