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

# --- 기초 규격 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) # 목록용 세로 길이 고정
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 스타일 설정 (이모지 간격 밀착 및 레이아웃 유지) ---
st.markdown(f"""
    <style>
    /* 1. 달력 숫자와 이모지 사이 간격 최소화 (사용자 요청 반영) */
    .cal-box {{
        text-align: center;
        display: block;
        background-color: transparent !important;
        border: none !important;
        line-height: 1.0 !important;
    }}
    .cal-day-num {{
        font-size: 13px;
        font-weight: bold;
        display: block;
        margin-bottom: -3px !important; /* 바짝 밀착 */
    }}
    .cal-book-emoji {{
        font-size: 18px;
        display: block;
        margin-top: 0px !important;
    }}

    /* 2. 네모 버튼 및 입력창 규격 유지 */
    div.stButton > button, div.stDownloadButton > button {{
        width: 100% !important;
        height: 45px !important;
        border-radius: 5px;
    }}
    .stDateInput div[data-baseweb="input"] {{
        height: 45px !important;
        border-radius: 5px;
    }}
    
    /* 3. 제목 폰트 설정 */
    .section-title {{
        font-size: 24px !important;
        font-weight: bold !important;
        margin-bottom: 15px !important;
        display: block;
    }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "User")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로드 (이미지 객체 포함 기능 복구) ---
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
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": itm["url"],
                            "start": itm.get("start"), "end": itm.get("end"), "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.divider()

# --- 상단: 통계 및 달력 ---
t_col1, t_col2 = st.columns([1, 1.2])
with t_col1:
    st.markdown(f"<div style='text-align:center;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:60px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    st.divider()
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with t_col2:
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전 달"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h3 style='text-align:center;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
    if mc3.button("다음 달 ▶"):
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
                    st.markdown(f"<div class='cal-box'><span class='cal-day-num'>{day}</span>" + 
                                (f"<span class='cal-book-emoji'>📖</span>" if is_reading else "") + "</div>", unsafe_allow_html=True)

st.divider()

# --- 검색 ---
st.markdown("<span class='section-title'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed")
if query:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                g_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                sel_genre = st.text_input("장르", value=g_val, key=f"src_g_{i}")
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
    st.markdown("<span class='section-title'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        print_Indices = []
        ctrl_c1, ctrl_c2 = st.columns([1, 2])
        if ctrl_c1.button("🗑️ 전체 비우기"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = ctrl_c2.toggle("개별 삭제 모드")
        
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                # 이미지 세로 길이 고정
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): print_Indices.append(idx)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                
                # 날짜 처리
                try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: val = [date.today(), date.today()]
                new_dr = st.date_input("기간", val, key=f"e_d_{idx}", label_visibility="collapsed")
                
                b_c1, b_c2 = st.columns([2, 1])
                if b_c1.button("수정", key=f"sv_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and b_c2.button("❌", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
                st.write("---")

        if print_Indices:
            # PDF 생성 로직 복구
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x_pos, y_pos = 100, 100
            for i in print_Indices:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x_pos + img_res.size[0] > A4_W_PX - 100: x_pos = 100; y_pos += TARGET_H_PX + 40
                sheet.paste(img_res, (x_pos, y_pos)); x_pos += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택 {len(print_Indices)}권 PDF 인쇄", buf.getvalue(), "my_record.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    st.write(""); st.write("")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                # 위시리스트도 세로 정렬을 위해 이미지 로드
                r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(f"장르: {item.get('genre', '미지정')}")
                c1, c2 = st.columns(2)
                if c1.button("✅ 선택", key=f"wr_{i}"):
                    st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if c2.button("🗑️ 삭제", key=f"wd_{i}"):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                st.write("---")