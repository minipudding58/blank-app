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
# ⚙️ 1. 전역 설정 및 상수
# ==========================================
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(
    page_title="나의 독서 기록장",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 2. 스타일 시트 (버튼 강제 밀착 정렬 로직)
# ==========================================
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 2.5rem !important; max-width: 1200px; }}
    
    .main-title {{ 
        font-size: 44px; font-weight: 800; color: #1E1E1E; 
        margin-bottom: 55px !important; letter-spacing: -0.5px !important; line-height: 1.6 !important; 
        padding-top: 15px; font-family: 'Pretendard', sans-serif;
    }}

    /* 버튼 벌어짐 방지를 위한 커스텀 컨테이너 */
    .stHorizontalBlock {{
        gap: 8px !important; /* 컬럼 사이 간격을 8px로 고정 */
    }}
    
    div[data-testid="column"] {{
        width: fit-content !important;
        flex: none !important;
    }}

    .wish-top-spacer {{ height: 74px !important; display: block; }}
    .header-label {{ font-size: 16px !important; font-weight: 600 !important; color: #666 !important; margin-bottom: 12px; display: block; }}
    .total-count-display {{ font-size: 56px; font-weight: 900; color: #87CEEB; line-height: 1; }}
    
    .genre-card-item {{ 
        background-color: #FFFFFF; border: 1px solid #EAEAEA; border-radius: 14px; 
        padding: 12px 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03); min-width: 90px;
    }}

    /* 버튼 스타일 통일 */
    .stButton button {{
        width: 100px !important; /* 버튼 너비를 고정하여 균형 맞춤 */
        height: 40px !important;
        border-radius: 8px !important; 
        font-weight: 600 !important;
        padding: 0px !important;
    }}

    [data-testid="stImage"] img {{ height: 220px !important; object-fit: contain !important; border-radius: 10px; border: 1px solid #F0F0F0; }}
    
    .del-btn-red button {{ background-color: transparent !important; border: 1px solid #FF6B6B !important; }}
    .del-btn-red button p {{ color: #FF6B6B !important; }}
    .date-text {{ font-size: 13px; color: #999; display: block; margin-top: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🗝️ 3. 데이터 관리 로직
# ==========================================
if 'user_id' not in st.session_state:
    try:
        if "user" in st.query_params: st.session_state.user_id = st.query_params["user"]
        else:
            st.markdown("<div class='main-title'>📖 독서 기록장 입장</div>", unsafe_allow_html=True)
            u_input = st.text_input("닉네임", placeholder="예: 먼작귀", label_visibility="collapsed")
            if st.button("입장") and u_input:
                st.session_state.user_id = u_input; st.query_params["user"] = u_input; st.rerun()
            st.stop()
    except: st.stop()

USER_DATA_PATH = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    if 'search_cache' not in st.session_state: st.session_state.search_cache = {"query": "", "items": []}
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                st.session_state.wishlist = loaded.get("wishlist", [])
                for item in loaded.get("collection", []):
                    try:
                        resp = requests.get(item["url"], timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                        if resp.status_code == 200:
                            st.session_state.collection.append({"img": Image.open(io.BytesIO(resp.content)).convert("RGB"), "url": item["url"], "start": item.get("start"), "end": item.get("end"), "genre": item.get("genre", "미지정")})
                    except: continue
        except: pass

def commit_changes():
    payload = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i["genre"]} for i in st.session_state.collection]}
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f: json.dump(payload, f, ensure_ascii=False, indent=4)

# ==========================================
# 📊 4. 대시보드
# ==========================================
st.markdown(f"<div class='main-title'>{st.session_state.user_id}의 독서기록</div>", unsafe_allow_html=True)
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

st.divider()

# ==========================================
# 🔍 5. 검색 결과 (버튼 밀착)
# ==========================================
st.markdown("<span class='header-label'>🔍 새로운 도서 검색</span>", unsafe_allow_html=True)
q_in = st.text_input("검색", placeholder="제목/저자 입력", label_visibility="collapsed")

if q_in and q_in != st.session_state.search_cache["query"]:
    try:
        res_text = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q_in}", headers={"User-Agent":"Mozilla/5.0"}).text
        imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', res_text)))
        genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res_text)
        st.session_state.search_cache["items"] = [{"url": imgs[i], "genre": genres[i] if i < len(genres) else "미지정"} for i in range(min(4, len(imgs)))]
        st.session_state.search_cache["query"] = q_in
    except: st.error("검색 실패")

if st.session_state.search_cache["items"]:
    s_cols = st.columns(4)
    for idx, item in enumerate(st.session_state.search_cache["items"]):
        with s_cols[idx]:
            st.image(item["url"], use_container_width=True)
            # 검색 결과 버튼 밀착
            btn_col1, btn_col2, _ = st.columns([1, 1, 2])
            with btn_col1:
                if st.button("📖 읽음", key=f"s_add_lib_{idx}"):
                    img_raw = requests.get(item["url"], headers={"User-Agent":"Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_raw)).convert("RGB"), "url": item["url"], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item["genre"]})
                    commit_changes(); st.rerun()
            with btn_col2:
                if st.button("🩵 위시", key=f"s_add_wish_{idx}"):
                    st.session_state.wishlist.append({"url": item["url"], "genre": item["genre"]})
                    commit_changes(); st.rerun()

st.divider()

# ==========================================
# 📚 6. 메인 탭 (저장/삭제 밀착)
# ==========================================
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
    is_edit = st.toggle("편집 및 PDF 모드 활성화", key="edit_toggle_full")
    selected_for_pdf = []
    if st.session_state.collection:
        lib_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with lib_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                if is_edit:
                    if st.checkbox("선택", key=f"chk_{i}", value=True): selected_for_pdf.append(i)
                    new_g = st.text_input("장르", value=item['genre'], key=f"eg_{i}", label_visibility="collapsed")
                    try: d_range = (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
                    except: d_range = (date.today(), date.today())
                    new_d = st.date_input("날짜", d_range, key=f"ed_{i}", label_visibility="collapsed")
                    
                    # 내 서재 버튼 밀착
                    edit_btn_col1, edit_btn_col2, _ = st.columns([1, 1, 2])
                    with edit_btn_col1:
                        if st.button("저장", key=f"esv_{i}"):
                            sd = new_d[0].isoformat() if isinstance(new_d, (list, tuple)) else new_d.isoformat()
                            ed = new_d[1].isoformat() if isinstance(new_d, (list, tuple)) and len(new_d) > 1 else sd
                            st.session_state.collection[i].update({"genre": new_g, "start": sd, "end": ed})
                            commit_changes(); st.rerun()
                    with edit_btn_col2:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"edl_{i}"):
                            st.session_state.collection.pop(i); commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**장르: {item['genre']}**")
                    st.markdown(f'<span class="date-text">{item["start"]} ~ {item["end"]}</span>', unsafe_allow_html=True)

        if is_edit and selected_for_pdf:
            st.divider()
            if st.button(f"📥 선택한 {len(selected_for_pdf)}권 PDF 생성", use_container_width=True):
                with st.spinner("PDF 생성 중..."):
                    canv = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    cx, cy = 160, 160
                    for idx in selected_for_pdf:
                        im = st.session_state.collection[idx]["img"]; ratio = TARGET_H_PX / float(im.size[1])
                        resized = im.resize((int(im.size[0]*ratio), TARGET_H_PX), Image.LANCZOS)
                        if cx + resized.size[0] > A4_W_PX - 160: cx = 160; cy += TARGET_H_PX + 70
                        canv.paste(resized, (cx, cy)); cx += resized.size[0] + 70
                    pdf_io = io.BytesIO(); canv.save(pdf_io, format="PDF", resolution=300.0)
                    st.download_button("📂 PDF 다운로드", pdf_io.getvalue(), "my_shelf.pdf", use_container_width=True)
    else: st.info("기록된 도서가 없습니다.")

with tab_wish:
    st.markdown('<div class="wish-top-spacer"></div>', unsafe_allow_html=True)
    if st.session_state.wishlist:
        wish_cols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wish_cols[i % 4]:
                try:
                    w_resp = requests.get(item['url'], headers={"User-Agent":"Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(w_resp))
                    st.image(w_img, use_container_width=True)
                    # 위시리스트 버튼 밀착
                    wish_btn_col1, wish_btn_col2, _ = st.columns([1, 1, 2])
                    with wish_btn_col1:
                        if st.button("📖 완료", key=f"wdn_{i}"):
                            st.session_state.collection.append({"img": w_img.convert("RGB"), "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                            st.session_state.wishlist.pop(i); commit_changes(); st.rerun()
                    with wish_btn_col2:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("🗑️ 삭제", key=f"wdl_{i}"):
                            st.session_state.wishlist.pop(i); commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                except: continue
    else: st.info("위시리스트가 비어있습니다.")