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

# --- 데이터 관리 ---
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

# --- 🎨 디자인 스타일 ---
st.markdown("""
    <style>
    .big-font { font-size: 32px !important; font-weight: bold !important; margin-bottom: 20px !important; display: block; }
    /* 달력 칸 크기 최적화 및 이모지 안으로 넣기 */
    .cal-box { height: 65px; border: 1px solid #eee; border-radius: 4px; text-align: center; background: white; }
    .cal-day-num { font-size: 13px; color: #555; margin-top: 2px; }
    .cal-book-emoji { font-size: 18px; margin-top: -2px; }
    /* 버튼 정렬 */
    div.stButton > button { width: 100%; height: 35px !important; padding: 0 !important; font-size: 13px !important; }
    .stDateInput div[data-baseweb="input"] { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)
st.divider()

# --- 📊 상단 섹션 ---
t_col1, t_col2 = st.columns([1, 2])
with t_col1:
    st.markdown(f"<div style='text-align:center;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:55px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    st.write("---")
    st.caption("📚 장르별 독서 현황")
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with t_col2:
    # 달력 컨트롤
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h3 style='text-align:center; margin:0;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
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
                with cols[i]:
                    is_reading = any(b["start"] <= curr <= b["end"] for b in st.session_state.collection)
                    st.markdown(f"<div class='cal-box'><div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    if is_reading: st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 검색 섹션 (장르 연동 강화) ---
st.markdown("<span class='big-font'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed", placeholder="예: 먼작귀")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # 장르 추출 정규식 강화
    genres_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)

    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                genre_val = genres_raw[i] if i < len(genres_raw) else "미지정"
                sel_genre = st.text_input("장르", value=genre_val, key=f"sq_{i}")
                
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"sr_{i}"):
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(requests.get(url).content)).convert("RGB"), "url": url,
                        "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                    })
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"sw_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 목록 섹션 (날짜 통합 수정 & 버튼 일자 정렬) ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='big-font'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        print_list = []
        ctrl1, ctrl2 = st.columns(2)
        if ctrl1.button("🗑️ 전체 삭제"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = ctrl2.toggle("개별 삭제 모드")

        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): print_list.append(idx)
                
                # 날짜 수정 (한 줄 정렬)
                st.caption("읽은 기간 수정")
                date_c1, date_c2 = st.columns([3, 1])
                with date_c1:
                    new_dr = st.date_input("날짜", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"ed_{idx}", label_visibility="collapsed")
                with date_c2:
                    if st.button("수정", key=f"sv_{idx}"):
                        if len(new_dr) == 2:
                            st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                            st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                            save_all(); st.rerun()
                
                if del_m and st.button("❌ 삭제", key=f"di_{idx}"):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
                st.write("---")

        if print_list:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for i in print_list:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택 {len(print_list)}권 PDF 인쇄", buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='big-font'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                with st.container(border=True):
                    st.image(item['url'], use_container_width=True)
                    # ✅ 4번 요구사항: 버튼 디자인 및 일자 정렬
                    bt1, bt2 = st.columns(2)
                    if bt1.button("⬜ 읽음", key=f"wr_{i}"):
                        img = Image.open(io.BytesIO(requests.get(item['url']).content)).convert("RGB")
                        st.session_state.collection.append({"img": img, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if bt2.button("🗑️ 삭제", key=f"wd_{i}"):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()