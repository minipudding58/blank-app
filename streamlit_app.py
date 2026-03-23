import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (폰트 크기 강제 적용 및 간격/선 최적화) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* 상단 통계 스타일 */
    .stat-container {{ text-align: center; }}
    .genre-wrapper {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 5px 12px;
        min-width: 60px;
        text-align: center;
    }}
    .genre-label {{ font-size: 12px; color: #888; }}
    .genre-value {{ font-size: 16px; font-weight: bold; color: #333; }}

    /* [기준] 타이틀 폰트: 18px, Bold */
    .section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 12px; 
        display: block; 
        color: #31333F;
    }}

    /* 탭 디자인 (책 검색 타이틀과 동일한 크기/굵기 강제 적용) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px !important;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        padding-left: 40px !important;  /* 선 길이를 확보하기 위한 좌우 패딩 */
        padding-right: 40px !important;
        margin-right: 40px !important;  /* 탭 사이 간격 */
    }}
    /* 탭 내부 글자 크기를 18px로 강제 수정 */
    .stTabs [data-baseweb="tab"] p {{
        font-size: 18px !important;
        font-weight: bold !important;
        color: #31333F !important;
    }}

    /* 하단 하늘색 강조선 (얇게 2px) */
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #87CEEB !important;
        height: 2px !important;
    }}

    /* 이미지 및 버튼 스타일 */
    [data-testid="stImage"] img {{
        height: 200px !important;
        object-fit: contain !important;
        background-color: #f9f9f9;
        border-radius: 5px;
    }}
    div.stButton > button {{
        padding: 2px 5px !important;
        height: 35px !important;
        font-size: 14px !important;
    }}
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
                                    "url": u,
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

# --- 🏠 5. 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.user_id}** 님의 서재")
    st.write("---")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    if st.button("🗑️ 내 데이터 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# --- 📊 6. 상단 통계 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.write("")

t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    st.markdown(f"""
        <div class="stat-container">
            <div style="font-size: 14px; color: #666;">{datetime.now().year}년 누적</div>
            <div style="font-size: 40px; font-weight: bold; color: #87CEEB;">✨{len(st.session_state.collection)}권✨</div>
        </div>
    """, unsafe_allow_html=True)
with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items = "".join([f"<div class='genre-card'><div class='genre-label'>{g}</div><div class='genre-value'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-wrapper'>{genre_items}</div>", unsafe_allow_html=True)
    else: st.caption("기록이 없습니다.")

st.divider()

# --- 🔍 7. 책 검색 섹션 ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력창", placeholder="제목/저자 입력...", label_visibility="collapsed")
if q:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', res)))
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                sel_genre = st.text_input("장르", value="미지정", key=f"sg_{i}", label_visibility="collapsed")
                b_cols = st.columns(2)
                if b_cols[0].button("📖 읽음", key=f"r_{i}", use_container_width=True):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                    save_all(); st.rerun()
                if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()
    else: st.warning("검색 결과가 없습니다.")

st.divider()

# --- 📚 8. 하단 탭 (내 서재 & 위시리스트) ---
tab_library, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_library:
    st.write("")
    if st.session_state.collection:
        p_idx = []; del_m = st.toggle("삭제 모드", key="del_lib")
        dcols = st.columns(4)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): p_idx.append(idx)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: val = [date.today(), date.today()]
                new_dr = st.date_input("읽은 기간", val, key=f"ed_{idx}", label_visibility="collapsed")
                b_edit_cols = st.columns([2, 1])
                if b_edit_cols[0].button("수정", key=f"sv_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and b_edit_cols[1].button("❌", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
        
        st.write("---")
        if p_idx:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for i in p_idx:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택한 {len(p_idx)}권 PDF 저장", buf.getvalue(), "my_library.pdf", use_container_width=True)
    else: st.info("서재가 비어 있습니다.")

with tab_wish:
    st.write("")
    if st.session_state.wishlist:
        wcols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 4]:
                url = item.get('url') if isinstance(item, dict) else item
                try:
                    r_img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                    st.image(img_obj, use_container_width=True)
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    wb_cols = st.columns(2)
                    if wb_cols[0].button("📖 읽음 완료", key=f"wr_{i}", use_container_width=True):
                        st.session_state.collection.append({"img": img_obj, "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if wb_cols[1].button("🗑️ 삭제", key=f"w_d_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                except: st.error("이미지 로드 실패")
    else: st.info("위시리스트가 비어 있습니다.")