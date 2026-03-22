import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
import calendar

# --- 기초 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide", initial_sidebar_state="expanded")

# --- 🔗 URL 닉네임 인식 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임 입력")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 💾 데이터 관리 함수 ---
def save_data():
    data = {
        "wishlist": st.session_state.wishlist,
        "collection": [
            {"url": itm["url"], "start": itm.get("start"), "end": itm.get("end")} 
            for itm in st.session_state.collection
        ]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    r = requests.get(itm["url"], timeout=5)
                    if r.status_code == 200:
                        img = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({
                            "img": img, "url": itm["url"], 
                            "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

# --- 🎨 스타일 설정 ---
st.markdown("""
    <style>
    .stats-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
    .cal-text { font-size: 11px; }
    div.stButton > button p { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 사이드바 ---
with st.sidebar:
    st.write(f"👤 **{st.session_state.user_id}** 님")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    st.write("---")
    if st.button("🔥 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# --- 📊 상단 미니 대시보드 (통계 & 달력) ---
head_col1, head_col2 = st.columns([1, 2])

with head_col1:
    st.markdown(f"""<div class="stats-card">
        <h3>{datetime.now().year} 누적 독서</h3>
        <h1 style="color: #ff4b4b;">{len(st.session_state.collection)}권</h1>
    </div>""", unsafe_allow_html=True)

with head_col2:
    today = date.today()
    cal_obj = calendar.monthcalendar(today.year, today.month)
    st.write(f"📅 **{today.year}년 {today.month}월 독서 달력**")
    cal_cols = st.columns(7)
    days = ["월", "화", "수", "목", "금", "토", "일"]
    for i, d in enumerate(days): cal_cols[i].caption(d)
    
    for week in cal_obj:
        w_cols = st.columns(7)
        for i, d in enumerate(week):
            if d != 0:
                current_d = date(today.year, today.month, d).isoformat()
                is_reading = any(b.get("start") <= current_d <= b.get("end") for b in st.session_state.collection if b.get("start") and b.get("end"))
                if is_reading: w_cols[i].markdown(f"**{d}** ✨")
                else: w_cols[i].write(str(d))

st.title(f"📖 {st.session_state.user_id}의 독서 기록")

# --- 🔍 검색 및 등록 ---
query = st.text_input("책 제목 입력", placeholder="예: 먼작귀")
if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent":"Mozilla/5.0"})
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover\d*[^"\'\s>]+', res.text)))
    if imgs:
        cols = st.columns(4)
        for i, img_url in enumerate(imgs[:4]):
            with cols[i]:
                st.image(img_url, use_container_width=True)
                d_range = st.date_input("읽은 기간", [date.today(), date.today()], key=f"d_{i}")
                if st.button("📖 읽은 책 추가", key=f"btn_{i}", use_container_width=True):
                    r = requests.get(img_url)
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": img_url,
                        "start": d_range[0].isoformat(), "end": d_range[1].isoformat() if len(d_range)>1 else d_range[0].isoformat()
                    })
                    save_data(); st.rerun()

st.divider()

# --- 📚 하단: 복구된 기존 목록 섹션 ---
left_col, right_col = st.columns(2)

with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        b_col1, b_col2 = st.columns([1, 1])
        if b_col1.button("🗑️ 전체 비우기"):
            st.session_state.collection = []; save_data(); st.rerun()
        del_mode = b_col2.toggle("개별 삭제 모드")
        
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if del_mode and st.button("❌ 삭제", key=f"del_c_{idx}"):
                    st.session_state.collection.pop(idx); save_data(); st.rerun()
    else: st.info("아직 읽은 책이 없습니다.")

with right_col:
    st.header("🩵 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                st.image(item['url'], use_container_width=True)
                if st.button("🗑️ 삭제", key=f"del_w_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_data(); st.rerun()
    else: st.info("위시리스트가 비어있습니다.")