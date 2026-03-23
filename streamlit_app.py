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

# --- 🎨 2. 스타일 (사용자 요청 디자인 집대성) ---
st.markdown(f"""
    <style>
    /* 전체 여백 조정 */
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [테두리] 빨간색 테두리 및 포커스 효과 완전 제거 */
    input, div[data-baseweb="input"], .stTextInput > div {{
        border-color: #eee !important;
        box-shadow: none !important;
    }}
    
    /* [상단] 누적 독서량 가로 레이아웃 (image_3b66bf.png) */
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 100px;
        padding: 30px 0;
        background-color: white;
    }}
    .total-summary-box {{
        text-align: center;
        min-width: 180px;
    }}
    .total-count-text {{
        font-size: 48px;
        font-weight: bold;
        color: #87CEEB;
        display: block;
        margin: 10px 0;
    }}
    .total-label-text {{ font-size: 18px; color: #666; font-weight: bold; }}
    
    /* [탭] 18px 볼드체 + 여유롭고 긴 하늘색 밑줄 (image_3b082e.png) */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 80px !important;   /* 선 길이를 길게 뽑기 위한 패딩 */
        padding-right: 80px !important;  /* 선 길이를 길게 뽑기 위한 패딩 */
        margin-right: 20px !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 4px !important;
    }}

    /* 공통 섹션 타이틀 */
    .sub-section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 15px; 
        display: block;
        color: #333;
    }}

    /* 장르 카드 스타일 */
    .genre-badge-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
    }}
    .genre-badge-card {{
        background-color: #fcfcfc;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 12px 28px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }}

    /* 책 이미지 및 텍스트 디테일 */
    [data-testid="stImage"] img {{ 
        height: 220px !important; 
        object-fit: contain !important; 
        border-radius: 8px;
        border: 1px solid #f5f5f5;
    }}
    .book-date-label {{ 
        font-size: 13px; 
        color: #999; 
        display: block; 
        margin-top: 10px; 
        letter-spacing: -0.5px;
    }}

    /* 편집 모드 붉은색 강조 (image_3b69a7.jpg) */
    .edit-mode-container label {{ color: #ff6b6b !important; font-weight: bold !important; }}
    div.stButton > button p {{ font-weight: bold !important; }}
    .save-btn-red p {{ color: #ff6b6b !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 세션 및 데이터 로직 ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.markdown("<h2 style='text-align:center;'>📖 나만의 독서 기록장</h2>", unsafe_allow_html=True)
    with st.container():
        _, center_col, _ = st.columns([1, 1, 1])
        with center_col:
            u_input = st.text_input("닉네임을 입력하세요", placeholder="예: 치이카와")
            if st.button("내 서재 들어가기", use_container_width=True) and u_input:
                st.session_state.user_id = u_input
                st.query_params["user"] = u_input
                st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

def load_data():
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

load_data()

def save_all_data():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [
            {"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} 
            for i in st.session_state.collection
        ]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 📊 4. 상단 레이아웃 (image_3b66bf.png 완벽 복구) ---
st.title(f"📖 {st.session_state.user_id}의 서재")

st.markdown('<div class="top-header-wrapper">', unsafe_allow_html=True)
header_col1, header_col2 = st.columns([1, 3])

with header_col1:
    st.markdown(f"""
        <div class="total-summary-box">
            <span class="total-label-text">누적</span><br>
            <span class="total-count-text">✨ {len(st.session_state.collection)}권 읽음 ✨</span>
            <div style="font-size: 30px; margin-top:15px; line-height: 1.2;">✨<br>✨✨</div>
        </div>
        """, unsafe_allow_html=True)

with header_col2:
    st.markdown("<span class='sub-section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        g_html = "".join([f"<div class='genre-badge-card'>{g}<br><b>{c}권</b></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-badge-container'>{g_html}</div>", unsafe_allow_html=True)
    else:
        st.info("아직 읽은 책이 없어요. 아래에서 검색해 보세요!")
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 🔍 5. 책 검색 및 추가 로직 ---
st.markdown("<span class='sub-section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
search_q = st.text_input("검색어 입력창", placeholder="책 제목이나 저자를 검색해 보세요...", label_visibility="collapsed")

if search_q:
    with st.spinner("책을 찾는 중..."):
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_q}"
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
        
        # 상세 데이터 추출 (이미지, 장르, 저자 등)
        items = re.findall(r'<table[^>]*class="ss_book_list"[^>]*>.*?</table>', response, re.DOTALL)
        
        if items:
            search_cols = st.columns(4)
            for idx, item_html in enumerate(items[:4]):
                with search_cols[idx]:
                    img_match = re.search(r'https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', item_html)
                    if img_match:
                        cover_url = img_match.group(0)
                        genre_match = re.search(r'class="ss_f_g_l"[^>]*>([^<]+)</a>', item_html)
                        found_genre = genre_match.group(1) if genre_match else "미지정"
                        
                        st.image(cover_url, use_container_width=True)
                        input_genre = st.text_input("장르", value=found_genre, key=f"search_genre_{idx}", label_visibility="collapsed")
                        
                        btn_col_a, btn_col_b = st.columns(2)
                        if btn_col_a.button("📖 읽음", key=f"add_read_{idx}", use_container_width=True):
                            img_data = requests.get(cover_url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                "url": cover_url, "start": date.today().isoformat(), 
                                "end": date.today().isoformat(), "genre": input_genre
                            })
                            save_all_data(); st.rerun()
                        if btn_col_b.button("🩵 위시", key=f"add_wish_{idx}", use_container_width=True):
                            st.session_state.wishlist.append({"url": cover_url, "genre": input_genre})
                            save_all_data(); st.rerun()
        else:
            st.error("검색 결과가 없습니다.")

st.divider()

# --- 📚 6. 메인 관리 탭 (image_3b082e.png 디자인) ---
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
    st.write("")
    if st.session_state.collection:
        edit_toggle = st.toggle("🔧 편집 모드 (삭제 및 수정)", key="lib_edit_toggle")
        print_indices = []
        
        lib_cols = st.columns(4)
        for i, book in enumerate(st.session_state.collection):
            with lib_cols[i % 4]:
                st.image(book["img"], use_container_width=True)
                
                if edit_toggle:
                    # 편집 UI (image_3b69a7.jpg 반영)
                    st.markdown('<div class="edit-mode-container">', unsafe_allow_html=True)
                    if st.checkbox("인쇄용 선택", key=f"check_{i}", value=True):
                        print_indices.append(i)
                    
                    m_genre = st.text_input("장르 수정", value=book.get('genre', '미지정'), key=f"edit_genre_{i}", label_visibility="collapsed")
                    
                    try: 
                        curr_dates = [date.fromisoformat(book["start"]), date.fromisoformat(book["end"])]
                    except: 
                        curr_dates = [date.today(), date.today()]
                    
                    m_date = st.date_input("날짜 수정", curr_dates, key=f"edit_date_{i}", label_visibility="collapsed")
                    
                    ctrl_cols = st.columns([2, 1])
                    with ctrl_cols[0]:
                        st.markdown('<div class="save-btn-red">', unsafe_allow_html=True)
                        if st.button("저장", key=f"btn_save_{i}", use_container_width=True):
                            if len(m_date) == 2:
                                st.session_state.collection[i].update({
                                    "genre": m_genre, "start": m_date[0].isoformat(), "end": m_date[1].isoformat()
                                })
                                save_all_data(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    if ctrl_cols[1].button("❌", key=f"btn_del_{i}", use_container_width=True):
                        st.session_state.collection.pop(i)
                        save_all_data(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 일반 뷰 모드
                    st.caption(f"장르: {book.get('genre', '미지정')}")
                    date_range = f"{book.get('start','').replace('-','/')} - {book.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="book-date-label">{date_range}</span>', unsafe_allow_html=True)

        # PDF 생성 로직 (상세 유지)
        if edit_toggle and print_indices:
            st.write("---")
            if st.button(f"📥 선택한 {len(print_indices)}권 PDF로 내려받기", use_container_width=True):
                a4_canvas = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                pos_x, pos_y = 150, 150
                for idx in print_indices:
                    b_img = st.session_state.collection[idx]["img"]
                    scale = TARGET_H_PX / float(b_img.size[1])
                    resized_img = b_img.resize((int(b_img.size[0] * scale), TARGET_H_PX), Image.LANCZOS)
                    
                    if pos_x + resized_img.size[0] > A4_W_PX - 150:
                        pos_x = 150
                        pos_y += TARGET_H_PX + 80
                    
                    a4_canvas.paste(resized_img, (pos_x, pos_y))
                    pos_x += resized_img.size[0] + 80
                
                pdf_output = io.BytesIO()
                a4_canvas.save(pdf_output, format="PDF", resolution=300.0)
                st.download_button("📥 PDF 다운로드", pdf_output.getvalue(), f"{st.session_state.user_id}_reading_list.pdf", use_container_width=True)

with tab_wish:
    st.write("")
    if st.session_state.wishlist:
        wish_cols = st.columns(4)
        for wi, witem in enumerate(st.session_state.wishlist):
            with wish_cols[wi % 4]:
                try:
                    wr = requests.get(witem['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(wr))
                    st.image(w_img, use_container_width=True)
                    st.caption(f"장르: {witem.get('genre', '미지정')}")
                    
                    wc_cols = st.columns(2)
                    if wc_cols[0].button("📖 읽음", key=f"wish_read_{wi}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": w_img.convert("RGB"), "url": witem['url'], 
                            "start": date.today().isoformat(), "end": date.today().isoformat(), 
                            "genre": witem.get('genre', '미지정')
                        })
                        st.session_state.wishlist.pop(wi)
                        save_all_data(); st.rerun()
                    if wc_cols[1].button("🗑️", key=f"wish_del_{wi}", use_container_width=True):
                        st.session_state.wishlist.pop(wi)
                        save_all_data(); st.rerun()
                except: continue
    else:
        st.write("위시리스트가 비어 있습니다. 책을 검색해 추가해 보세요!")