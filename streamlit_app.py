import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- 기초 규격 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 스타일 설정 (장르 카드 가로폭 축소 및 여백 제거) ---
st.markdown(f"""
    <style>
    /* 상단 여백 최소화 */
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }}
    
    /* 누적 독서 (테두리 없음) */
    .stat-container {{
        text-align: center;
        padding: 5px;
    }}

    /* ✅ 장르 카드 가로폭 및 크기 대폭 축소 */
    .genre-wrapper {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px; /* 카드 사이 간격 */
    }}
    .genre-card {{
        background-color: #f8f9fa;
        padding: 8px 12px; /* 내부 여백 줄임 */
        border-radius: 6px;
        text-align: center;
        border: 1px solid #eee;
        min-width: 80px; /* 가로 최소폭 대폭 축소 */
        max-width: 100px; /* 가로 최대폭 제한 */
    }}
    
    .section-title {{
        font-size: 19px !important;
        font-weight: bold !important;
        margin-bottom: 8px !important;
        display: block;
    }}

    /* 버튼 및 입력창 규격 유지 */
    div.stButton > button {{
        height: 40px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "User")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로드 ---
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
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": itm["url"],
                            "start": itm.get("start"), "end": itm.get("end"), "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 상단: 통계 섹션 ---
t_col1, t_col2 = st.columns([1, 3])

with t_col1:
    st.markdown(f"""
        <div class="stat-container">
            <span style='font-size: 16px; color: #666;'>{datetime.now().year}년 누적 독서</span><br>
            <span style='color:#87CEEB; font-size:48px; font-weight:bold;'>✨{len(st.session_state.collection)}권✨</span>
        </div>
    """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        # ✅ 가로로 촘촘하게 배치하기 위해 HTML 직접 구성
        genre_html = "<div class='genre-wrapper'>"
        for genre, count in counts.items():
            genre_html += f"""
                <div class='genre-card'>
                    <div style='font-size: 12px; color: #888;'>{genre}</div>
                    <div style='font-size: 16px; font-weight: bold; color: #333;'>{count}권</div>
                </div>
            """
        genre_html += "</div>"
        st.markdown(genre_html, unsafe_allow_html=True)
    else:
        st.caption("기록된 책이 없습니다.")

st.divider()

# --- 검색/추가 섹션 ---
st.markdown("<span class='section-title'>🔍 새 책 추가</span>", unsafe_allow_html=True)
query = st.text_input("알라딘 검색", placeholder="제목/저자 입력", label_visibility="collapsed")
if query:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                g_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                sel_genre = st.text_input("장르", value=g_val, key=f"src_g_{i}", label_visibility="collapsed")
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_{i}"):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 하단 리스트 ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책 모음</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        print_Indices = []
        c1, c2 = st.columns([1, 2])
        if c1.button("🗑️ 전체 비우기"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = c2.toggle("삭제 모드")
        
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄", key=f"p_{idx}", value=True): print_Indices.append(idx)
                st.caption(f"{itm.get('genre', '미지정')}")
                
                try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: val = [date.today(), date.today()]
                new_dr = st.date_input("날짜", val, key=f"e_d_{idx}", label_visibility="collapsed")
                
                b1, b2 = st.columns([2, 1])
                if b1.button("수정", key=f"sv_{idx}"):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and b2.button("❌", key=f"dc_{idx}"):
                    st.session_state.pop(idx); save_all(); st.rerun()

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(item.get('genre', '미지정'))
                c1, c2 = st.columns(2)
                if c1.button("✅ 읽음", key=f"wr_{i}"):
                    st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if c2.button("🗑️ 삭제", key=f"wd_{i}"):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()