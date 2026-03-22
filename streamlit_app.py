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

# --- 설정 및 데이터 관리 ---
DPI = 300
TARGET_H_PX = 400 # 목록 이미지 세로 높이 고정
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("닉네임 입력")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input; st.query_params["user"] = u_input; st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

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

# --- 🎨 스타일 설정 (이모지 위치 및 버튼 정렬 강제) ---
st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold !important; margin-bottom: 15px; display: block; }
    /* 1. 달력 이모지 숫자 밑으로 딱 붙이기 */
    .cal-box { height: 55px; border: 1px solid #eee; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: white; }
    .cal-day-num { font-size: 13px; font-weight: bold; line-height: 1; margin-bottom: 2px; }
    .cal-book-emoji { font-size: 16px; line-height: 1; }
    /* 3. 버튼 및 네모칸 넉넉하게 */
    div.stButton > button { height: 45px !important; font-size: 14px !important; border-radius: 6px !important; }
    .stDateInput div[data-baseweb="input"] { height: 45px !important; }
    /* 위시리스트 테두리 제거 */
    [data-testid="stVerticalBlockBorderWrapper"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)
st.divider()

# --- 📊 대시보드 및 달력 ---
t_col1, t_col2 = st.columns([1, 1.4])
with t_col1:
    st.markdown(f"<div style='text-align:center;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:55px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    st.divider()
    st.caption("📚 장르별 독서 현황")
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with t_col2:
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전 달"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h3 style='text-align:center; margin:0;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
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
                    st.markdown(f"<div class='cal-box'><div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    if is_reading: st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 검색 (장르 연동 보강) ---
st.markdown("<span class='big-font'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed", placeholder="예: 먼작귀")

if query:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # 장르 추출 정규식: [<a ...>장르명</a>] 패턴 정밀 타겟팅
    found_genres = re.findall(r'\[<a href=[^>]+>([^<]+)</a>\]', res)

    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                g_val = found_genres[i] if i < len(found_genres) else "미지정"
                sel_genre = st.text_input("장르", value=g_val, key=f"gen_{i}")
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"read_{i}"):
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(requests.get(url).content)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"wish_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 하단 목록 (정렬 및 높이 고정) ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='big-font'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    # 3. 전체비우기-개별삭제-PDF인쇄 일렬 정렬
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 1, 1.5])
    with ctrl_c1: 
        if st.button("🗑️ 전체 비우기", use_container_width=True): st.session_state.collection = []; save_all(); st.rerun()
    with ctrl_c2:
        del_m = st.toggle("개별 삭제 모드")
    
    print_list = []
    dcols = st.columns(3)
    for idx, itm in enumerate(st.session_state.collection):
        with dcols[idx % 3]:
            # 세로 높이 고정 이미지 출력
            st.image(itm["img"], height=TARGET_H_PX)
            if st.checkbox("인쇄 선택", key=f"ck_{idx}", value=True): print_list.append(idx)
            # 장르칸 높이 맞추기 위해 공백 포함
            st.markdown(f"<div style='height:45px; display:flex; align-items:center;'><b>장르: {itm['genre']}</b></div>", unsafe_allow_html=True)
            new_dr = st.date_input("날짜", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"dt_{idx}", label_visibility="collapsed")
            
            btn_c1, btn_c2 = st.columns([2, 1])
            with btn_c1:
                if st.button("수정", key=f"up_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
            with btn_c2:
                if del_m and st.button("❌", key=f"del_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
            st.write("---")
            
    with ctrl_c3:
        if print_list:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x_p, y_p = 100, 100
            for i in print_list:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x_p + img_res.size[0] > A4_W_PX - 100: x_p = 100; y_p += TARGET_H_PX + 40
                sheet.paste(img_res, (x_p, y_p)); x_p += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택 {len(print_list)}권 PDF 인쇄", buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='big-font'>🩵 위시리스트</span>", unsafe_allow_html=True)
    # 5. 위시리스트 시작 위치 맞춤 (상단 컨트롤 바 높이만큼 공백)
    st.markdown("<div style='height:65px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                # 이미지 세로 높이 고정
                st.image(item['url'], height=TARGET_H_PX)
                st.markdown(f"<div style='height:45px; display:flex; align-items:center;'><b>장르: {item['genre']}</b></div>", unsafe_allow_html=True)
                
                # 4. 빈 네모+읽음 -> 선택이모지+읽음 로직
                wc1, wc2 = st.columns(2)
                if wc1.button("⬜ 읽음", key=f"wi_r_{i}", use_container_width=True):
                    # 클릭 즉시 시각적 피드백을 위해 세션에 반영 후 리런
                    img = Image.open(io.BytesIO(requests.get(item['url']).content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if wc2.button("🗑️ 삭제", key=f"wi_d_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                st.write("---")