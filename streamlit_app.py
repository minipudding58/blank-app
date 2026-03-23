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

# --- 🎨 2. 스타일 (상단 가로형 고정 + 탭 디자인 디테일 복구) ---
st.markdown(f"""
    <style>
    /* 전체 여백 조정 */
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [상단] 누적 독서량 가로 레이아웃 완벽 재현 */
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 80px;
        padding: 20px 0;
    }}
    .total-summary-box {{
        text-align: center;
        min-width: 150px;
    }}
    .total-count-text {{
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
        display: block;
        margin: 5px 0;
    }}
    .total-label-text {{ font-size: 16px; color: #666; font-weight: bold; }}
    
    /* [탭] 18px 볼드체 + 여유롭고 긴 하늘색 밑줄 (image_3b082e.png 기준) */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 80px !important;   /* 선 길이를 확보하기 위한 여백 */
        padding-right: 80px !important;  /* 선 길이를 확보하기 위한 여백 */
        margin-right: 20px !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 3px !important;
    }}

    /* 공통 섹션 타이틀 */
    .sub-section-title {{ font-size: 18px !important; font-weight: bold !important; margin-bottom: 12px; display: block; }}
    
    /* 장르 카드 (image_f7b2fb.png) */
    .genre-card {{ background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 5px 12px; text-align: center; }}
    
    /* 책 이미지 높이 고정 (image_2fa7c7.png 유지) */
    [data-testid="stImage"] img {{ height: 200px !important; object-fit: contain !important; border-radius: 5px; }}
    .date-display {{ font-size: 14px; color: #888; display: block; margin-top: 8px; }}

    /* 편집 모드 붉은색 강조 (image_3b69a7.jpg 반영) */
    .edit-mode-container label {{ color: #ff6b6b !important; font-weight: bold !important; }}
    div.stButton > button p {{ font-weight: bold !important; }}
    .save-btn-red p {{ color: #ff6b6b !important; }}
    
    /* 입력창 빨간 테두리 강제 제거 (image_3107cd.png) */
    div[data-baseweb="input"] {{ border: none !important; box-shadow: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 로그인 및 세션 관리 ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("나만의 닉네임을 입력하세요", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 🔗 4. 데이터 로드 및 저장 함수 ---
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
                                    "url": u, "start": itm.get("start", date.today().isoformat()),
                                    "end": itm.get("end", date.today().isoformat()), "genre": itm.get("genre", "미지정")
                                })
                        except: continue
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 5. 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.user_id}** 님의 서재")
    st.write("---")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    st.write("")
    if st.button("🗑️ 내 데이터 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# --- 📊 6. 상단 대시보드 (수정 요청 완벽 반영) ---
# 치이카와의 서재 -> 치이카와의 독서기록으로 변경
st.title(f"📖 {st.session_state.user_id}의 독서기록")
st.write(""); st.write("")

# [요청] 누적 부분 디자인 완벽 원상복구 (image_f7b2fb.png 가로형 고정)
st.markdown('<div class="top-header-wrapper">', unsafe_allow_html=True)
t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    # [요청] 누적 부분 -> 2026 누적 독서 ✨3권✨으로 변경
    curr_year = datetime.now().year
    st.markdown(f"""
        <div class="total-summary-box">
            <span class="total-label-text">{curr_year} 누적 독서</span><br>
            <span class="total-count-text">✨{len(st.session_state.collection)}권✨</span>
            <div style="font-size: 28px; margin-top:10px;">✨<br>✨✨</div>
        </div>
        """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='sub-section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items = "".join([f"<div class='genre-card'>{g}<br><b>{c}권</b></div>" for g, c in counts.items()])
        st.markdown(f"<div style='display:flex; gap:12px; flex-wrap:wrap;'>{genre_items}</div>", unsafe_allow_html=True)
    else: st.caption("기록이 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 🔍 7. 책 검색 섹션 ---
st.markdown("<span class='sub-section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색창", placeholder="제목/저자 입력...", label_visibility="collapsed")
if q:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
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
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                        save_all(); st.rerun()
                    if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()
    else: st.warning("검색 결과가 없습니다.")

st.divider()

# --- 📚 8. 목록 관리 및 수정 (탭 디테일 복구) ---
tab_library, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_library:
    st.write("")
    if st.session_state.collection:
        edit_mode = st.toggle("편집 모드 활성화", key="library_edit_toggle")
        p_idx = []
        
        dcols = st.columns(4)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                
                # 편집 모드 ON일 때 (image_3b69a7.jpg 반영)
                if edit_mode:
                    st.markdown('<div class="edit-mode-container">', unsafe_allow_html=True)
                    if st.checkbox("인쇄 선택 (빨간색 줄)", key=f"p_{idx}", value=True): p_idx.append(idx)
                    new_g = st.text_input("장르 수정", value=itm.get('genre', '미지정'), key=f"g_e_{idx}", label_visibility="collapsed")
                    try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                    except: val = [date.today(), date.today()]
                    new_d = st.date_input("날짜 수정", val, key=f"d_e_{idx}", label_visibility="collapsed")
                    b_edit_cols = st.columns([2, 1])
                    with b_edit_cols[0]:
                        st.markdown('<div class="save-btn-red">', unsafe_allow_html=True)
                        if st.button("저장 (빨간색 줄)", key=f"sv_{idx}", use_container_width=True):
                            if len(new_d) == 2:
                                st.session_state.collection[idx].update({"genre": new_g, "start": new_d[0].isoformat(), "end": new_d[1].isoformat()})
                                save_all(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    if b_edit_cols[1].button("❌ 삭제", key=f"dc_{idx}", use_container_width=True):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 편집 모드 OFF일 때 (기본 모드)
                else:
                    st.caption(f"장르: {itm.get('genre', '미지정')}")
                    date_display = f"{itm.get('start', '').replace('-', '/')} - {itm.get('end', '').replace('-', '/')}"
                    st.markdown(f'<span class="date-display">{date_display}</span>', unsafe_allow_html=True)

        if edit_mode and p_idx:
            st.divider()
            if st.button(f"📥 선택한 {len(p_idx)}권 PDF로 저장하기", key="lib_pdf_btn", use_container_width=True):
                sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                cx, cy = 150, 150
                for i in p_idx:
                    img = st.session_state.collection[i]["img"]
                    ratio = TARGET_H_PX / float(img.size[1])
                    res = img.resize((int(img.size[0]*ratio), TARGET_H_PX), Image.LANCZOS)
                    if cx + res.size[0] > A4_W_PX - 150: cx = 150; cy += TARGET_H_PX + 60
                    sheet.paste(res, (cx, cy)); cx += res.size[0] + 60
                buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
                st.download_button("📥 PDF 다운로드", buf.getvalue(), f"{st.session_state.user_id}_서재.pdf", use_container_width=True)
    else: st.info("서재가 비어 있습니다.")

with tab_wish:
    st.write("")
    if st.session_state.wishlist:
        wcols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 4]:
                r = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                st.image(Image.open(io.BytesIO(r)), use_container_width=True)
                st.caption(f"장르: {item.get('genre', '미지정')}")
                if st.button("📖 읽음 완료", key=f"w_r_{i}", use_container_width=True):
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(r)).convert("RGB"), "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if st.button("🗑️ 삭제", key=f"w_d_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()