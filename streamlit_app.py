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

# --- 🔗 데이터 로드 및 저장 로직 ---
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

# --- 🎨 스타일 설정 (폰트 크기, 이모지 밀착, 레이아웃) ---
st.markdown("""
    <style>
    /* 제목 폰트 크기 완벽 일치 */
    .big-font {
        font-size: 32px !important;
        font-weight: bold !important;
        margin-bottom: 20px !important;
        display: block;
    }
    /* 달력 이모지 밀착 배치 */
    .cal-day-num { font-size: 13px; font-weight: bold; margin-bottom: -8px; text-align: center; }
    .cal-book-emoji { font-size: 18px; text-align: center; margin-top: -2px; line-height: 1; }
    /* 버튼 정렬 및 크기 최적화 */
    div.stButton > button { width: 100%; height: 38px !important; }
    /* 날짜 입력창 텍스트 크기 조정 */
    .stDateInput div[data-baseweb="input"] { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

# 최상단 타이틀
st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)
st.divider()

# --- 📊 상단 대시보드 (누적독서 & 달력) ---
t_col1, t_col2 = st.columns([1, 2])
with t_col1:
    # 배경색 제거 + ✨ 이모지
    st.markdown(f"<div style='text-align:center; padding: 20px;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:60px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    
    st.write("---")
    st.caption("📚 장르별 독서 현황")
    if st.session_state.collection:
        genres = [itm.get("genre", "미지정") for itm in st.session_state.collection]
        counts = Counter(genres)
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with t_col2:
    # 달력 컨트롤 (연월 제목과 같은 열)
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
                with cols[i]:
                    is_reading = any(b["start"] <= curr <= b["end"] for b in st.session_state.collection)
                    st.markdown(f"<div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    if is_reading:
                        st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 검색 섹션 (폰트 크기 일치 + 먼작귀 엑박 방지) ---
st.markdown("<span class='big-font'>📖 책 제목 입력</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed", placeholder="예: 먼작귀")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(search_url, headers=headers).text
    # 엑박 방지 이미지 추출
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # 장르 자동 추출
    genre_matches = re.findall(r'\[([^\]]+)\]', res)

    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                auto_genre = genre_matches[i] if i < len(genre_matches) else "만화"
                sel_genre = st.text_input("장르", value=auto_genre, key=f"src_g_{i}")
                dr = st.date_input("읽은 기간", [date.today(), date.today()], key=f"src_dr_{i}")
                
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"btn_r_{i}"):
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(requests.get(url).content)).convert("RGB"), "url": url,
                        "start": dr[0].isoformat(), "end": dr[1].isoformat() if len(dr)>1 else dr[0].isoformat(),
                        "genre": sel_genre
                    })
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"btn_w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 읽은 책 모음 & 선택 인쇄 ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='big-font'>📖 읽은 책 모음</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        # 선택된 인덱스 저장
        selected_to_print = []
        
        # 상단 컨트롤
        h_c1, h_c2 = st.columns([1, 1])
        if h_c1.button("🗑️ 전체 비우기"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = h_c2.toggle("개별 삭제 모드")

        st.write("")
        # 목록 루프
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                
                # 1. 인쇄 선택
                if st.checkbox("인쇄 포함", key=f"print_chk_{idx}", value=True):
                    selected_to_print.append(idx)
                
                # 2. 기간 수정 (버튼 분리 + 줄바꿈 레이아웃)
                st.caption("읽은 기간")
                new_dr = st.date_input("수정용", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"edit_date_{idx}", label_visibility="collapsed")
                
                if st.button("수정", key=f"save_date_{idx}"):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                        st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                        save_all(); st.rerun()
                
                if del_m and st.button("❌ 삭제", key=f"del_itm_{idx}"):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
                st.write("---")

        # PDF 생성 섹션
        if selected_to_print:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x_pos, y_pos = 100, 100
            for idx in selected_to_print:
                img_obj = st.session_state.collection[idx]["img"]
                ratio = TARGET_H_PX / float(img_obj.size[1])
                img_res = img_obj.resize((int(img_obj.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x_pos + img_res.size[0] > A4_W_PX - 100: x_pos = 100; y_pos += TARGET_H_PX + 40
                if y_pos + TARGET_H_PX > A4_H_PX - 100: break
                sheet.paste(img_res, (x_pos, y_pos)); x_pos += img_res.size[0] + 40
            
            pdf_buf = io.BytesIO(); sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택한 {len(selected_to_print)}권 PDF 인쇄", pdf_buf.getvalue(), "my_reading_list.pdf", "application/pdf", use_container_width=True)
    else: st.info("아직 기록이 없어요.")

with r_col:
    st.markdown("<span class='big-font'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                st.image(item['url'], use_container_width=True)
                if st.button("✅ 읽음 완료", key=f"wish_to_r_{i}"):
                    r = requests.get(item['url'])
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": item['url'],
                        "start": date.today().isoformat(), "end": date.today().isoformat(),
                        "genre": item.get('genre', '미지정')
                    })
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if st.button("🗑️ 제거", key=f"wish_del_{i}"):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()