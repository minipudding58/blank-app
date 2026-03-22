import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
import calendar

# --- 📏 규격 및 설정 ---
DPI = 300
TARGET_H_PX = int((35 / 25.4) * DPI)
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🔗 로그인 및 데이터 관리 ---
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
                    r = requests.get(itm["url"], timeout=5)
                    if r.status_code == 200:
                        st.session_state.collection.append({
                            "img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": itm["url"],
                            "start": itm.get("start"), "end": itm.get("end")
                        })
        except: pass

def save_all():
    data = {"wishlist": st.session_state.wishlist, "collection": [{"url": i["url"], "start": i["start"], "end": i["end"]} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🎨 스타일 설정 ---
st.markdown("""
    <style>
    div.stButton > button { white-space: nowrap !important; padding: 0px 10px !important; font-size: 13px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 사이드바 ---
with st.sidebar:
    st.write(f"👤 **{st.session_state.user_id}** 님")
    if st.button("🚪 로그아웃", use_container_width=True): st.session_state.clear(); st.rerun()
    st.write("---")
    if st.button("🔥 데이터 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.clear(); st.rerun()

# --- 📊 상단 대시보드 ---
t_col1, t_col2 = st.columns([1, 2.5])
with t_col1:
    # ✨ 이모지 추가 반영
    st.markdown(f"""<div style="background-color:#f8f9fa; padding:20px; border-radius:15px; text-align:center; border:1px solid #ddd;">
        <h3 style="margin-bottom:0;">{datetime.now().year}년 누적 독서</h3>
        <h1 style="color:#87CEEB; font-size:50px; margin-top:10px;">✨{len(st.session_state.collection)}권✨</h1>
    </div>""", unsafe_allow_html=True)

with t_col2:
    mc1, mc2, mc3 = st.columns([1, 2, 1])
    if mc1.button("◀ 이전"):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    mc2.markdown(f"<h4 style='text-align:center;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</h4>", unsafe_allow_html=True)
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
                    st.markdown(f"<div style='font-size:11px; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)
                    for b in st.session_state.collection:
                        if b["start"] <= curr <= b["end"]: st.image(b["url"], use_container_width=True)

st.divider()

# --- 🔍 검색 섹션 생략 (이전과 동일) ---
query = st.text_input("책 제목 입력", placeholder="예: 먼작귀")
if query:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}", headers={"User-Agent":"Mozilla/5.0"})
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover\d*[^"\'\s>]+', res.text)))
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                dr = st.date_input("기간", [date.today(), date.today()], key=f"search_dr_{i}")
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_{i}", use_container_width=True):
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(requests.get(url).content)).convert("RGB"), "url": url, "start": dr[0].isoformat(), "end": dr[1].isoformat() if len(dr)>1 else dr[0].isoformat()})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_{i}", use_container_width=True):
                    st.session_state.wishlist.append({"url": url}); save_all(); st.rerun()

st.divider()

# --- 📚 읽은 책 목록 & 선택 인쇄 기능 ---
l_col, r_col = st.columns(2)
with l_col:
    st.header("📖 읽은 책 모음")
    if st.session_state.collection:
        # 상단 제어 바
        ctrl_c1, ctrl_c2 = st.columns([1, 2])
        if ctrl_c1.button("🗑️ 전체 비우기"): st.session_state.collection = []; save_all(); st.rerun()
        del_m = ctrl_c2.toggle("개별 삭제 모드")

        # 인쇄할 책 선택 리스트 생성
        selected_indices = []
        st.write("📄 **인쇄할 책을 선택해 주세요:**")
        
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                # 인쇄 선택 체크박스
                if st.checkbox("인쇄 선택", key=f"sel_print_{idx}", value=True):
                    selected_indices.append(idx)
                
                # 날짜 수정
                new_dr = st.date_input("수정", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"edit_dr_{idx}")
                if len(new_dr) == 2:
                    if itm["start"] != new_dr[0].isoformat() or itm["end"] != new_dr[1].isoformat():
                        st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                        st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                        save_all(); st.rerun()
                
                if del_m and st.button("❌ 삭제", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
        
        st.write("---")
        # 선택된 책들로만 PDF 생성 로직
        if selected_indices:
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for idx in selected_indices:
                itm = st.session_state.collection[idx]
                ratio = TARGET_H_PX / float(itm['img'].size[1])
                img_res = itm['img'].resize((int(itm['img'].size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                if y + TARGET_H_PX > A4_H_PX - 100: break 
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            
            pdf_buf = io.BytesIO(); sheet.save(pdf_buf, format="PDF", resolution=300.0)
            st.download_button(
                f"📥 선택한 {len(selected_indices)}권 PDF 다운로드", 
                pdf_buf.getvalue(), "my_reading_record.pdf", "application/pdf", 
                use_container_width=True
            )
        else:
            st.warning("인쇄할 책을 하나 이상 선택해 주세요.")

with r_col:
    st.header("🩵 위시리스트")
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                st.image(item['url'], use_container_width=True)
                wc1, wc2 = st.columns(2)
                if wc1.button("✅ 선택", key=f"sel_{i}", use_container_width=True):
                    r = requests.get(item['url'])
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(r.content)).convert("RGB"), "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat()})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if wc2.button("🗑️ 삭제", key=f"dw_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()