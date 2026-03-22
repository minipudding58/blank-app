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
TARGET_H_PX = int((35 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 데이터 로드 및 저장 ---
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
    st.session_state.cal_year = date.today().year
    st.session_state.cal_month = date.today().month
    
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
                            "start": itm.get("start"), "end": itm.get("end"),
                            "genre": itm.get("genre", "미지정")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist,
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🎨 스타일 설정 ---
st.markdown("""
    <style>
    .big-font { font-size: 32px !important; font-weight: bold !important; margin-bottom: 20px !important; display: block; }
    /* 달력 크기 확대 및 이모지 배치 */
    .cal-box { height: 80px; border: 1px solid #f0f2f6; border-radius: 5px; text-align: center; display: flex; flex-direction: column; justify-content: flex-start; }
    .cal-day-num { font-size: 14px; font-weight: bold; margin-top: 5px; }
    .cal-book-emoji { font-size: 24px; margin-top: 2px; }
    /* 버튼 높이 통일 */
    div.stButton > button { height: 42px !important; }
    /* 날짜 입력창 폰트 작게 하여 줄바꿈 방지 보조 */
    .stDateInput div[data-baseweb="input"] { font-size: 13px !important; padding: 2px 5px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)
st.divider()

# --- 📊 상단 대시보드 ---
t_col1, t_col2 = st.columns([1, 2])
with t_col1:
    st.markdown(f"<div style='text-align:center; padding: 20px;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:60px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    st.write("---")
    st.caption("📚 장르별 독서 현황")
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with t_col2:
    # 달력 컨트롤
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전 달", use_container_width=True):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h3 style='text-align:center; margin:0;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
    if mc3.button("다음 달 ▶", use_container_width=True):
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
                with cols[i]:
                    is_reading = any(b["start"] <= curr <= b["end"] for b in st.session_state.collection)
                    st.markdown(f"<div class='cal-box'><div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    if is_reading: st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 검색 섹션 (장르 자동 표기 강화) ---
st.markdown("<span class='big-font'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed", placeholder="예: 먼작귀")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                # 장르 추출 로직 강화
                found_genre = "미지정"
                try:
                    genre_match = re.search(r'\[<a[^>]+>([^<]+)</a>\]', res)
                    if genre_match: found_genre = genre_match.group(1)
                except: pass
                
                sel_genre = st.text_input("장르", value=found_genre, key=f"s_g_{i}")
                dr = st.date_input("읽은 기간", [date.today(), date.today()], key=f"s_dr_{i}")
                
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"b_r_{i}"):
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(requests.get(url).content)).convert("RGB"), "url": url,
                        "start": dr[0].isoformat(), "end": dr[1].isoformat() if len(dr)>1 else dr[0].isoformat(),
                        "genre": sel_genre
                    })
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"b_w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 읽은 책 모음 (날짜 가독성 & 버튼 정렬) ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='big-font'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        print_indices = []
        c1, c2 = st.columns(2)
        if c1.button("🗑️ 전체 삭제"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = c2.toggle("개별 삭제 모드")

        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄 포함", key=f"p_{idx}", value=True): print_indices.append(idx)
                
                # 날짜 입력창과 수정 버튼 나란히 배치
                date_c1, date_c2 = st.columns([2, 1])
                with date_c1:
                    new_dr = st.date_input("수정", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"e_d_{idx}", label_visibility="collapsed")
                with date_c2:
                    if st.button("수정", key=f"s_d_{idx}"):
                        if len(new_dr) == 2:
                            st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                            st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                            save_all(); st.rerun()
                
                # 날짜 표시 (위아래로 늘려서 표시)
                st.caption(f"📅 {itm['start']} \n\n ~ {itm['end']}")
                
                if del_m and st.button("❌ 삭제", key=f"d_i_{idx}"):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
                st.write("---")

        if print_indices:
            pdf_buf = io.BytesIO()
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for idx in print_indices:
                img = st.session_state.collection[idx]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                if y + TARGET_H_PX > A4_H_PX - 100: break
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택 {len(print_indices)}권 PDF 인쇄", pdf_buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='big-font'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                st.image(item['url'], use_container_width=True)
                if st.button("✅ 이동", key=f"m_{i}"):
                    img = Image.open(io.BytesIO(requests.get(item['url']).content)).convert("RGB")
                    st.session_state.collection.append({"img": img, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if st.button("🗑️ 제거", key=f"w_d_{i}"): st.session_state.wishlist.pop(i); save_all(); st.rerun()