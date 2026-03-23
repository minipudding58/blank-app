import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (A4 출력 및 해상도 절대 고정) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 통합 (UI 레이아웃 및 텍스트 배경 제거) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 3rem !important; padding-bottom: 2rem !important; }}
    
    .main-title {{ 
        font-size: 36px; 
        font-weight: bold; 
        color: #31333F; 
        margin-bottom: 10px !important;
        display: block;
    }}

    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 80px;
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

    /* 텍스트 배경 하이라이트 제거 */
    .stMarkdown div, .stMarkdown p, .stMarkdown span, div[data-testid="stCheckbox"] label div {{
        background-color: transparent !important;
        background: none !important;
    }}
    
    .stButton button {{
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

# --- 🗝️ 3. 데이터 및 세션 관리 (AttributeError 방지 로직) ---
# 최신 Streamlit의 query_params 대응
q_params = st.query_params
if "user" in q_params:
    st.session_state.user_id = q_params["user"]

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장 로그인</div>", unsafe_allow_html=True)
    u_in = st.text_input("닉네임을 입력해주세요", placeholder="예: 먼작귀", label_visibility="collapsed")
    if st.button("입장하기") and u_in:
        st.session_state.user_id = u_in
        st.query_params["user"] = u_in
        st.rerun()
    st.stop()

USER_FILE = f"data_{st.session_state.user_id}.json"

# 세션 변수 초기화
if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    # 검색 결과 유지용 캐시
    if 'search_results_cache' not in st.session_state:
        st.session_state.search_results_cache = []
    if 'last_search_query' not in st.session_state:
        st.session_state.last_search_query = ""

    # 데이터 로드
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
        st.error(f"저장 오류: {e}")

# --- 📊 4. 대시보드 ---
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
        st.caption("등록된 데이터가 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 검색창 및 결과 유지 로직 ---
st.markdown("<span class='header-label'>🔍 책 검색</span>", unsafe_allow_html=True)
search_q = st.text_input("검색어 입력", placeholder="제목 또는 저자를 입력하세요...", label_visibility="collapsed")

# 검색 실행 및 캐싱
if search_q and search_q != st.session_state.last_search_query:
    try:
        res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_q}", headers={"User-Agent": "Mozilla/5.0"}).text
        found_imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res)))
        found_genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
        
        st.session_state.search_results_cache = []
        for i in range(min(4, len(found_imgs))):
            st.session_state.search_results_cache.append({
                "url": found_imgs[i],
                "genre": found_genres[i] if i < len(found_genres) else "미지정"
            })
        st.session_state.last_search_query = search_q
    except:
        st.error("알라딘 검색 결과 호출 실패")

# 캐시된 결과 표시
if st.session_state.search_results_cache:
    s_cols = st.columns(4)
    for i, item in enumerate(st.session_state.search_results_cache):
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

# --- 📚 6. 메인 목록 (내 서재 및 위시리스트) ---
t_lib, t_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with t_lib:
    if st.session_state.collection:
        is_edit = st.toggle("편집 및 PDF 모드 활성화", key="main_edit_toggle")
        sel_idx = []
        
        l_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with l_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                if is_edit:
                    if st.checkbox("표지 선택", key=f"pc_{i}", value=True):
                        sel_idx.append(i)
                    
                    e_genre = st.text_input("장르", value=item.get('genre', '미지정'), key=f"eg_{i}", label_visibility="collapsed")
                    
                    try: d_val = (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
                    except: d_val = (date.today(), date.today())
                    
                    e_date = st.date_input("날짜", d_val, key=f"ed_{i}", label_visibility="collapsed")
                    
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        st.markdown('<div class="edit-btn-blue">', unsafe_allow_html=True)
                        if st.button("수정", key=f"es_{i}", use_container_width=True):
                            s_str = e_date[0].isoformat() if isinstance(e_date, (list, tuple)) else e_date.isoformat()
                            en_str = e_date[1].isoformat() if isinstance(e_date, (list, tuple)) and len(e_date) > 1 else s_str
                            st.session_state.collection[i].update({"genre": e_genre, "start": s_str, "end": en_str})
                            save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with btn_cols[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("❌ 삭제", key=f"edl_{i}", use_container_width=True):
                            st.session_state.collection.pop(i); save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.caption(f"장르: {item.get('genre')}")
                    d_display = f"{item.get('start','').replace('-','/')} - {item.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{d_display}</span>', unsafe_allow_html=True)

        if is_edit and sel_idx:
            st.divider()
            if st.button(f"📥 선택한 {len(sel_idx)}권 PDF 책장 만들기", use_container_width=True):
                with st.spinner("PDF 파일 생성 중..."):
                    canv = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    cur_x, cur_y = 150, 150
                    for idx in sel_idx:
                        orig = st.session_state.collection[idx]["img"]
                        scale = TARGET_H_PX / float(orig.size[1])
                        new_w = int(orig.size[0] * scale)
                        r_img = orig.resize((new_w, TARGET_H_PX), Image.LANCZOS)
                        
                        if cur_x + new_w > A4_W_PX - 150:
                            cur_x = 150
                            cur_y += TARGET_H_PX + 60
                        
                        canv.paste(r_img, (cur_x, cur_y))
                        cur_x += new_w + 60
                    
                    pdf_buf = io.BytesIO()
                    canv.save(pdf_buf, format="PDF", resolution=300.0)
                    st.download_button("📥 PDF 다운로드", pdf_buf.getvalue(), "my_book_shelf.pdf", use_container_width=True)
    else:
        st.info("서재가 비어있습니다. 책을 검색해 추가해보세요.")

with t_wish:
    if st.session_state.wishlist:
        w_cols = st.columns(4)
        for i, w in enumerate(st.session_state.wishlist):
            with w_cols[i % 4]:
                try:
                    w_res = requests.get(w['url'], timeout=5, headers={"User-Agent": "Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(w_res))
                    st.image(w_img, use_container_width=True)
                    if st.button("📖 읽음 완료", key=f"wr_{i}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": w_img.convert("RGB"), "url": w['url'], 
                            "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": w.get('genre')
                        })
                        st.session_state.wishlist.pop(i); save_data(); st.rerun()
                    if st.button("🗑️ 삭제", key=f"wd_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_data(); st.rerun()
                except: continue
    else:
        st.info("위시리스트가 비어있습니다.")