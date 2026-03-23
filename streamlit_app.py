import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (고해상도 PDF 및 레이아웃) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 통합 (모든 디자인 디테일 박제) ---
st.markdown(f"""
    <style>
    /* 전체 배경 및 여백 */
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* [상단] 메인 타이틀 */
    .main-title {{ font-size: 32px; font-weight: bold; color: #31333F; margin-bottom: 30px; }}

    /* [상단] 대시보드 레이아웃 */
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 80px;
        margin-bottom: 25px;
        padding: 10px 0;
    }}
    
    /* [폰트] 누적 독서 & 장르 현황 스타일 통일 (18px Bold) */
    .header-label {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #31333F !important;
        margin-bottom: 15px;
        display: block;
    }}
    
    .total-summary-box {{ text-align: center; min-width: 160px; }}
    .total-count-display {{
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
        display: block;
        margin: 5px 0;
    }}
    
    /* [장르 현황] 카드 디자인 */
    .genre-card-item {{ 
        background-color: #fcfcfc; 
        border: 1px solid #f0f0f0; 
        border-radius: 12px; 
        padding: 12px 22px; 
        text-align: center; 
        min-width: 100px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }}
    
    /* [탭] 18px 볼드 + 긴 하늘색 밑줄 (사용자 요청 반영) */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 3px !important;
    }}

    /* [목록] 이미지 높이 고정 (210px) 및 이미지 비율 유지 */
    [data-testid="stImage"] img {{ 
        height: 210px !important; 
        object-fit: contain !important; 
        border-radius: 8px;
        border: 1px solid #eee;
    }}
    .date-text {{ font-size: 14px; color: #888; display: block; margin-top: 8px; }}

    /* [편집 모드] 빨간색 강조 (삭제/선택 관련) */
    .edit-label-red label {{ color: #ff6b6b !important; font-weight: bold !important; }}
    .edit-btn-red button p {{ color: #ff6b6b !important; font-weight: bold !important; }}
    
    /* [입력창] 지저분한 테두리 및 그림자 완전 제거 */
    input, div[data-baseweb="input"], .stTextInput div {{ 
        border: none !important; 
        box-shadow: none !important; 
        background-color: #f9f9f9 !important;
        border-radius: 5px !important;
    }}
    
    /* 버튼 높이 보정 */
    div.stButton > button {{
        height: 40px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 데이터 및 세션 관리 (예외 처리 강화) ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장 로그인</div>", unsafe_allow_html=True)
    u_in = st.text_input("닉네임을 입력해주세요", placeholder="예: 치이카와", label_visibility="collapsed")
    if st.button("입장하기") and u_in:
        st.session_state.user_id = u_in
        st.query_params["user"] = u_in
        st.rerun()
    st.stop()

USER_FILE = f"data_{st.session_state.user_id}.json"

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
                                "url": itm["url"], 
                                "start": itm.get("start", date.today().isoformat()),
                                "end": itm.get("end", date.today().isoformat()), 
                                "genre": itm.get("genre", "미지정")
                            })
                    except Exception as e:
                        continue # 이미지 로드 실패 시 건너뜀
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

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
        st.error(f"데이터 저장 실패: {e}")

# --- 📊 4. 상단 대시보드 (치이카와의 독서기록) ---
st.markdown(f"<div class='main-title'>📖 {st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

st.markdown('<div class="top-header-wrapper">', unsafe_allow_html=True)
h_col1, h_col2 = st.columns([1, 4])

with h_col1:
    # 2026 누적 독서 (폰트 스타일 통일 및 이모지 제거 반영)
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
        st.caption("아직 기록된 도서 장르가 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# --- 🔍 5. 책 검색 (백업 코드의 강력한 정규표현식 로직 적용) ---
st.markdown("<span class='header-label'>🔍 책 검색</span>", unsafe_allow_html=True)
search_q = st.text_input("검색창", placeholder="제목 또는 저자를 입력하세요...", label_visibility="collapsed")

if search_q:
    with st.spinner("알라딘에서 도서 정보를 가져오고 있습니다..."):
        try:
            res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={search_q}", headers={"User-Agent": "Mozilla/5.0"}).text
            # 모든 이미지 경로(product, pimg 등)와 cover 키워드를 포함한 주소를 유연하게 추출
            imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res)))
            genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
            
            if imgs:
                s_cols = st.columns(4)
                for i, url in enumerate(imgs[:4]):
                    with s_cols[i]:
                        st.image(url, use_container_width=True)
                        g_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                        sel_genre = st.text_input("장르 설정", value=g_val, key=f"sq_{i}", label_visibility="collapsed")
                        b_cols = st.columns(2)
                        if b_cols[0].button("📖 읽음", key=f"rb_{i}", use_container_width=True):
                            raw_img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(raw_img)).convert("RGB"), 
                                "url": url, 
                                "start": date.today().isoformat(), 
                                "end": date.today().isoformat(), 
                                "genre": sel_genre
                            })
                            save_data(); st.rerun()
                        if b_cols[1].button("🩵 위시", key=f"wb_{i}", use_container_width=True):
                            st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                            save_data(); st.rerun()
            else:
                st.warning("검색 결과가 없습니다. 다른 검색어를 입력해보세요.")
        except Exception as e:
            st.error(f"검색 중 오류 발생: {e}")

st.divider()

# --- 📚 6. 메인 목록 관리 (내 서재 / 위시리스트) ---
t_lib, t_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with t_lib:
    if st.session_state.collection:
        is_edit = st.toggle("서재 편집 및 PDF 모드 활성화")
        sel_idx = []
        l_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with l_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                if is_edit:
                    st.markdown('<div class="edit-label-red">', unsafe_allow_html=True)
                    if st.checkbox("인쇄 포함", key=f"pc_{i}", value=True): sel_idx.append(i)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    e_genre = st.text_input("장르 수정", value=item.get('genre', '미지정'), key=f"eg_{i}", label_visibility="collapsed")
                    
                    # 날짜 유효성 검사 및 로드
                    try:
                        d_val = [date.fromisoformat(item["start"]), date.fromisoformat(item["end"])]
                    except:
                        d_val = [date.today(), date.today()]
                    
                    e_date = st.date_input("날짜 수정", d_val, key=f"ed_{i}", label_visibility="collapsed")
                    
                    eb_c = st.columns([2, 1])
                    with eb_c[0]:
                        st.markdown('<div class="edit-btn-red">', unsafe_allow_html=True)
                        if st.button("저장", key=f"es_{i}", use_container_width=True):
                            if isinstance(e_date, list) and len(e_date) == 2:
                                st.session_state.collection[i].update({
                                    "genre": e_genre, 
                                    "start": e_date[0].isoformat(), 
                                    "end": e_date[1].isoformat()
                                })
                                save_data(); st.rerun()
                            elif isinstance(e_date, date):
                                st.warning("종료 날짜까지 선택해주세요.")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if eb_c[1].button("❌", key=f"edl_{i}", help="삭제하기", use_container_width=True):
                        st.session_state.collection.pop(i)
                        save_data(); st.rerun()
                else:
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    d_str = f"{item.get('start','').replace('-','/')} - {item.get('end','').replace('-','/')}"
                    st.markdown(f'<span class="date-text">{d_str}</span>', unsafe_allow_html=True)

        # PDF 저장 기능 (선택된 도서 대상)
        if is_edit and sel_idx:
            st.divider()
            if st.button(f"📥 선택한 {len(sel_idx)}권 PDF 책장 생성", use_container_width=True):
                with st.spinner("PDF 파일을 생성하고 있습니다..."):
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
                    
                    b_io = io.BytesIO()
                    canv.save(b_io, format="PDF", resolution=300.0)
                    st.download_button("📥 생성된 PDF 다운로드", b_io.getvalue(), f"{st.session_state.user_id}_reading_list.pdf", use_container_width=True)
    else:
        st.info("아직 서재에 책이 없습니다. 상단 검색창에서 책을 추가해보세요!")

with t_wish:
    if st.session_state.wishlist:
        w_cols = st.columns(4)
        for i, w in enumerate(st.session_state.wishlist):
            with w_cols[i % 4]:
                try:
                    w_raw = requests.get(w['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    st.image(Image.open(io.BytesIO(w_raw)), use_container_width=True)
                    st.caption(f"장르: {w.get('genre', '미지정')}")
                    
                    if st.button("📖 읽기 완료", key=f"wr_{i}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(w_raw)).convert("RGB"), 
                            "url": w['url'], 
                            "start": date.today().isoformat(), 
                            "end": date.today().isoformat(), 
                            "genre": w.get('genre', '미지정')
                        })
                        st.session_state.wishlist.pop(i)
                        save_data(); st.rerun()
                    
                    if st.button("🗑️ 위시 삭제", key=f"wd_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i)
                        save_data(); st.rerun()
                except:
                    st.error("이미지를 불러올 수 없습니다.")
    else:
        st.info("위시리스트가 비어있습니다.")