import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
import calendar
from collections import Counter

# --- 설정 및 데이터 규격 ---
DPI = 300
TARGET_H_PX = 380 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# CSS: 다른 곳은 유지, 달력 높이와 내부 정렬만 수정
st.markdown(f"""
    <style>
    .big-font {{ font-size: 26px !important; font-weight: bold !important; margin-bottom: 10px; display: block; }}
    /* ✅ 달력 칸 높이 축소 및 이모지 중앙 정렬 */
    .cal-box {{ 
        height: 50px !important; 
        border: 1px solid #eee; 
        border-radius: 4px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center; 
        background: #fdfdfd;
    }}
    .cal-day-num {{ font-size: 13px; font-weight: bold; line-height: 1; }}
    .cal-book-emoji {{ font-size: 16px; margin-top: 2px; line-height: 1; }}
    
    /* 기존 레이아웃 규격 유지 */
    div.stButton > button, .stDateInput div[data-baseweb="input"] {{ 
        height: 45px !important; 
        border-radius: 6px !important; 
    }}
    .book-img-fixed {{ height: {TARGET_H_PX}px !important; object-fit: contain; width: 100%; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "User")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로드 (이미지 객체 포함) ---
if 'collection' not in st.session_state:
    st.session_state.collection = []; st.session_state.wishlist = []
    st.session_state.cal_year, st.session_state.cal_month = date.today().year, date.today().month
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    r = requests.get(itm["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                            "url": itm["url"], "start": itm.get("start"), "end": itm.get("end"), 
                            "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.divider()

# --- 상단 섹션 ---
t_col1, t_col2 = st.columns([1, 1.2])
with t_col1:
    st.markdown(f"<div style='text-align:center;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:50px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        st.write(f"**장르:** " + ", ".join([f"{g} {c}" for g, c in counts.items()]))

with t_col2:
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h4 style='text-align:center;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h4>", unsafe_allow_html=True)
    if mc3.button("다음 ▶"):
        if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        else: st.session_state.cal_month += 1
        st.rerun()
    
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    w_cols = st.columns(7)
    for i, dname in enumerate(["일", "월", "화", "수", "목", "금", "토"]): w_cols[i].caption(dname)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                curr = date(st.session_state.cal_year, st.session_state.cal_month, day).isoformat()
                is_reading = any(b["start"] <= curr <= b["end"] for b in st.session_state.collection)
                with cols[i]:
                    st.markdown(f"<div class='cal-box'><div class='cal-day-num'>{day}</div>" + 
                                (f"<div class='cal-book-emoji'>📖</div>" if is_reading else "") + "</div>", unsafe_allow_html=True)

st.divider()

# --- 검색 섹션 ---
st.markdown("<span class='big-font'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed")
if query:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    found_genres = re.findall(r'\[<a[^>]*>([^<]+)</a>\]', res)
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.markdown(f"<img src='{url}' class='book-img-fixed'>", unsafe_allow_html=True)
                g_val = found_genres[i] if i < len(found_genres) else "미지정"
                sel_genre = st.text_input("장르", value=g_val, key=f"g_{i}")
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_{i}", use_container_width=True):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_{i}", use_container_width=True):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 하단 목록 및 인쇄 기능 ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='big-font'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    print_indices = []
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 1, 1.5])
    with ctrl_c1: 
        if st.button("🗑️ 전체 비우기", use_container_width=True): st.session_state.collection = []; save_all(); st.rerun()
    with ctrl_c2: del_m = st.toggle("개별 삭제 모드")
    
    dcols = st.columns(3)
    for idx, itm in enumerate(st.session_state.collection):
        with dcols[idx % 3]:
            st.markdown(f"<img src='{itm['url']}' class='book-img-fixed'>", unsafe_allow_html=True)
            if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): print_indices.append(idx)
            st.markdown(f"<div style='height:35px; margin-top:10px; font-weight:bold;'>장르: {itm['genre']}</div>", unsafe_allow_html=True)
            
            # ✅ TypeError 방지 날짜 처리
            try:
                val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
            except: val = [date.today(), date.today()]
            
            new_dr = st.date_input("기간", val, key=f"dt_{idx}", label_visibility="collapsed")
            
            b_c1, b_c2 = st.columns([2, 1])
            with b_c1:
                if st.button("수정", key=f"up_{idx}", use_container_width=True):
                    if isinstance(new_dr, list) and len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
            with b_c2:
                if del_m and st.button("❌", key=f"del_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
            st.write("---")

    with ctrl_c3:
        if print_indices:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x_p, y_p = 100, 100
            for i in print_indices:
                img = st.session_state.collection[i]["img"]
                ratio = (TARGET_H_PX * 2) / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX * 2), Image.LANCZOS)
                if x_p + img_res.size[0] > A4_W_PX - 100: x_p = 100; y_p += img_res.size[1] + 40
                sheet.paste(img_res, (x_p, y_p)); x_p += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택 {len(print_indices)}권 PDF 인쇄", buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='big-font'>🩵 위시리스트</span>", unsafe_allow_html=True)
    st.markdown("<div style='height:65px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, itm in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                st.markdown(f"<img src='{itm['url']}' class='book-img-fixed'>", unsafe_allow_html=True)
                st.markdown(f"<div style='height:35px; margin-top:10px; font-weight:bold;'>장르: {itm['genre']}</div>", unsafe_allow_html=True)
                
                wc1, wc2 = st.columns(2)
                if wc1.button("⬜ 읽음", key=f"wi_r_{i}", use_container_width=True):
                    img_data = requests.get(itm['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": itm['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": itm.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if wc2.button("🗑️ 삭제", key=f"wi_d_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                st.write("---")