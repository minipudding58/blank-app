import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter, defaultdict

# --- ⚙️ 1. 기본 설정 ---
st.set_page_config(page_title="나의 독서 기록장", page_icon="📖", layout="wide")
TARGET_H_PX = 180

# --- 🎨 2. [UI] CSS 스타일 (원본 유지) ---
st.markdown(f"""
    <style>
    .stTextInput {{ text-align: left !important; }}
    div[data-baseweb="input"], input {{ 
        text-align: left !important; border: none !important; 
        background-color: #f0f2f6 !important; border-radius: 10px !important;
    }}
    .search-card {{
        background-color: #f8f9fb; border-radius: 15px; padding: 20px;
        display: flex; flex-direction: column; align-items: center !important; 
        justify-content: center; margin-bottom: 10px; min-height: 230px; width: 100%;
    }}
    [data-testid="stImage"] img {{
        height: {TARGET_H_PX}px !important; width: auto !important;
        object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }}
    .field-left {{ 
        width: 100%; text-align: left !important; font-size: 14px; 
        color: #444; font-weight: 600; margin-top: 15px; margin-bottom: 5px;
    }}
    .no-title-text {{
        color: rgba(0,0,0,0) !important; font-size: 0px !important;
        line-height: 0px !important; user-select: none;
    }}
    .count-box {{ text-align: center; padding: 25px; background: #f8f9fb; border-radius: 20px; border: 1px solid #eee; display: flex; flex-direction: column; justify-content: center; }}
    .genre-card {{ background-color: #ffffff; border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; min-width: 90px; margin: 5px; }}
    .genre-container {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; align-items: center; }}
    .genre-subtitle {{ font-size: 20px !important; font-weight: 800 !important; border-bottom: 3px solid #87CEEB; padding-bottom: 5px; width: 100%; text-align: left !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔗 3. 데이터 관리 ---
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
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                            "url": itm["url"], "genre": itm.get("genre", "미정"), 
                            "title": itm.get("title", "제목 없음"), "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "genre": i.get("genre", "미정"), "title": i.get("title", "제목 없음"), "start": i.get("start"), "end": i.get("end")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 상단 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
dash_col1, dash_col2 = st.columns([1, 3.5])
with dash_col1:
    st.markdown(f'<div class="count-box"><div style="font-size:14px; color:#666;">{datetime.now().year}년 누적</div><div style="font-size:38px; font-weight:bold; color:#87CEEB;">✨{len(st.session_state.collection)}권✨</div></div>', unsafe_allow_html=True)
with dash_col2:
    if st.session_state.collection:
        st.markdown("<div style='font-size:15px; font-weight:700;'>분야별(장르별) 통계</div>", unsafe_allow_html=True)
        counts = Counter([itm.get("genre", "미정") for itm in st.session_state.collection])
        genre_items_html = "".join([f"<div class='genre-card'><b>{g}</b><br><span style='color:#666;'>{c}권</span></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-container'>{genre_items_html}</div>", unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 검색 섹션 (수리된 엔진) ---
st.markdown("### 🔍 책 검색")
q = st.text_input("검색어 입력", placeholder="책 제목을 입력하세요...", label_visibility="collapsed") 

if q:
    try:
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
        # 브라우저인 척 하기 위한 헤더
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        html = res.text
        
        # 💡 핵심 수정: 이미지와 제목을 각각의 독립적인 리스트로 추출 (더 유연함)
        # 이미지: 'cover'가 포함된 모든 https 주소 추출
        imgs = re.findall(r'src="(https://image\.aladin\.co\.kr/[^"]+cover[^"]+)"', html)
        # 제목: bo3 클래스 안의 b 태그 내용 추출
        titles = re.findall(r'<a[^>]+class="bo3"[^>]*><b>(.*?)</b></a>', html)
        
        if imgs and titles:
            valid_books = []
            seen_urls = set()
            # 이미지와 제목 개수가 안 맞을 수 있으므로 루프 처리
            for i in range(min(len(imgs), len(titles))):
                if imgs[i] not in seen_urls:
                    # 분야(장르) 추출 시도
                    try:
                        seg = html.split(imgs[i])[1].split('</table>')[0]
                        genre_match = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', seg)
                        genre = genre_match[-1] if genre_match else "미정"
                    except: genre = "미정"
                    
                    valid_books.append({"url": imgs[i], "title": titles[i], "genre": genre})
                    seen_urls.add(imgs[i])

            # 4열 배치 출력
            for i in range(0, len(valid_books), 4):
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
                            g_val = st.text_input("분야수정", value=book["genre"], label_visibility="collapsed", key=f"s_gen_{idx}")
                            with st.expander("📅 기간"):
                                s_d = st.date_input("시작", value=date.today(), key=f"s_ds_{idx}")
                                e_d = st.date_input("종료", value=date.today(), key=f"s_de_{idx}")
                            b_r, b_w = st.columns(2)
                            if b_r.button("📖 읽음", key=f"s_br_{idx}", use_container_width=True):
                                img_data = requests.get(book["url"]).content
                                st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": book["url"], "genre": g_val, "title": book["title"], "start": s_d.isoformat(), "end": e_d.isoformat()})
                                save_all(); st.rerun()
                            if b_w.button("🩵 위시", key=f"s_bw_{idx}", use_container_width=True):
                                st.session_state.wishlist.append({"url": book["url"], "genre": g_val, "title": book["title"]})
                                save_all(); st.rerun()
        else:
            st.warning("검색 결과를 찾을 수 없습니다. 검색어를 확인해주세요.")
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")

# --- 📚 6. 내 서재 목록 ---
st.divider()
tab1, tab2 = st.tabs(["📚 내 서재", "🩵 위시리스트"])
with tab1:
    if st.session_state.collection:
        edit_mode = st.toggle("삭제 모드 활성화", key="lib_edit")
        grouped = defaultdict(list)
        for idx, item in enumerate(st.session_state.collection): 
            grouped[item.get('genre', '미정')].append((idx, item))
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='genre-subtitle'>{g_name}</div>", unsafe_allow_html=True)
            for k in range(0, len(g_items), 5):
                cols = st.columns(5)
                for c_idx, (orig_idx, itm) in enumerate(g_items[k:k+5]):
                    with cols[c_idx]:
                        st.image(itm["img"], use_container_width=True)
                        st.caption(f"**{itm['title'][:10]}**")
                        if edit_mode and st.button("❌", key=f"del_{orig_idx}"):
                            st.session_state.collection.pop(orig_idx); save_all(); st.rerun()