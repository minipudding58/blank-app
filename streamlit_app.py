import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (PDF 및 고해상도 처리) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (사용자 요청 디테일 박제) ---
st.markdown(f"""
    <style>
    /* 전체 여백 조정 */
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [상단 타이틀] */
    .main-title {{ font-size: 32px; font-weight: bold; color: #31333F; margin-bottom: 30px; }}

    /* [상단 레이아웃] 가로 정렬 고정 */
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 80px;
        margin-bottom: 20px;
    }}
    
    /* [누적 독서] 폰트를 '장르별 독서 현황'과 동일하게 설정 */
    .header-label {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #31333F !important;
        margin-bottom: 15px;
        display: block;
    }}
    .total-summary-box {{ text-align: center; min-width: 150px; }}
    .total-count-display {{
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
        display: block;
        margin: 5px 0;
    }}
    
    /* [장르 현황] 카드 스타일 */
    .genre-card-item {{ 
        background-color: #fcfcfc; 
        border: 1px solid #f0f0f0; 
        border-radius: 10px; 
        padding: 10px 20px; 
        text-align: center; 
        min-width: 100px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    
    /* [탭] 18px 볼드 + 긴 하늘색 밑줄 (image_3b082e.png) */
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
    }}
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 3px !important;
    }}

    /* [책 리스트] 이미지 및 날짜 */
    [data-testid="stImage"] img {{ height: 210px !important; object-fit: contain !important; border-radius: 5px; }}
    .date-text {{ font-size: 14px; color: #888; display: block; margin-top: 8px; }}

    /* [편집 모드] 빨간색 강조 (image_3b69a7.jpg) */
    .edit-label-red label {{ color: #ff6b6b !important; font-weight: bold !important; }}
    .edit-btn-red button p {{ color: #ff6b6b !important; font-weight: bold !important; }}
    
    /* [입력창] 빨간 테두리 완전 제거 (image_3107cd.png) */
    input, div[data-baseweb="input"], .stTextInput div {{ border: none !important; box-shadow: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 데이터 및 세션 관리 ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장 로그인</div>", unsafe_allow_html=True)
    u_in = st.text_input("닉네임", placeholder="예: 치이카와", label_visibility="collapsed")
    if st.button("입장") and u_in:
        st.session_state.user_id = u_in
        st.query_params["user"] = u_in
        st.rerun()
    st.stop()

USER_FILE = f"data_{st.session_state.user_id}.json"

# 데이터 로드 로직 (이미지 캐싱 포함)
if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
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
                                "url": itm["url"], "start": itm.get("start", date.today().isoformat()),
                                "end": itm.get("end", date.today().isoformat()), "genre": itm.get("genre", "미지정")
                            })
                    except: continue
        except: pass

def save_data():
    out = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=4)

# --- 📊 4. 상단 대시보드 (수정 사항 반영 버전) ---
# [요청] 치이카와의 독서기록
st.markdown(f"<div class='main-title'>📖 {st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

st.markdown('<div class="top-header-wrapper">', unsafe_allow_html=True)
h_col1, h_col2 = st.columns([1, 4])

with h_col1:
    # [요청] 2026 누적 독서 (폰트 일치) + 하단 이모지 제거
    curr_year = datetime.now().year
    st.markdown(f"""
        <div class="total-summary-box">
            <span class="header-label">{curr_year} 누적 독서</span>
            <span class="total-count-display">✨{len(st.session_state.collection)}권✨</span>
        </div>
        """, unsafe_allow_html=True)

with h_col2:
    st.markdown("<span class='header-label'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        g_html = "".join([f"<div class='genre-card-item'>{g}<br><b>{c}권</b></div>" for g, c in counts.items()])
        st.markdown(f"<div style='display:flex; gap:12px; flex-wrap:wrap;'>{g_html}</div>", unsafe_allow_html=True)
    else:
        st.caption("아직 읽은 책이 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 책 검색 (검색 로직 완전 복구) ---
st.markdown("<span class='header-label'>🔍 책 검색</span>", unsafe_allow_html=True)
search_q = st.text_input("검색창", placeholder="제목 또는 저자를 입력하세요...", label_visibility="collapsed")

if search_q:
    with st.spinner("알라딘에서 책을 찾는 중..."):
        s_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_q}"
        resp = requests.get(s_url, headers={"User-Agent": "Mozilla/5.0"}).text
        
        # 알라딘 검색 리스트 블록 추출
        blocks = re.findall(r'<table[^>]*class="ss_book_list"[^>]*>.*?</table>', resp, re.DOTALL)
        
        if blocks:
            s_cols = st.columns(4)
            for idx, block in enumerate(blocks[:4]):
                with s_cols[idx]:
                    img_m = re.search(r'https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', block)
                    if img_m:
                        cover = img_m.group(0)
                        st.image(cover, use_container_width=True)
                        
                        # 장르 추출 로직
                        genre_m = re.search(r'class="ss_f_g_l"[^>]*>([^<]+)</a>', block)
                        def_genre = genre_m.group(1) if genre_m else "미지정"
                        
                        in_genre = st.text_input("장르", value=def_genre, key=f"sq_{idx}", label_visibility="collapsed")
                        btn_c1, btn_c2 = st.columns(2)
                        
                        if btn_c1.button("📖 읽음", key=f"rb_{idx}", use_container_width=True):
                            raw = requests.get(cover, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(raw)).convert("RGB"), 
                                "url": cover, "start": date.today().isoformat(), 
                                "end": date.today().isoformat(), "genre": in_genre
                            })
                            save_data(); st.rerun()
                            
                        if btn_c2.button("🩵 위시", key=f"wb_{idx}", use_container_width=True):
                            st.session_state.wishlist.append({"url": cover, "genre": in_genre})
                            save_data(); st.rerun()
        else:
            st.warning("검색 결과가 없습니다. 다시 시도해주세요!")

st.divider()

# --- 📚 6. 목록 관리 (탭 및 리스트) ---
t_lib, t_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with t_lib:
    st.write("")
    if st.session_state.collection:
        is_edit = st.toggle("편집 모드 활성화")
        sel_idx = []
        l_cols = st.columns(4)
        
        for i, item in enumerate(st.session_state.collection):
            with l_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                
                if is_edit:
                    st.markdown('<div class="edit-label-red">', unsafe_allow_html=True)
                    if st.checkbox("인쇄 선택", key=f"pc_{i}", value=True): sel_idx.append(i)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    e_genre = st.text_input("장르 수정", value=item.get('genre', '미지정'), key=f"eg_{i}", label_visibility="collapsed")
                    
                    try: d_val = [date.fromisoformat(item["start"]), date.fromisoformat(item["end"])]
                    except: d_val = [date.today(), date.today()]
                    
                    e_date = st.date_input("날짜 수정", d_val, key=f"ed_{i}", label_visibility="collapsed")
                    
                    eb_cols = st.columns([2, 1])
                    with eb_cols[0]:
                        st.markdown('<div class="edit-btn-red">', unsafe_allow_html=True)
                        if st.button("저장", key=f"es_{i}", use_container_width=True):
                            if len(e_date) == 2:
                                st.session_state.collection[i].update({
                                    "genre": e_genre, "start": e_date[0].isoformat(), "end": e_date[1].isoformat()
                                })
                                save_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if eb_cols[1].button("❌", key=f"edl_{i}", use_container_width=True):
                        st.session_state.collection.pop(i); save_data(); st.rerun()
                else:
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    d_str = f"{item.get('start','').replace('-','/')} - {item.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{d_str}</span>', unsafe_allow_html=True)

        # PDF 생성 섹션
        if is_edit and sel_idx:
            st.divider()
            if st.button(f"📥 선택한 {len(sel_idx)}권 PDF 저장", use_container_width=True):
                canv = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                curr_x, curr_y = 150, 150
                for idx in sel_idx:
                    im = st.session_state.collection[idx]["img"]
                    rat = TARGET_H_PX / float(im.size[1])
                    r_im = im.resize((int(im.size[0]*rat), TARGET_H_PX), Image.LANCZOS)
                    
                    if curr_x + r_im.size[0] > A4_W_PX - 150:
                        curr_x = 150
                        curr_y += TARGET_H_PX + 60
                    
                    canv.paste(r_im, (curr_x, curr_y))
                    curr_x += r_im.size[0] + 60
                
                pdf_b = io.BytesIO()
                canv.save(pdf_b, format="PDF", resolution=300.0)
                st.download_button("📥 PDF 다운로드", pdf_b.getvalue(), f"{st.session_state.user_id}_reading_list.pdf", use_container_width=True)
    else:
        st.info("서재가 비어있습니다. 책을 추가해보세요!")

with t_wish:
    st.write("")
    if st.session_state.wishlist:
        w_cols = st.columns(4)
        for i, w in enumerate(st.session_state.wishlist):
            with w_cols[i % 4]:
                w_raw = requests.get(w['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                st.image(Image.open(io.BytesIO(w_raw)), use_container_width=True)
                st.caption(f"장르: {w.get('genre', '미지정')}")
                
                if st.button("📖 읽음 완료", key=f"wr_{i}", use_container_width=True):
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(w_raw)).convert("RGB"), 
                        "url": w['url'], "start": date.today().isoformat(), 
                        "end": date.today().isoformat(), "genre": w.get('genre', '미지정')
                    })
                    st.session_state.wishlist.pop(i); save_data(); st.rerun()
                
                if st.button("🗑️ 삭제", key=f"wd_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_data(); st.rerun()