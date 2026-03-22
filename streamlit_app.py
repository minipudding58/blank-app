import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
import calendar

# --- 기초 규격 설정 ---
DPI = 300
TARGET_H_PX = int((35 / 25.4) * DPI)
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
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
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
                            "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist,
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"]} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🎨 스타일 설정 (검색창 크기 및 볼드 반영) ---
st.markdown("""
    <style>
    /* ✅ 검색창 제목 스타일 (볼드, 크기 확대) */
    .search-label {
        font-size: 20px !important;
        font-weight: bold !important;
        margin-bottom: 10px;
    }
    /* 버튼 텍스트 최적화 */
    div.stButton > button p { 
        font-size: 13px !important; 
        white-space: nowrap !important; 
    }
    div.stButton > button { height: 38px !important; padding: 0px 5px !important; }
    /* 달력 이모지 스타일 */
    .cal-book-emoji { font-size: 18px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 사이드바 ---
with st.sidebar:
    st.write(f"👤 접속 중: **{st.session_state.user_id}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear(); st.session_state.clear(); st.rerun()
    st.write("---")
    if st.button("🔥 데이터 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear(); st.session_state.clear(); st.rerun()

# ✅ 최상단 타이틀 복구
st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)

# --- 📊 대시보드 (통계 & 개편된 달력) ---
t_col1, t_col2 = st.columns([1, 2])
with t_col1:
    st.markdown(f"""<div style="background-color:#f8f9fa; padding:20px; border-radius:15px; text-align:center; border:1px solid #ddd; margin-top:10px;">
        <h3 style="margin-bottom:0;">{datetime.now().year}년 누적 독서</h3>
        <h1 style="color:#87CEEB; font-size:60px; margin-top:10px;">{len(st.session_state.collection)}권</h1>
    </div>""", unsafe_allow_html=True)

with t_col2:
    # 달력 컨트롤
    prev_col, next_col = st.columns([1, 1])
    if prev_col.button("◀ 이전 달"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1; st.rerun()
    if next_col.button("다음 달 ▶"):
        if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        else: st.session_state.cal_month += 1; st.rerun()
    
    # ✅ 이모지 독서 달력 (디자인 전면 개편)
    year, month = st.session_state.cal_year, st.session_state.cal_month
    st.markdown(f"<h3 style='text-align:center;'>📅 {year}년 {month}월</h3>", unsafe_allow_html=True)
    cal = calendar.monthcalendar(year, month)
    
    w_cols = st.columns(7)
    for i, dname in enumerate(["일", "월", "화", "수", "목", "금", "토"]): w_cols[i].caption(dname)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                curr = date(year, month, day).isoformat()
                # 해당 날짜에 읽은 책이 있는지 확인
                is_reading = any(b.get("start") <= curr <= b.get("end") for b in st.session_state.collection if b.get("start") and b.get("end"))
                
                with cols[i]:
                    st.write(f"**{day}**")
                    if is_reading:
                        # 책 표지 대신 📖 이모지 표시
                        st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 ✅ 검색 섹션 (디자인 업그레이드) ---
# 글씨 크기 키우고 볼드체 적용
st.markdown("<p class='search-label'>📖 책 제목 입력</p>", unsafe_allow_html=True)
query = st.text_input("제목을 입력하고 Enter!", placeholder="예: 먼작귀", label_visibility="collapsed")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        # 이미지 URL 추출 패턴 보강 (먼작귀 3권 등 엑박 방지)
        raw_imgs = re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover\d*[^"\'\s>]+', res.text)
        imgs = list(dict.fromkeys([url for url in raw_imgs if 'cover' in url]))

        if imgs:
            scols = st.columns(4)
            for i, url in enumerate(imgs[:4]):
                with scols[i]:
                    st.image(url, use_container_width=True)
                    # 읽은 기간 설정
                    dr = st.date_input("읽은 기간", [date.today(), date.today()], key=f"dr_{i}")
                    c1, c2 = st.columns(2)
                    if c1.button("📖 읽음", key=f"r_{i}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(requests.get(url, headers=headers).content)).convert("RGB"), "url": url,
                            "start": dr[0].isoformat(), "end": dr[1].isoformat() if len(dr)>1 else dr[0].isoformat()
                        })
                        save_all(); st.rerun()
                    if c2.button("🩵 위시", key=f"w_{i}", use_container_width=True):
                        if not any(d['url'] == url for d in st.session_state.wishlist):
                            st.session_state.wishlist.append({"url": url}); save_all(); st.rerun()
    except Exception as e: st.error(f"검색 결과를 가져오는 중 문제가 발생했습니다.")

st.divider()

# --- 🖨️ 하단: 목록 & PDF 인쇄 ---
left_col, right_col = st.columns(2)

with left_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        b1, b2, b3 = st.columns([1, 1, 1.5])
        if b1.button("🗑️ 전체 비우기", use_container_width=True): st.session_state.collection = []; save_all(); st.rerun()
        del_m = b2.toggle("개별 삭제 모드")
        
        # ✅ PDF 다운로드 버튼 복구
        with b3:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for itm in st.session_state.collection:
                ratio = TARGET_H_PX / float(itm['img'].size[1])
                img_res = itm['img'].resize((int(itm['img'].size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                if y + TARGET_H_PX > A4_H_PX - 100: break # 일단 1페이지만
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            
            pdf_buf = io.BytesIO(); sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button("📥 A4 인쇄 미리보기 (PDF)", pdf_buf.getvalue(), f"{st.session_state.user_id}_books.pdf", "application/pdf", use_container_width=True)
            
        st.write("---")
        # ✅ 목록 내 날짜 수정 기능
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                # 날짜 직접 수정
                new_dr = st.date_input("기간 수정", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"edit_dr_{idx}")
                if len(new_dr) == 2:
                    if itm["start"] != new_dr[0].isoformat() or itm["end"] != new_dr[1].isoformat():
                        st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                        st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                        save_all(); st.rerun()
                
                if del_m and st.button("❌", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
    else: st.info("기록이 없습니다.")

with right_col:
    st.header("🩵 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                with st.container(border=True):
                    st.image(item['url'], use_container_width=True)
                    ic1, ic2 = st.columns(2)
                    # ✅ 위시리스트 '✅ 선택' 버튼 복구 및 '읽은 책 모음' 이동
                    if ic1.button("✅ 선택", key=f"sel_w_{i}", use_container_width=True):
                        r = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"})
                        img_obj = Image.open(io.BytesIO(r.content)).convert("RGB")
                        st.session_state.collection.append({
                            "img": img_obj, "url": item['url'],
                            "start": date.today().isoformat(), "end": date.today().isoformat()
                        })
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if ic2.button("🗑️ 삭제", key=f"dw_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
    else: st.write("위시리스트가 비어있습니다.")