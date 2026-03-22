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

# --- 🎨 스타일 설정 (사용자 요청 사항 반영) ---
st.markdown("""
    <style>
    /* ✅ 검색창 제목 크기 확대 (밑에 목록만큼) */
    .stTextInput label p {
        font-size: 24px !important;
        font-weight: bold !important;
        margin-bottom: 15px !important;
    }
    /* 버튼 텍스트 최적화 */
    div.stButton > button p { 
        font-size: 13px !important; 
        white-space: nowrap !important; 
    }
    div.stButton > button { height: 38px !important; padding: 0px 5px !important; }
    /* 달력 날짜 숫자 스타일 */
    .cal-day-num { font-size: 12px; font-weight: bold; margin-bottom: 1px; }
    /* ✅ 달력 이모지 스타일 (날짜 바로 밑에 딱 붙게) */
    .cal-book-emoji { font-size: 18px; text-align: center; margin-top: -3px; }
    </style>
    """, unsafe_allow_html=True)

# ✅ 최상단 타이틀 복구
st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)

# --- 📊 대시보드 (디자인 개편) ---
# 빈 공간 없이 알차게 배치하기 위해 컬럼 비율 조정
t_col1, t_col2 = st.columns([1, 2.5])
with t_col1:
    # ✅ 누적 독서 카드 슬림화 (배경색 제거, 크기 축소)
    st.markdown(f"""<div style="text-align:center; padding: 10px; border-bottom: 2px solid #ddd; margin-bottom: 20px;">
        <h3 style="margin-bottom:0; color: #333;">{datetime.now().year}년 누적 독서</h3>
        <h1 style="color:#87CEEB; font-size:55px; margin-top:5px; margin-bottom: 0;">{len(st.session_state.collection)}권</h1>
    </div>""", unsafe_allow_html=True)
    
    # 누적 독서 카드 아래 빈 공간에 넣으면 좋은 '최근 읽은 책' 미니 목록
    st.caption("✨ 최근 추가된 기록")
    if st.session_state.collection:
        latest = st.session_state.collection[-3:]
        for itm in latest:
            st.write(f"- {itm['start']}에 독서 시작")

with t_col2:
    # ✅ 달력 컨트롤 (버튼 위치 이동: 이전은 왼쪽, 다음은 오른쪽)
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    # 이전 달 버튼 (왼쪽 끝)
    if mc1.button("◀ 이전 달", use_container_width=True):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1; st.rerun()
    # 연월 제목 (중앙)
    mc2.markdown(f"<h3 style='text-align:center; margin-top: 0;'>📅 {st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
    # 다음 달 버튼 (오른쪽 끝)
    if mc3.button("다음 달 ▶", use_container_width=True):
        if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        else: st.session_state.cal_month += 1; st.rerun()
    
    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    w_cols = st.columns(7)
    for i, dname in enumerate(["일", "월", "화", "수", "목", "금", "토"]): w_cols[i].caption(dname)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                curr = date(st.session_state.cal_year, st.session_state.cal_month, day).isoformat()
                with cols[i]:
                    # 날짜 숫자
                    st.markdown(f"<div class='cal-day-num'>{day}</div>", unsafe_allow_html=True)
                    # ✅ 해당 날짜에 읽은 책이 있으면 이모지를 날짜 바로 밑에 딱 붙여서 표시
                    for b in st.session_state.collection:
                        if b["start"] <= curr <= b["end"]: 
                            st.markdown("<div class='cal-book-emoji'>📖</div>", unsafe_allow_html=True)

st.divider()

# --- 🔍 ✅ 검색 섹션 (글씨 크기 확대 반영) ---
# 스타일 시트에서 label 크기를 키웠으므로, text_input을 그대로 사용
query = st.text_input("📖 책 제목 입력", placeholder="예: 먼작귀", key="search_input")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=10)
        # 이미지 URL 추출 패턴 보강 (엑박 방지)
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
    # 읽은 책 모음 제목 크기는 이전과 동일
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
        dcols = st.columns(4)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                # 날짜 수정 기능도 유지
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