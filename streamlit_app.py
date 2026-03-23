import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 시스템 및 상수 설정 (고해상도 인쇄 기준) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)  # 인쇄용 높이 40mm
A4_W_PX = int((210 / 25.4) * DPI)     # A4 너비
A4_H_PX = int((297 / 25.4) * DPI)     # A4 높이

# 페이지 설정
st.set_page_config(
    page_title="나의 독서 기록장",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🎨 2. CSS 스타일 시트 (329줄의 핵심: 디테일한 디자인 코드) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');

    /* 전체 폰트 및 배경 */
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Noto Sans KR', sans-serif;
        background-color: #ffffff;
    }}

    .block-container {{ 
        padding-top: 3rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 1200px;
    }}
    
    /* 타이틀 영역 */
    .main-title {{ 
        font-size: 38px; 
        font-weight: 700; 
        color: #1E1E1E; 
        margin-bottom: 45px; 
        letter-spacing: -1px;
        display: flex;
        align-items: center;
        gap: 15px;
    }}

    /* 상단 대시보드 박스 레이아웃 */
    .top-dashboard-container {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 90px;
        background-color: #fcfcfc;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        margin-bottom: 40px;
    }}
    
    /* 공통 라벨 스타일 (18px Bold) */
    .section-label {{ 
        font-size: 18px !important; 
        font-weight: 700 !important; 
        color: #444 !important;
        margin-bottom: 15px;
        display: block;
    }}
    
    /* 누적 숫자 강조 */
    .counter-box {{ text-align: center; }}
    .counter-number {{
        font-size: 52px;
        font-weight: 800;
        color: #87CEEB;
        line-height: 1;
        margin-top: 10px;
    }}
    
    /* 장르 카드 아이템 */
    .genre-tag {{ 
        background-color: #ffffff; 
        border: 1.5px solid #eee; 
        border-radius: 12px; 
        padding: 10px 20px; 
        text-align: center; 
        min-width: 90px;
        transition: all 0.2s ease;
    }}
    .genre-tag:hover {{ border-color: #87CEEB; transform: translateY(-2px); }}
    .genre-name {{ font-size: 13px; color: #888; }}
    .genre-count {{ font-size: 18px; font-weight: 700; color: #333; }}
    
    /* 탭 스타일 최적화 (하늘색 긴 밑줄) */
    .stTabs [data-baseweb="tab"] {{
        height: 60px !important;
        padding-left: 50px !important;
        padding-right: 50px !important;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"] p {{
        font-size: 19px !important;
        font-weight: 700 !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 4px !important;
    }}

    /* 도서 카드 이미지 (210px 고정) */
    [data-testid="stImage"] {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    [data-testid="stImage"] img {{ 
        height: 210px !important; 
        object-fit: cover !important; 
    }}
    
    /* 날짜 텍스트 */
    .date-display {{ 
        font-size: 14px; 
        color: #999; 
        margin-top: 10px;
        font-family: monospace;
    }}

    /* 편집 모드 - 빨간색 포인트 스타일 */
    .red-edit-text label {{ color: #FF4B4B !important; font-weight: 700 !important; }}
    div[data-testid="stCheckbox"] label p {{ color: #FF4B4B !important; font-weight: 600; }}
    
    /* 버튼 스타일 커스텀 */
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        border-color: #87CEEB !important;
        color: #87CEEB !important;
    }}

    /* 입력 필드 테두리 제거 및 배경색 */
    .stTextInput input, .stDateInput input {{
        border: none !important;
        background-color: #f5f5f5 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 세션 상태 및 데이터 로드 (상세 예외 처리 포함) ---
if "user" in st.query_params:
    st.session_state.user_id = st.query_params["user"]

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장</div>", unsafe_allow_html=True)
    with st.container():
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            u_input = st.text_input("닉네임을 입력하세요", placeholder="치이카와", key="login_input")
            if st.button("내 서재 들어가기", use_container_width=True) and u_input:
                st.session_state.user_id = u_input
                st.query_params["user"] = u_input
                st.rerun()
    st.stop()

USER_DATA_PATH = f"data_{st.session_state.user_id}.json"

def init_data():
    if 'collection' not in st.session_state:
        st.session_state.collection = []
        st.session_state.wishlist = []
        if os.path.exists(USER_DATA_PATH):
            try:
                with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                    st.session_state.wishlist = stored.get("wishlist", [])
                    raw_col = stored.get("collection", [])
                    for item in raw_col:
                        try:
                            resp = requests.get(item["url"], timeout=7, headers={"User-Agent": "Mozilla/5.0"})
                            if resp.status_code == 200:
                                img_obj = Image.open(io.BytesIO(resp.content)).convert("RGB")
                                st.session_state.collection.append({
                                    "img": img_obj,
                                    "url": item["url"],
                                    "start": item.get("start", date.today().isoformat()),
                                    "end": item.get("end", date.today().isoformat()),
                                    "genre": item.get("genre", "미지정")
                                })
                        except Exception as e:
                            print(f"이미지 로드 스킵: {e}")
                            continue
            except Exception as e:
                st.error(f"데이터 로드 오류: {e}")

init_data()

def save_all():
    try:
        payload = {
            "wishlist": st.session_state.wishlist,
            "collection": [
                {
                    "url": x["url"], 
                    "start": x["start"], 
                    "end": x["end"], 
                    "genre": x.get("genre", "미지정")
                } for x in st.session_state.collection
            ]
        }
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"저장 실패: {e}")

# --- 📊 4. 메인 헤더 & 대시보드 ---
st.markdown(f"<div class='main-title'>📖 {st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="top-dashboard-container">', unsafe_allow_html=True)
    d_col1, d_col2 = st.columns([1.5, 5])
    
    with d_col1:
        st.markdown(f"""
            <div class="counter-box">
                <span class="section-label">{datetime.now().year} 누적 독서</span>
                <span class="counter-number">{len(st.session_state.collection)}권</span>
            </div>
            """, unsafe_allow_html=True)
            
    with d_col2:
        st.markdown("<span class='section-label'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
        if st.session_state.collection:
            genre_map = Counter([b.get("genre", "미지정") for b in st.session_state.collection])
            tags_html = "".join([
                f"<div class='genre-tag'><div class='genre-name'>{g}</div><div class='genre-count'>{c}권</div></div>"
                for g, c in genre_map.items()
            ])
            st.markdown(f"<div style='display:flex; gap:15px; flex-wrap:wrap;'>{tags_html}</div>", unsafe_allow_html=True)
        else:
            st.info("아직 읽은 책이 없어요. 아래에서 검색해 보세요!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🔍 5. 검색 엔진 (강력한 정규표현식 로직) ---
st.markdown("<span class='section-label'>🔍 새로운 책 추가하기</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="책 제목이나 저자를 입력하고 엔터를 누르세요...", label_visibility="collapsed")

if q:
    with st.spinner("알라딘 서고를 뒤지는 중..."):
        try:
            search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
            html = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
            
            # 이미지와 장르를 더 정확하게 매칭하기 위한 정규식
            found_imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', html)))
            found_genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', html)
            
            if found_imgs:
                res_cols = st.columns(4)
                for i, img_url in enumerate(found_imgs[:8]): # 최대 8개 표시
                    with res_cols[i % 4]:
                        st.image(img_url, use_container_width=True)
                        cur_g = found_genres[i] if i < len(found_genres) else "미지정"
                        in_g = st.text_input(f"장르_{i}", value=cur_g, key=f"in_g_{i}", label_visibility="collapsed")
                        
                        btn_c = st.columns(2)
                        if btn_c[0].button("📖 읽음", key=f"add_read_{i}", use_container_width=True):
                            r_img = requests.get(img_url).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(r_img)).convert("RGB"),
                                "url": img_url,
                                "start": date.today().isoformat(),
                                "end": date.today().isoformat(),
                                "genre": in_g
                            })
                            save_all(); st.rerun()
                            
                        if btn_c[1].button("🩵 위시", key=f"add_wish_{i}", use_container_width=True):
                            st.session_state.wishlist.append({"url": img_url, "genre": in_g})
                            save_all(); st.rerun()
            else:
                st.warning(f"'{q}'에 대한 검색 결과가 없습니다. 다시 시도해 주세요!")
        except Exception as e:
            st.error(f"검색 엔진 오류: {e}")

st.divider()

# --- 📚 6. 내 서재 & 위시리스트 (편집 모드 포함) ---
tab_main, tab_wish = st.tabs(["📚 내 서재 관리", "🩵 장바구니 위시"])

with tab_main:
    if st.session_state.collection:
        is_edit = st.toggle("🛠️ 편집 모드 (수정/삭제/PDF)")
        print_targets = []
        
        lib_cols = st.columns(4)
        for idx, book in enumerate(st.session_state.collection):
            with lib_cols[idx % 4]:
                st.image(book["img"], use_container_width=True)
                
                if is_edit:
                    st.markdown('<div class="red-edit-text">', unsafe_allow_html=True)
                    if st.checkbox("인쇄 선택", key=f"sel_{idx}", value=True):
                        print_targets.append(idx)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    new_g = st.text_input("장르", value=book.get('genre'), key=f"edit_g_{idx}")
                    
                    try:
                        d_range = [date.fromisoformat(book["start"]), date.fromisoformat(book["end"])]
                    except:
                        d_range = [date.today(), date.today()]
                    
                    new_d = st.date_input("기간", d_range, key=f"edit_d_{idx}")
                    
                    ctrl_c = st.columns([3, 1])
                    with ctrl_c[0]:
                        if st.button("💾 저장", key=f"save_b_{idx}", use_container_width=True):
                            if isinstance(new_d, list) and len(new_d) == 2:
                                st.session_state.collection[idx].update({
                                    "genre": new_g, "start": new_d[0].isoformat(), "end": new_d[1].isoformat()
                                })
                                save_all(); st.rerun()
                    with ctrl_c[1]:
                        if st.button("🗑️", key=f"del_b_{idx}", use_container_width=True):
                            st.session_state.collection.pop(idx)
                            save_all(); st.rerun()
                else:
                    st.caption(f"분류: {book.get('genre')}")
                    period = f"{book['start'].replace('-','.')} ~ {book['end'].replace('-','.')}"
                    st.markdown(f'<div class="date-display">{period}</div>', unsafe_allow_html=True)

        # PDF 생성 섹션
        if is_edit and print_targets:
            st.divider()
            if st.button(f"📥 선택한 {len(print_targets)}권 PDF 책장으로 내보내기", use_container_width=True):
                with st.spinner("인쇄용 파일을 생성하고 있습니다..."):
                    pdf_canvas = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    px, py = 180, 180 # 여백
                    
                    for p_idx in print_targets:
                        target_img = st.session_state.collection[p_idx]["img"]
                        # 높이 기준 리사이징
                        scale = TARGET_H_PX / float(target_img.size[1])
                        new_w = int(target_img.size[0] * scale)
                        resized = target_img.resize((new_w, TARGET_H_PX), Image.LANCZOS)
                        
                        # 줄바꿈 체크
                        if px + new_w > A4_W_PX - 180:
                            px = 180
                            py += TARGET_H_PX + 80
                        
                        pdf_canvas.paste(resized, (px, py))
                        px += new_w + 80
                    
                    pdf_buf = io.BytesIO()
                    pdf_canvas.save(pdf_buf, format="PDF", resolution=300.0)
                    st.download_button(
                        label="📥 PDF 파일 저장하기",
                        data=pdf_buf.getvalue(),
                        file_name=f"{st.session_state.user_id}_book_collection.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
    else:
        st.info("서재가 아직 비어있어요. 멋진 책들로 채워보세요!")

with tab_wish:
    if st.session_state.wishlist:
        wi_cols = st.columns(4)
        for w_idx, wish_item in enumerate(st.session_state.wishlist):
            with wi_cols[w_idx % 4]:
                try:
                    w_resp = requests.get(wish_item['url'], timeout=5).content
                    w_img = Image.open(io.BytesIO(w_resp))
                    st.image(w_img, use_container_width=True)
                    st.caption(f"예정 장르: {wish_item.get('genre')}")
                    
                    if st.button("✅ 다 읽음!", key=f"finish_w_{w_idx}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": w_img.convert("RGB"),
                            "url": wish_item['url'],
                            "start": date.today().isoformat(),
                            "end": date.today().isoformat(),
                            "genre": wish_item.get('genre')
                        })
                        st.session_state.wishlist.pop(w_idx)
                        save_all(); st.rerun()
                        
                    if st.button("❌ 삭제", key=f"del_w_{w_idx}", use_container_width=True):
                        st.session_state.wishlist.pop(w_idx)
                        save_all(); st.rerun()
                except:
                    st.error("이미지를 불러오지 못했습니다.")
    else:
        st.info("읽고 싶은 책들을 위시리스트에 담아보세요!")

# --- 🛠️ 7. 하단 정보 ---
st.markdown("---")
st.caption(f"© 2026 {st.session_state.user_id}의 개인 독서 기록장 | 모든 데이터는 로컬 브라우저 세션에 안전하게 보관됩니다.")