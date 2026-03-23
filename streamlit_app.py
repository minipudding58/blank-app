import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (A4 인쇄 규격) ---
DPI = 300
TARGET_H_PX_PRINT = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (누적 독서량 원상복구 + 테두리 제거) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* 입력창 클릭 시 빨간 테두리 제거 */
    div[data-baseweb="input"] {{ border: 1px solid #ccc !important; box-shadow: none !important; }}
    div[data-baseweb="input"]:focus-within {{ border: 1px solid #87CEEB !important; box-shadow: 0 0 0 0.2rem rgba(135, 206, 235, 0.25) !important; }}

    /* 누적 독서량 박스 디자인 원상복구 */
    .total-box {{
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }}
    .total-text {{
        font-size: 32px;
        font-weight: bold;
        color: #87CEEB;
    }}

    .genre-card {{ background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 5px 12px; text-align: center; }}
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin-bottom: 12px; display: block; color: #31333F; }}
    
    /* 책 이미지 높이 고정 */
    [data-testid="stImage"] img {{ height: 200px !important; object-fit: contain !important; background-color: #f9f9f9; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 로그인 상태 유지 (쿼리 파라미터 활용) ---
query_user = st.query_params.get("user")
if query_user:
    st.session_state.user_id = query_user
elif 'user_id' not in st.session_state:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("나만의 닉네임을 입력하세요", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 🔗 4. 데이터 로드 ---
if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    u = itm.get("url")
                    if u:
                        try:
                            r = requests.get(u, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                            if r.status_code == 200:
                                st.session_state.collection.append({
                                    "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                                    "url": u,
                                    "start": itm.get("start", date.today().isoformat()),
                                    "end": itm.get("end", date.today().isoformat()),
                                    "genre": itm.get("genre", "미지정")
                                })
                        except: continue
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 5. 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.user_id}** 님의 서재")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    if st.button("🔥 내 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# --- 📊 6. 상단 대시보드 (디자인 원상복구) ---
st.title(f"📖 {st.session_state.user_id}의 서재")

# 원상복구된 누적 독서량 박스
st.markdown(f"""
    <div class="total-box">
        <span class="total-text">✨ {len(st.session_state.collection)}권 읽음 ✨</span>
    </div>
    """, unsafe_allow_html=True)

# 장르 현황
if st.session_state.collection:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
    cols = st.columns(len(counts) if len(counts) > 0 else 1)
    for i, (genre, count) in enumerate(counts.items()):
        cols[i % len(cols)].markdown(f"<div class='genre-card'>{genre}<br><b>{count}권</b></div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 7. 책 검색 (결과 출력 복구 및 장르 연동) ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="제목/저자 입력...", label_visibility="collapsed")
if q:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    
    # 책 단위로 데이터 파싱
    items = re.findall(r'<table[^>]*class="ss_book_list"[^>]*>.*?</table>', res, re.DOTALL)
    
    if items:
        scols = st.columns(4)
        for i, block in enumerate(items[:4]):
            with scols[i]:
                img_match = re.search(r'https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', block)
                if img_match:
                    url = img_match.group(0)
                    genre_match = re.search(r'class="ss_f_g_l"[^>]*>([^<]+)</a>', block)
                    g_val = genre_match.group(1) if genre_match else "미지정"
                    
                    st.image(url, use_container_width=True)
                    sel_genre = st.text_input("장르", value=g_val, key=f"sg_{i}", label_visibility="collapsed")
                    
                    b_cols = st.columns(2)
                    if b_cols[0].button("📖 읽음", key=f"r_{i}", use_container_width=True):
                        img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                            "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                        })
                        save_all(); st.rerun()
                    if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                        save_all(); st.rerun()
    else:
        st.warning("검색 결과가 없습니다.")

st.divider()

# --- 📚 8. 독서 목록 및 PDF 저장 ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        p_idx = []; del_m = st.toggle("삭제 모드")
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄", key=f"p_{idx}", value=True): p_idx.append(idx)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: val = [date.today(), date.today()]
                new_dr = st.date_input("날짜", val, key=f"ed_{idx}", label_visibility="collapsed")
                
                b_edit_cols = st.columns([2, 1])
                if b_edit_cols[0].button("수정", key=f"sv_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and b_edit_cols[1].button("❌", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
        
        if p_idx:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255)); x, y = 100, 100
            for i in p_idx:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX_PRINT / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX_PRINT), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX_PRINT + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 {len(p_idx)}권 PDF 저장", buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                url = item.get('url')
                r_img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(item.get('genre', '미지정'))
                wb_cols = st.columns(2)
                if wb_cols[0].button("✅읽음", key=f"wr_{i}", use_container_width=True):
                    st.session_state.collection.append({"img": img_obj, "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if wb_cols[1].button("🗑️", key=f"w_d_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()