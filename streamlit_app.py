import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (PDF 및 이미지 처리용) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (상단 가로 정렬 + 탭 디자인 디테일) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [상단] 누적 독서량 가로 레이아웃 (image_301fa1.png 완벽 재현) */
    .top-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
    }}
    .total-box {{
        text-align: center;
        padding-right: 50px;
    }}
    .total-text {{
        font-size: 45px;
        font-weight: bold;
        color: #87CEEB;
    }}
    .total-label {{ font-size: 18px; color: #666; }}
    
    /* [탭] 18px 볼드체 + 여유롭고 긴 하늘색 선 (image_3b082e.png 기준) */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 70px !important;   /* 선 길이를 확보하기 위한 여백 */
        padding-right: 70px !important;  /* 선 길이를 확보하기 위한 여백 */
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 3px !important;
    }}

    /* 섹션 타이틀 스타일 */
    .section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 15px; 
        display: block;
    }}

    /* 장르 카드 스타일 (image_30723e.png) */
    .genre-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }}
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 10px 20px;
        text-align: center;
        min-width: 100px;
    }}

    /* 이미지 및 날짜 텍스트 */
    [data-testid="stImage"] img {{ height: 210px !important; object-fit: contain !important; border-radius: 5px; }}
    .date-text {{ font-size: 14px; color: #888; display: block; margin-top: 8px; }}

    /* 편집 모드 빨간색 포인트 (image_3b010c.jpg) */
    .stCheckbox label, div.stButton > button p {{ 
        color: #ff6b6b !important; 
        font-weight: bold !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 데이터 로드 및 세션 관리 ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.title("📖 나만의 독서 기록장")
    u_input = st.text_input("닉네임을 입력하세요", placeholder="예: 치이카와")
    if st.button("서재 입장") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
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

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 📊 4. 상단 레이아웃 (가로형 유지) ---
st.title(f"📖 {st.session_state.user_id}의 서재")

t_col1, t_col2 = st.columns([1, 2.5])
with t_col1:
    st.markdown(f"""
        <div class="total-box">
            <span class="total-label">누적</span><br>
            <span class="total-text">✨ {len(st.session_state.collection)}권 읽음 ✨</span><br>
            <span style="font-size: 30px;">✨✨</span>
        </div>
        """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        g_html = "".join([f"<div class='genre-card'>{g}<br><b>{c}권</b></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-status-container' style='display:flex; gap:10px; flex-wrap:wrap;'>{g_html}</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 5. 책 검색 ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="제목/저자 입력...", label_visibility="collapsed")
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
                    sel_genre = st.text_input("장르", value=g_val, key=f"s_g_{i}", label_visibility="collapsed")
                    b_cols = st.columns(2)
                    if b_cols[0].button("📖 읽음", key=f"r_b_{i}", use_container_width=True):
                        img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                        save_all(); st.rerun()
                    if b_cols[1].button("🩵 위시", key=f"w_b_{i}", use_container_width=True):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 6. 내 서재 & 위시리스트 (탭 디테일 반영) ---
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
    st.write("")
    if st.session_state.collection:
        edit_mode = st.toggle("편집 모드 활성화", key="edit_mode_toggle")
        p_idx = []
        lcols = st.columns(4)
        for idx, itm in enumerate(st.session_state.collection):
            with lcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                if edit_mode:
                    if st.checkbox("인쇄 선택 (빨간색 줄)", key=f"p_c_{idx}", value=True): p_idx.append(idx)
                    new_g = st.text_input("장르 수정", value=itm.get('genre', '미지정'), key=f"g_m_{idx}", label_visibility="collapsed")
                    try: d_val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                    except: d_val = [date.today(), date.today()]
                    new_d = st.date_input("날짜 수정", d_val, key=f"d_m_{idx}", label_visibility="collapsed")
                    btn_c = st.columns([2, 1])
                    if btn_c[0].button("저장 (빨간색 줄)", key=f"sv_m_{idx}", use_container_width=True):
                        if len(new_d) == 2:
                            st.session_state.collection[idx].update({"genre": new_g, "start": new_d[0].isoformat(), "end": new_d[1].isoformat()})
                            save_all(); st.rerun()
                    if btn_c[1].button("❌ 삭제", key=f"dl_m_{idx}", use_container_width=True):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
                else:
                    st.caption(f"장르: {itm.get('genre', '미지정')}")
                    d_str = f"{itm.get('start','').replace('-','/')} - {itm.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{d_str}</span>', unsafe_allow_html=True)
        
        if edit_mode and p_idx:
            st.write("---")
            if st.button(f"📥 선택한 {len(p_idx)}권 PDF로 내려받기", use_container_width=True):
                sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                cx, cy = 150, 150
                for i in p_idx:
                    img = st.session_state.collection[i]["img"]
                    ratio = TARGET_H_PX / float(img.size[1])
                    res = img.resize((int(img.size[0]*ratio), TARGET_H_PX), Image.LANCZOS)
                    if cx + res.size[0] > A4_W_PX - 150: cx = 150; cy += TARGET_H_PX + 60
                    sheet.paste(res, (cx, cy)); cx += res.size[0] + 60
                pdf_b = io.BytesIO(); sheet.save(pdf_b, format="PDF", resolution=300.0)
                st.download_button("확인 후 다운로드", pdf_b.getvalue(), f"{st.session_state.user_id}_서재.pdf", use_container_width=True)

with tab_wish:
    st.write("")
    if st.session_state.wishlist:
        wcols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 4]:
                r = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                st.image(Image.open(io.BytesIO(r)), use_container_width=True)
                st.caption(f"장르: {item.get('genre', '미지정')}")
                if st.button("📖 다 읽음!", key=f"w_r_{i}", use_container_width=True):
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(r)).convert("RGB"), "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()