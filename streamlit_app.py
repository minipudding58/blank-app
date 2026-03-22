import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date, timedelta
import calendar

# --- 기초 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 데이터 관리 (날짜 정보 포함) ---
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

def save_data():
    data = {
        "wishlist": st.session_state.wishlist,
        "collection": [
            {"url": itm["url"], "start": itm["start"], "end": itm["end"]} 
            for itm in st.session_state.collection
        ]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            st.session_state.wishlist = d.get("wishlist", [])
            for itm in d.get("collection", []):
                try:
                    r = requests.get(itm["url"], timeout=5)
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.collection.append({
                        "img": img, "url": itm["url"], 
                        "start": itm.get("start"), "end": itm.get("end")
                    })
                except: continue

# --- 상단 통계 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
this_year = datetime.now().year
total_books = len(st.session_state.collection)
st.subheader(f"📊 {this_year}년 누적 독서: {total_books}권")

# --- 🔍 검색 및 등록 (기간 설정 추가) ---
query = st.text_input("새로운 책 등록하기", placeholder="책 제목 입력")
if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent":"Mozilla/5.0"})
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover\d*[^"\'\s>]+', res.text)))
    
    if imgs:
        cols = st.columns(4)
        for i, img_url in enumerate(imgs[:4]):
            with cols[i]:
                st.image(img_url, use_container_width=True)
                with st.expander("📖 읽은 기간 설정"):
                    d_range = st.date_input("독서 기간", [date.today(), date.today()], key=f"date_{i}")
                    if st.button("기록 추가", key=f"add_{i}"):
                        r = requests.get(img_url)
                        img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({
                            "img": img_obj, "url": img_url,
                            "start": d_range[0].isoformat(),
                            "end": d_range[1].isoformat() if len(d_range)>1 else d_range[0].isoformat()
                        })
                        save_data(); st.rerun()

st.divider()

# --- 📅 독서 달력 (현재 달 기준) ---
st.header(f"📅 {datetime.now().month}월의 독서 달력")
today = date.today()
cal = calendar.monthcalendar(today.year, today.month)
weekdays = ["월", "화", "수", "목", "금", "토", "일"]

# 달력 헤더
cols = st.columns(7)
for idx, day_name in enumerate(weekdays):
    cols[idx].write(f"**{day_name}**")

# 달력 날짜 채우기
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            with cols[i]:
                st.write(f"**{day}**")
                current_date = date(today.year, today.month, day).isoformat()
                # 해당 날짜에 읽은 책들 찾기
                for book in st.session_state.collection:
                    if book["start"] <= current_date <= book["end"]:
                        st.image(book["url"], use_container_width=True)

st.divider()

# --- 📖 읽은 책 목록 & PDF ---
c1, c2 = st.columns([3, 1])
with c1: st.header("📚 전체 읽은 책 목록")
with c2:
    if st.session_state.collection:
        # PDF 생성 (간략화)
        if st.button("📥 PDF로 소장하기"):
            st.info("준비 중인 기능입니다. (위의 PDF 코드를 결합하여 사용 가능)")

if st.session_state.collection:
    dcols = st.columns(6)
    for idx, itm in enumerate(st.session_state.collection):
        with dcols[idx % 6]:
            st.image(itm["img"], caption=f"{itm['start']} ~ {itm['end']}", use_container_width=True)
            if st.button("❌", key=f"del_{idx}"):
                st.session_state.collection.pop(idx); save_data(); st.rerun()