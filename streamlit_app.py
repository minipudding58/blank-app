import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (수정 금지) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (사용자 요청 디자인 완벽 박제) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [핵심] 탭 디자인: '책 검색'과 동일한 18px 볼드체 + 여유롭고 긴 하늘색 선 */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 50px !important;   /* 선 길이를 길게 뽑기 위한 여백 */
        padding-right: 50px !important;  /* 선 길이를 길게 뽑기 위한 여백 */
        margin-right: 20px !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important; /* 하늘색 선 */
        height: 3px !important;
    }}

    /* 타이틀 스타일 */
    .section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 12px; 
        display: block; 
        color: #31333F;
    }}

    /* 상단 누적 박스 */
    .total-box {{
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #eee;
    }}
    .total-text {{ font-size: 32px; font-weight: bold; color: #87CEEB; }}

    /* 장르 카드 */
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }}

    /* 책 이미지 및 텍스트 스타일 */
    [data-testid="stImage"] img {{
        height: 200px !important;
        object-fit: contain !important;
        background-color: #f9f9f9;
        border-radius: 5px;
    }}
    .date-text {{ font-size: 14px; color: #666; margin-top: 5px; margin-bottom: 5px; display: block; }}

    /* 편집 모드 빨간색 텍스트 유지 */
    .stCheckbox label {{ color: #ff6b6b !important; font-weight: bold !important; }}
    div.stButton > button p {{ color: #ff6b6b !important; font-weight: bold !important; }}
    
    /* 입력창 테두리 제거 및 깔끔한 스타일 */
    div[data-baseweb="input"] {{ border: 1px solid #eee !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 세션 및 데이터 로드 ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임을 입력하세요", placeholder="예: 치이카와")
    if st.button("서재 입장") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
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

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 4. 메인 대시보드 ---
st.title(f"📖 {st.session_state.user_id}의 서재")
st.markdown(f'<div class="total-box"><span class="total-text">✨ {len(st.session_state.collection)}권 읽음 ✨</span></div>', unsafe_allow_html=True)

if st.session_state.collection:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
    g_cols = st.columns(6)
    for i, (genre, count) in enumerate(counts.items()):
        g_cols[i % 6].markdown(f"<div class='genre-card'>{genre}<br><b>{count}권</b></div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 5. 책 검색 섹션 ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색창", placeholder="제목/저자 입력...", label_visibility="collapsed")
if q:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
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
                    sel_genre = st.text_input("장르 설정", value=g_val, key=f"sg_{i}", label_visibility="collapsed")
                    b_cols = st.columns(2)
                    if b_cols[0].button("📖 읽음", key=f"r_{i}", use_container_width=True):
                        img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                        save_all(); st.rerun()
                    if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 6. 내 서재 & 위시리스트 (탭 디자인 적용) ---
tab_library, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_library:
    st.write("")
    if st.session_state.collection:
        edit_mode = st.toggle("편집 모드", key="main_edit_toggle")
        p_idx = []
        dcols = st.columns(4)
        
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                
                # [수정] 편집 모드 ON일 때: 표지 선택, 장르 수정, 날짜 수정, 수정 버튼 노출
                if edit_mode:
                    if st.checkbox(f"표지 선택", key=f"p_sel_{idx}", value=True):
                        p_idx.append(idx)
                    
                    new_genre = st.text_input("장르 수정", value=itm.get('genre', '미지정'), key=f"genre_edit_{idx}", label_visibility="collapsed")
                    
                    try: 
                        date_val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                    except: 
                        date_val = [date.today(), date.today()]
                    
                    new_date = st.date_input("날짜 수정", date_val, key=f"date_edit_{idx}", label_visibility="collapsed")
                    
                    btn_cols = st.columns([2, 1])
                    if btn_cols[0].button("수정", key=f"save_btn_{idx}", use_container_width=True):
                        if len(new_date) == 2:
                            st.session_state.collection[idx].update({
                                "genre": new_genre,
                                "start": new_date[0].isoformat(),
                                "end": new_date[1].isoformat()
                            })
                            save_all(); st.rerun()
                    if btn_cols[1].button("❌", key=f"del_btn_{idx}", use_container_width=True):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
                
                # [수정] 편집 모드 OFF일 때: 장르와 날짜 텍스트만 노출 (날짜 항상 표시)
                else:
                    st.caption(f"장르: {itm.get('genre', '미지정')}")
                    date_str = f"{itm.get('start','').replace('-','/')} - {itm.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{date_str}</span>', unsafe_allow_html=True)

        # PDF 저장 버튼 (하단 노출)
        if edit_mode and p_idx:
            st.write("---")
            if st.button(f"📥 선택한 {len(p_idx)}권 PDF로 저장하기", key="pdf_gen_btn", use_container_width=True):
                sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                curr_x, curr_y = 150, 150
                for i in p_idx:
                    img = st.session_state.collection[i]["img"]
                    ratio = TARGET_H_PX / float(img.size[1])
                    resized = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                    if curr_x + resized.size[0] > A4_W_PX - 150:
                        curr_x = 150; curr_y += TARGET_H_PX + 60
                    sheet.paste(resized, (curr_x, curr_y))
                    curr_x += resized.size[0] + 60
                
                pdf_buf = io.BytesIO()
                sheet.save(pdf_buf, format="PDF", resolution=300.0)
                st.download_button("📥 PDF 다운로드 시작", pdf_buf.getvalue(), "my_reading_list.pdf", use_container_width=True)

with tab_wish:
    st.write("")
    if st.session_state.wishlist:
        wcols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 4]:
                try:
                    r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    wb_cols = st.columns(2)
                    if wb_cols[0].button("📖 읽음", key=f"wish_r_{i}", use_container_width=True):
                        st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if wb_cols[1].button("🗑️", key=f"wish_d_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                except: continue
    else:
        st.info("위시리스트가 비어 있습니다.")