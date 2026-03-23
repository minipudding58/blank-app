import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (절대 고정) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 통합 (UI 가독성 및 정밀 레이아웃 수정) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 3rem !important; padding-bottom: 2rem !important; }}
    
    .main-title {{ 
        font-size: 36px; 
        font-weight: bold; 
        color: #31333F; 
        margin-bottom: 10px !important;
        line-height: 1.2;
        display: block;
    }}

    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 80px;
        margin-top: 0px !important;
        margin-bottom: 25px;
        padding: 10px 0 !important;
    }}
    
    .header-label {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #31333F !important;
        margin-bottom: 8px;
        display: block;
    }}
    
    .total-summary-box {{ text-align: center; min-width: 160px; }}
    .total-count-display {{
        font-size: 48px;
        font-weight: bold;
        color: #87CEEB;
        display: block;
        margin-top: 5px;
    }}
    
    .genre-card-item {{ 
        background-color: #fcfcfc; 
        border: 1px solid #f0f0f0; 
        border-radius: 12px; 
        padding: 10px 20px; 
        text-align: center; 
        min-width: 90px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        padding-left: 50px !important;
        padding-right: 50px !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 4px !important;
    }}

    [data-testid="stImage"] img {{ 
        height: 210px !important; 
        object-fit: contain !important; 
        border-radius: 8px;
        border: 1px solid #eee;
    }}
    .date-text {{ font-size: 14px; color: #888; display: block; margin-top: 8px; }}

    /* 텍스트 하이라이트(배경색) 완전 제거 */
    .stMarkdown div, .stMarkdown p, .stMarkdown span {{
        background-color: transparent !important;
        background: none !important;
    }}
    
    /* --- [핵심 수정] 버튼 수평 정렬 및 높이 통일 --- */
    .stButton button {{
        width: 100% !important; /* 컬럼 너비에 꽉 차게 */
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 8px !important;
    }}

    .edit-btn-blue button p {{ color: #87CEEB !important; font-weight: bold !important; }}
    .del-btn-red button p {{ color: #ff6b6b !important; font-weight: bold !important; }}

    input, div[data-baseweb="input"], .stTextInput div {{ 
        border: none !important; 
        background-color: #f9f9f9 !important;
        border-radius: 6px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 데이터 및 세션 관리 ---
try:
    if "user" in st.query_params:
        st.session_state.user_id = st.query_params["user"]
except:
    pass

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장 로그인</div>", unsafe_allow_html=True)
    u_in = st.text_input("닉네임을 입력해주세요", placeholder="예: 먼작귀", label_visibility="collapsed")
    if st.button("입장하기") and u_in:
        st.session_state.user_id = u_in
        st.query_params["user"] = u_in
        st.rerun()
    st.stop()

USER_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    # 검색 결과 증발 방지용 캐시
    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {"query": "", "items": []}

    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    try:
                        r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code == 200:
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                                "url": itm["url"], 
                                "start": itm.get("start", date.today().isoformat()),
                                "end": itm.get("end", date.today().isoformat()), 
                                "genre": itm.get("genre", "미지정")
                            })
                    except: continue
        except: pass

def save_data():
    try:
        out = {
            "wishlist": st.session_state.wishlist, 
            "collection": [
                {"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} 
                for i in st.session_state.collection
            ]
        }
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"저장 중 오류: {e}")

# --- 📊 4. 상단 대시보드 ---
st.markdown(f"<div class='main-title'>📖 {st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

st.markdown('<div class="top-header-wrapper">', unsafe_allow_html=True)
h_col1, h_col2 = st.columns([1, 4])

with h_col1:
    st.markdown(f"""
        <div class="total-summary-box">
            <span class="header-label">{datetime.now().year} 누적 독서</span>
            <span class="total-count-display">{len(st.session_state.collection)}권</span>
        </div>
        """, unsafe_allow_html=True)

with h_col2:
    st.markdown("<span class='header-label'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        g_html = "".join([f"<div class='genre-card-item'>{g}<br><b>{c}권</b></div>" for g, c in counts.items()])
        st.markdown(f"<div style='display:flex; gap:12px; flex-wrap:wrap;'>{g_html}</div>", unsafe_allow_html=True)
    else:
        st.caption("아직 데이터가 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 책 검색 (검색 결과 유지 기능 포함) ---
st.markdown("<span class='header-label'>🔍 책 검색</span>", unsafe_allow_html=True)
search_input = st.text_input("검색어 입력", placeholder="제목 또는 저자를 입력하세요...", label_visibility="collapsed")

if search_input and search_input != st.session_state.search_cache["query"]:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_input}", headers={"User-Agent": "Mozilla/5.0"}).text
        imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res)))
        genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
        
        st.session_state.search_cache["items"] = []
        for i in range(min(4, len(imgs))):
            st.session_state.search_cache["items"].append({
                "url": imgs[i],
                "genre": genre_raw[i] if i < len(genre_raw) else "미지정"
            })
        st.session_state.search_cache["query"] = search_input
    except:
        st.error("검색 중 오류가 발생했습니다.")

if st.session_state.search_cache["items"]:
    s_cols = st.columns(4)
    for i, item in enumerate(st.session_state.search_cache["items"]):
        with s_cols[i]:
            st.image(item["url"], use_container_width=True)
            sel_genre = st.text_input("장르", value=item["genre"], key=f"sq_{i}", label_visibility="collapsed")
            b_cols = st.columns(2)
            if b_cols[0].button("📖 읽음", key=f"rb_{i}", use_container_width=True):
                r_img = requests.get(item["url"], headers={"User-Agent": "Mozilla/5.0"}).content
                st.session_state.collection.append({
                    "img": Image.open(io.BytesIO(r_img)).convert("RGB"), 
                    "url": item["url"], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                })
                save_data(); st.rerun()
            if b_cols[1].button("🩵 위시", key=f"wb_{i}", use_container_width=True):
                st.session_state.wishlist.append({"url": item["url"], "genre": sel_genre})
                save_data(); st.rerun()

st.divider()

# --- 📚 6. 메인 목록 및 위시리스트 (편집 및 PDF 기능 포함) ---
t_lib, t_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with t_lib:
    if st.session_state.collection:
        # 내 서재 탭의 토글 버튼
        is_edit = st.toggle("편집 및 PDF 모드 활성화", key="edit_toggle_lib")
        selected_books = []
        
        l_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with l_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                if is_edit:
                    if st.checkbox("표지 선택", key=f"pc_{i}", value=True):
                        selected_books.append(i)
                    
                    e_genre = st.text_input("장르", value=item.get('genre', '미지정'), key=f"eg_{i}", label_visibility="collapsed")
                    try: d_val = (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
                    except: d_val = (date.today(), date.today())
                    e_date = st.date_input("기간", d_val, key=f"ed_{i}", label_visibility="collapsed")
                    
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        st.markdown('<div class="edit-btn-blue">', unsafe_allow_html=True)
                        if st.button("수정", key=f"es_{i}", use_container_width=True):
                            s_date = e_date[0].isoformat() if isinstance(e_date, (list, tuple)) else e_date.isoformat()
                            en_date = e_date[1].isoformat() if isinstance(e_date, (list, tuple)) and len(e_date) > 1 else s_date
                            st.session_state.collection[i].update({"genre": e_genre, "start": s_date, "end": en_date})
                            save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with btn_cols[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("❌ 삭제", key=f"edl_{i}", use_container_width=True):
                            st.session_state.collection.pop(i); save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.caption(f"장르: {item.get('genre')}")
                    d_str = f"{item.get('start','').replace('-','/')} - {item.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{d_str}</span>', unsafe_allow_html=True)

        if is_edit and selected_books:
            st.divider()
            if st.button(f"📥 선택한 {len(selected_books)}권 PDF 책장 만들기", use_container_width=True):
                with st.spinner("PDF 생성 중..."):
                    canv = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    x, y = 150, 150
                    for idx in selected_books:
                        im = st.session_state.collection[idx]["img"]
                        rat = TARGET_H_PX / float(im.size[1])
                        r_im = im.resize((int(im.size[0]*rat), TARGET_H_PX), Image.LANCZOS)
                        if x + r_im.size[0] > A4_W_PX - 150: x = 150; y += TARGET_H_PX + 60
                        canv.paste(r_im, (x, y)); x += r_im.size[0] + 60
                    
                    b_io = io.BytesIO(); canv.save(b_io, format="PDF", resolution=300.0)
                    st.download_button("📥 PDF 다운로드", b_io.getvalue(), "my_books.pdf", use_container_width=True)
    else: st.info("서재가 비어있습니다.")

with t_wish:
    # --- 핵심 수정: 내 서재의 토글 버튼 공간만큼 공백 추가 ---
    # st.markdown(f'<div style="height: {토글버튼높이}px;"></div>', ...) 방식으로 구현
    # Streamlit 기본 toggle의 높이는 라벨 주석 포함 약 56px 정도입니다.
    st.markdown('<div style="height: 56px; margin-bottom: 0px;"></div>', unsafe_allow_html=True)
    
    if st.session_state.wishlist:
        w_cols = st.columns(4)
        for i, w in enumerate(st.session_state.wishlist):
            with w_cols[i % 4]:
                try:
                    w_r = requests.get(w['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(w_r))
                    st.image(w_img, use_container_width=True)
                    
                    # --- [핵심 수정] 버튼 수평 정렬 및 텍스트 변경 ---
                    wb_col1, wb_col2 = st.columns(2)
                    with wb_col1:
                        # 텍스트 수정: '읽기 완료!'
                        if st.button("📖 읽기 완료!", key=f"wr_{i}", use_container_width=True):
                            st.session_state.collection.append({
                                "img": w_img.convert("RGB"), "url": w['url'], 
                                "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": w.get('genre')
                            })
                            st.session_state.wishlist.pop(i); save_data(); st.rerun()
                    with wb_col2:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        # 텍스트 수정: '삭제하기' -> '삭제'
                        if st.button("🗑️ 삭제", key=f"wd_{i}", use_container_width=True):
                            st.session_state.wishlist.pop(i); save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                except: continue
    else: st.info("위시리스트가 비어있습니다.")