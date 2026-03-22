import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date, timedelta
import calendar
from collections import Counter

# --- 기초 규격 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) # 목록용 세로 길이 고정
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🔗 로그인 및 데이터 로드 ---
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
    # 에러 방지용 세션 초기화
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
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🎨 스타일 설정 (모든 네모 칸 넉넉하게 및 이모지 밀착) ---
st.markdown("""
    <style>
    /* 폰트 크기 일치 */
    .stTextInput label p, .stDateInput label p {
        font-size: 20px !important;
        font-weight: bold !important;
        margin-bottom: 10px !important;
    }
    /* ✅ 모든 버튼/입력창 네모 칸 넉넉하게 및 정렬 */
    div.stButton > button, div.stDownloadButton > button {
        width: 100% !important;
        height: 45px !important; /* 높이 넉넉하게 */
        font-size: 14px !important;
        text-align: center;
        border-radius: 5px;
        white-space: nowrap; /* 줄바꿈 방지 */
    }
    .stDateInput div[data-baseweb="input"] {
        height: 45px !important; /* 높이 넉넉하게 */
        font-size: 14px !important;
        border-radius: 5px;
    }
    /* ✅ 달력 세로 길이 축소 및 이모지 밀착 */
    .cal-box { text-align: center; line-height: 1; margin-bottom: 0px;}
    .cal-day-num { font-size: 12px; font-weight: bold; margin-bottom: -5px; }
    .cal-book-emoji { font-size: 18px; margin-top: -3px; }
    </style>
    """, unsafe_allow_html=True)

# 최상단 타이틀 복구
st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)
st.divider()

# --- 📊 상단 섹션 (누적독서 & 달력 비율 조정) ---
top_c1, top_c2 = st.columns([1, 1])
with top_c1:
    # 누적 독서 (배경색 없음, ✨ 추가)
    st.markdown(f"<div style='text-align:center; padding: 20px;'><h3>{datetime.now().year}년 누적 독서</h3><h1 style='color:#87CEEB; font-size:60px;'>✨{len(st.session_state.collection)}권✨</h1></div>", unsafe_allow_html=True)
    st.divider()
    # 장르별 통계 (예시 제거)
    st.caption("📚 장르별 독서 현황")
    if st.session_state.collection:
        genres = [itm.get("genre", "미지정") for itm in st.session_state.collection]
        counts = Counter(genres)
        st.write(f"**" + ", ".join([f"{g} {c}권" for g, c in counts.items()]) + "**")

with top_c2:
    # 달력 컨트롤 (연월 제목과 같은 열)
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전 달", use_container_width=True):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1; st.rerun()
    mc2.markdown(f"<h3 style='text-align:center; margin:0;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
    if mc3.button("다음 달 ▶", use_container_width=True):
        if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        else: st.session_state.cal_month += 1; st.rerun()
    
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    w_cols = st.columns(7)
    for i, dname in enumerate(["일", "월", "화", "수", "목", "금", "토"]): w_cols[i].caption(dname)
    
    # ✅ 달력 세로 높이 축소 (cite: KakaoTalk_20260322_235849172.jpg)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                curr = date(st.session_state.cal_year, st.session_state.cal_month, day).isoformat()
                with cols[i]:
                    # 숫자 바로 밑에 이모지 밀착
                    is_reading = False
                    for b in st.session_state.collection:
                        if b["start"] <= curr <= b["end"]: is_reading = True; break
                    st.markdown(f"<div class='cal-box'><div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    if is_reading: st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 검색 섹션 (장르 연동 강화) ---
# 책 제목 입력 폰트 크기 확대
st.markdown("<p style='font-size:24px; font-weight:bold;'>📖 책 제목 입력</p>", unsafe_allow_html=True)
query = st.text_input("제목 입력", label_visibility="collapsed", placeholder="예: 먼작귀", key="search_input")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    # 엑박 방지 이미지 추출
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # ✅ 장르 추출 로직 강화
    genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)

    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                genre_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                # ✅ 검색창에서는 날짜 입력을 빼고 장르만 확인
                sel_genre = st.text_input("장르", value=genre_val, key=f"src_g_{i}")
                
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_{i}", use_container_width=True):
                    # 목록 추가 시 기본 날짜로 저장
                    st.session_state.collection.append({
                        "img": Image.open(io.BytesIO(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content)).convert("RGB"), "url": url,
                        "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                    })
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_{i}", use_container_width=True):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 📚 목록 섹션 (날짜 가독성, 버튼 크기 및 시작 높이 정렬) ---
l_col, r_col = st.columns(2)

# ✅ 읽은 책 모음과 위시리스트의 시작 높이 맞춤 (공백 활용)
with l_col:
    st.markdown("<p style='font-size:24px; font-weight:bold;'>📖 읽은 책 모음</p>", unsafe_allow_width=True)
    if st.session_state.collection:
        print_Indices = []
        # ✅ 관리 버튼 일렬 정렬 완벽 복구
        ctrl_c1, ctrl_c2 = st.columns([1, 2])
        if ctrl_c1.button("🗑️ 전체 비우기"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = ctrl_c2.toggle("개별 삭제 모드")
        
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                # ✅ 세로 길이 통일
                sheet = Image.new('RGB', (itm["img"].size[0], TARGET_H_PX), (255, 255, 255))
                st.image(itm["img"], use_container_width=True)
                # 인쇄 선택 체크박스 유지
                if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): print_Indices.append(idx)
                
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                # ✅ 날짜 안 잘리게 넉넉한 입력창
                st.write("읽은 기간")
                # 회색 날짜 입력창 하나로 통합 (확인/수정 동시 가능) (cite: image_c0b247.png)
                new_dr = st.date_input("수정", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"e_d_{idx}", label_visibility="collapsed")
                
                # ✅ 넉넉한 수정 버튼 옆으로
                date_c1, date_c2 = st.columns([1, 1])
                with date_c1:
                    if st.button("수정", key=f"sv_{idx}", use_container_width=True):
                        if len(new_dr) == 2:
                            st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                            st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                            save_all(); st.rerun()
                with date_c2:
                    if del_m and st.button("❌", key=f"dc_{idx}", use_container_width=True):
                        st.session_state.collection.pop(idx); save_all(); st.rerun()
                st.write("---")

        if print_Indices:
            # 선택 인쇄용 PDF 생성 로직
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x_pos, y_pos = 100, 100
            for i in print_Indices:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x_pos + img_res.size[0] > A4_W_PX - 100: x_pos = 100; y_pos += TARGET_H_PX + 40
                if y_pos + TARGET_H_PX > A4_H_PX - 100: break
                sheet.paste(img_res, (x_pos, y_pos)); x_pos += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            # 인쇄 버튼도 넉넉하게
            st.download_button(f"📥 선택 {len(print_Indices)}권 PDF 인쇄", buf.getvalue(), "my_record.pdf", use_container_width=True)

with r_col:
    st.markdown("<p style='font-size:24px; font-weight:bold;'>🩵 위시리스트</p>", unsafe_allow_width=True)
    if st.session_state.wishlist:
        # ✅ 시작 높이 맞춤 (공백 추가)
        st.write("") # 공백 추가
        st.write("") # 공백 추가
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                with st.container(border=True):
                    # ✅ 세로 길이 고정 및 정렬
                    img = Image.open(io.BytesIO(requests.get(item['url']).content)).convert("RGB")
                    # y축 고정
                    ratio = TARGET_H_PX / float(img.size[1])
                    img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                    st.image(img, use_container_width=True)
                    st.caption(f"장르: {item.get('genre', '미지정')}")
                    # ✅ 버튼 디자인 및 정렬 완벽 복구
                    c1, c2 = st.columns(2)
                    if c1.button("✅ 선택", key=f"wr_{i}"):
                        st.session_state.collection.append({
                            "img": img, "url": item['url'], 
                            "start": date.today().isoformat(), "end": date.today().isoformat(), 
                            "genre": item.get('genre', '미지정')
                        })
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if c2.button("🗑️ 삭제", key=f"wd_{i}"):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()