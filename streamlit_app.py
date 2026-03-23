import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# ==========================================
# ⚙️ 1. 전역 설정 및 상수 (A4 출력 최적화)
# ==========================================
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)  # 책 표지 높이 약 40mm 기준
A4_W_PX = int((210 / 25.4) * DPI)     # A4 너비 (픽셀)
A4_H_PX = int((297 / 25.4) * DPI)     # A4 높이 (픽셀)

st.set_page_config(
    page_title="나의 독서 기록장",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 2. 스타일 시트 (상단 디자인 복구 및 정렬)
# ==========================================
st.markdown(f"""
    <style>
    /* 전체 레이아웃 패딩 */
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 1200px;
    }}
    
    /* [핵심] 위시리스트 탭 상단 여백 고정 (내 서재 탭의 토글 버튼 위치와 대응) */
    .wish-top-spacer {{
        height: 74px !important; 
        display: block;
        width: 100%;
    }}

    /* 메인 타이틀 스타일 */
    .main-title {{ 
        font-size: 38px; 
        font-weight: 800; 
        color: #1E1E1E; 
        margin-bottom: 5px !important;
        letter-spacing: -1px;
    }}
    
    /* [상단 디자인 복구] 누적 독서량 & 장르 통계 가로 배치 */
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 80px;
        margin-bottom: 30px;
        padding: 20px 0;
    }}
    
    .header-label {{ 
        font-size: 16px !important; 
        font-weight: 600 !important; 
        color: #666 !important;
        margin-bottom: 10px;
        display: block;
    }}
    
    .total-count-display {{
        font-size: 52px;
        font-weight: 900;
        color: #87CEEB;
        line-height: 1;
    }}
    
    .genre-card-item {{ 
        background-color: #FFFFFF; 
        border: 1px solid #EAEAEA; 
        border-radius: 14px; 
        padding: 12px 18px; 
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        min-width: 85px;
    }}

    /* 탭 및 버튼 스타일 */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 19px !important;
        font-weight: 700 !important;
    }}

    /* 이미지 규격 및 버튼 수평 정렬 */
    [data-testid="stImage"] img {{ 
        height: 220px !important; 
        object-fit: contain !important; 
        border-radius: 10px;
        border: 1px solid #F0F0F0;
    }}
    
    .stButton button {{
        width: 100% !important;
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    
    /* 삭제 버튼 전용 스타일 */
    .del-btn-red button {{
        background-color: transparent !important;
        border: 1px solid #FF6B6B !important;
    }}
    .del-btn-red button p {{
        color: #FF6B6B !important;
    }}

    .date-text {{ 
        font-size: 13px; 
        color: #999; 
        display: block; 
        margin-top: 8px;
    }}
    
    /* 입력창 배경색 제거 */
    div[data-baseweb="input"] {{ 
        background-color: #F7F7F7 !important;
        border-radius: 10px !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🗝️ 3. 데이터 및 세션 관리 로직
# ==========================================
if 'user_id' not in st.session_state:
    try:
        params = st.query_params
        if "user" in params:
            st.session_state.user_id = params["user"]
        else:
            st.markdown("<div class='main-title'>📖 독서 기록장 입장</div>", unsafe_allow_html=True)
            u_input = st.text_input("닉네임을 입력하세요", placeholder="예: 먼작귀", label_visibility="collapsed")
            if st.button("입장하기") and u_input:
                st.session_state.user_id = u_input
                st.query_params["user"] = u_input
                st.rerun()
            st.stop()
    except: st.stop()

USER_DATA_PATH = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {"query": "", "items": []}

    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                st.session_state.wishlist = loaded.get("wishlist", [])
                for item in loaded.get("collection", []):
                    try:
                        resp = requests.get(item["url"], timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                        if resp.status_code == 200:
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(resp.content)).convert("RGB"), 
                                "url": item["url"], 
                                "start": item.get("start", date.today().isoformat()),
                                "end": item.get("end", date.today().isoformat()), 
                                "genre": item.get("genre", "미지정")
                            })
                    except: continue
        except: pass

def commit_changes():
    """데이터 영구 저장"""
    try:
        payload = {
            "wishlist": st.session_state.wishlist, 
            "collection": [
                {"url": i["url"], "start": i["start"], "end": i["end"], "genre": i["genre"]} 
                for i in st.session_state.collection
            ]
        }
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"저장 오류: {e}")

# ==========================================
# 📊 4. 상단 대시보드 (디자인 원상 복구)
# ==========================================
st.markdown(f"<div class='main-title'>{st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)

# 가로 배치 대시보드
h_col1, h_col2 = st.columns([1, 4])
with h_col1:
    st.markdown(f"<span class='header-label'>{datetime.now().year}년 누적 독서</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='total-count-display'>{len(st.session_state.collection)}<span style='font-size:24px; color:#333;'> 권</span></div>", unsafe_allow_html=True)

with h_col2:
    st.markdown("<span class='header-label'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        stats = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        stat_html = "".join([f"<div class='genre-card-item'>{g}<br><b>{c}권</b></div>" for g, c in stats.items()])
        st.markdown(f"<div style='display:flex; gap:14px; flex-wrap:wrap;'>{stat_html}</div>", unsafe_allow_html=True)
    else:
        st.caption("아직 데이터가 없습니다.")

st.divider()

# ==========================================
# 🔍 5. 도서 검색 및 추가 섹션
# ==========================================
st.markdown("<span class='header-label'>🔍 새로운 도서 검색</span>", unsafe_allow_html=True)
q_in = st.text_input("검색어", placeholder="제목 또는 저자를 입력하세요", label_visibility="collapsed")

if q_in and q_in != st.session_state.search_cache["query"]:
    try:
        res_text = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q_in}", headers={"User-Agent":"Mozilla/5.0"}).text
        found_imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res_text)))
        found_genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res_text)
        
        st.session_state.search_cache["items"] = []
        for i in range(min(4, len(found_imgs))):
            st.session_state.search_cache["items"].append({
                "url": found_imgs[i],
                "genre": found_genres[i] if i < len(found_genres) else "미지정"
            })
        st.session_state.search_cache["query"] = q_in
    except: st.error("검색 중 오류 발생")

if st.session_state.search_cache["items"]:
    s_cols = st.columns(4)
    for idx, item in enumerate(st.session_state.search_cache["items"]):
        with s_cols[idx]:
            st.image(item["url"], use_container_width=True)
            btn_grp = st.columns(2)
            if btn_grp[0].button("📖 읽음", key=f"s_add_lib_{idx}"):
                img_raw = requests.get(item["url"], headers={"User-Agent":"Mozilla/5.0"}).content
                st.session_state.collection.append({
                    "img": Image.open(io.BytesIO(img_raw)).convert("RGB"), 
                    "url": item["url"], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item["genre"]
                })
                commit_changes(); st.rerun()
            if btn_grp[1].button("🩵 위시", key=f"s_add_wish_{idx}"):
                st.session_state.wishlist.append({"url": item["url"], "genre": item["genre"]})
                commit_changes(); st.rerun()

st.divider()

# ==========================================
# 📚 6. 메인 콘텐츠 탭 (서재 / 위시리스트)
# ==========================================
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
    # 내 서재 상단 토글
    is_edit = st.toggle("편집 및 PDF 모드 활성화", key="edit_toggle_full")
    selected_for_pdf = []
    
    if st.session_state.collection:
        lib_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with lib_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                if is_edit:
                    if st.checkbox("선택", key=f"chk_{i}", value=True):
                        selected_for_pdf.append(i)
                    
                    # 정보 수정 로직
                    new_g = st.text_input("장르", value=item['genre'], key=f"eg_{i}", label_visibility="collapsed")
                    try:
                        d_range = (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
                    except:
                        d_range = (date.today(), date.today())
                    new_d = st.date_input("날짜", d_range, key=f"ed_{i}", label_visibility="collapsed")
                    
                    eb_cols = st.columns(2)
                    with eb_cols[0]:
                        if st.button("저장", key=f"esv_{i}"):
                            sd = new_d[0].isoformat() if isinstance(new_d, (list, tuple)) else new_d.isoformat()
                            ed = new_d[1].isoformat() if isinstance(new_d, (list, tuple)) and len(new_d) > 1 else sd
                            st.session_state.collection[i].update({"genre": new_g, "start": sd, "end": ed})
                            commit_changes(); st.rerun()
                    with eb_cols[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"edl_{i}"):
                            st.session_state.collection.pop(i); commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{item['genre']}**")
                    st.markdown(f'<span class="date-text">{item["start"]} ~ {item["end"]}</span>', unsafe_allow_html=True)

        # PDF 생성 기능 (상세 로직 유지)
        if is_edit and selected_for_pdf:
            st.divider()
            if st.button(f"📥 선택한 {len(selected_for_pdf)}권 PDF 생성", use_container_width=True):
                with st.spinner("PDF 작업 중..."):
                    canv = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    cx, cy = 160, 160
                    for idx in selected_for_pdf:
                        im = st.session_state.collection[idx]["img"]
                        ratio = TARGET_H_PX / float(im.size[1])
                        resized = im.resize((int(im.size[0]*ratio), TARGET_H_PX), Image.LANCZOS)
                        if cx + resized.size[0] > A4_W_PX - 160:
                            cx = 160; cy += TARGET_H_PX + 70
                        canv.paste(resized, (cx, cy)); cx += resized.size[0] + 70
                    
                    pdf_io = io.BytesIO()
                    canv.save(pdf_io, format="PDF", resolution=300.0)
                    st.download_button("📂 PDF 다운로드", pdf_io.getvalue(), "my_shelf.pdf", use_container_width=True)
    else:
        st.info("기록된 도서가 없습니다.")

with tab_wish:
    # 위시리스트 상단 공백 추가 (서재 탭과 수평 일치)
    st.markdown('<div class="wish-top-spacer"></div>', unsafe_allow_html=True)
    
    if st.session_state.wishlist:
        wish_cols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wish_cols[i % 4]:
                try:
                    w_resp = requests.get(item['url'], headers={"User-Agent":"Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(w_resp))
                    st.image(w_img, use_container_width=True)
                    
                    # 버튼 수평 정렬
                    wb_cols = st.columns(2)
                    with wb_cols[0]:
                        # 읽기 완료 시 즉시 서재 이동
                        if st.button("📖 읽기 완료!", key=f"wdn_{i}"):
                            st.session_state.collection.append({
                                "img": w_img.convert("RGB"), "url": item['url'], 
                                "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')
                            })
                            st.session_state.wishlist.pop(i) # 위시에서 즉시 제거
                            commit_changes()
                            st.rerun() # UI 즉시 갱신
                    with wb_cols[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        # 삭제하기 -> 삭제 변경
                        if st.button("🗑️ 삭제", key=f"wdl_{i}"):
                            st.session_state.wishlist.pop(i)
                            commit_changes()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                except: continue
    else:
        st.info("위시리스트가 비어있습니다.")