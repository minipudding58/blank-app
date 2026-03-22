import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter, defaultdict

# --- ⚙️ 1. 기본 설정 (절대 고정) ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180 

# --- 🎨 2. [UI] CSS 스타일 (상단 및 사이드바 고정 포함) ---
st.markdown(f"""
    <style>
    /* ✅ 사이드바 고정 */
    [data-testid="stSidebar"] {{
        position: fixed;
        background-color: #ffffff;
        z-index: 1000;
    }}

    /* ✅ 상단 대시보드 영역 고정 */
    .fixed-header {{
        position: fixed;
        top: 0;
        right: 0;
        left: 21rem; /* 사이드바 너비만큼 제외 */
        background-color: white;
        z-index: 999;
        padding: 10px 20px;
        border-bottom: 1px solid #eee;
    }}

    /* 본문 콘텐츠 여백 추가 (고정 헤더에 가려지지 않게) */
    .main-content {{
        margin-top: 250px; 
    }}

    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ 
        text-align: left !important; 
        border: none !important; 
        background-color: #f0f2f6 !important; 
        border-radius: 10px !important;
    }}

    .search-card {{
        background-color: #f8f9fb;
        border-radius: 15px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center !important; 
        justify-content: center;
        margin-bottom: 10px;
        min-height: 230px;
        width: 100%;
    }}

    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important;
        width: auto !important;
        object-fit: contain !important;
        margin: 0 auto !important;
        display: block !important;
    }}
    
    .field-left {{ 
        width: 100%; 
        text-align: left !important; 
        font-size: 14px; 
        color: #444; 
        font-weight: 600; 
        margin-top: 15px; 
        margin-bottom: 5px;
    }}

    .no-title-text {{
        color: rgba(0,0,0,0) !important;
        font-size: 0px !important;
        line-height: 0px !important;
        user-select: none;
    }}

    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; display: flex; flex-direction: column; justify-content: center; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; min-width: 90px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; align-items: center; }}
    .genre-subtitle {{ font-size: 20px !important; font-weight: 800 !important; border-bottom: 3px solid #87CEEB; padding-bottom: 5px; width: 100%; text-align: left !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 로직 (기존 동일) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임", placeholder="예: 치이카와")
    if st.button("입장") and u_input:
        st.session_state.user_id = u_input; st.query_params["user"] = u_input; st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": itm["url"], "genre": itm.get("genre", "미정"), "title": itm.get("title", "제목 없음"), "start": itm.get("start"), "end": itm.get("end")})
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "genre": i.get("genre", "미정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- ⬅️ 4. 사이드바 (구조 고정) ---
with st.sidebar:
    st.title("📖 MENU")
    st.write(f"**접속 유저:** {st.session_state.user_id}")
    st.divider()
    st.button("📚 내 서재 바로가기", use_container_width=True)
    st.button("🩵 위시리스트", use_container_width=True)

# --- 🏠 5. 상단 고정 대시보드 영역 ---
st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f'<div class="count-box"><div style="font-size:12px; color:#666;">{datetime.now().year}년 누적</div><div style="font-size:28px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)
with dash_col2:
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card' style='padding:10px;'><b>{g}</b><br>{c}권</div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 🔍 6. 메인 콘텐츠 (여백 적용) ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.markdown("### 🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers)
        res.encoding = 'utf-8'
        html = res.text
        
        raw_imgs = re.findall(r'src="(https://image.aladin.co.kr/product/\d+/\d+/cover[^"]+)"', html)
        raw_titles = re.findall(r'class="bo3"><b>(.*?)</b>', html)
        
        valid_books = []
        seen = set()
        for i in range(min(len(raw_imgs), len(raw_titles))):
            if raw_imgs[i] not in seen:
                seg = html.split(raw_imgs[i])[1].split('</table>')[0]
                genre_match = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', seg)
                valid_books.append({"url": raw_imgs[i], "title": raw_titles[i], "genre": genre_match[-1] if genre_match else "미정"})
                seen.add(raw_imgs[i])

        if valid_books:
            for i in range(0, min(12, len(valid_books)), 4):
                cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx < len(valid_books):
                        book = valid_books[idx]
                        with cols[j]:
                            st.markdown('<div class="search-card">', unsafe_allow_html=True)
                            st.image(book["url"])
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown(f"<div class='no-title-text'>{book['title']}</div>", unsafe_allow_html=True)
                            st.markdown("<div class='field-left'>분야</div>", unsafe_allow_html=True)
                            g_val = st.text_input("분야", value=book["genre"], key=f"s_gen_{idx}", label_visibility="collapsed")
                            
                            c1, c2 = st.columns(2)
                            if c1.button("📖 읽음", key=f"s_br_{idx}", use_container_width=True):
                                img_data = requests.get(book["url"]).content
                                st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": book["url"], "genre": g_val, "title": book["title"]})
                                save_all(); st.rerun()
                            if c2.button("🩵 위시", key=f"s_bw_{idx}", use_container_width=True):
                                st.session_state.wishlist.append({"url": book["url"], "genre": g_val, "title": book["title"]})
                                save_all(); st.rerun()
    except Exception as e:
        st.error(f"오류: {e}")

st.markdown('</div>', unsafe_allow_html=True)