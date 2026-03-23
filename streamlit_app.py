import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter
 
# --- 1. 기본 설정 (인쇄 규격 등) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)
 
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")
 
# --- 2. 🎨 CSS 스타일링 (입력창 테두리 제거 및 레이아웃) ---
st.markdown(f"""
   <style>
   .block-container {{ padding-top: 5rem !important; max-width: 1200px; }}
   
   .main-title {{
       font-size: 42px !important;
       font-weight: 800 !important;
       color: #31333F;
       margin-bottom: 30px !important;
       display: flex;
       align-items: center;
       gap: 15px;
   }}

   /* 🚫 모든 입력창 및 텍스트박스에서 빨간 테두리 제거 */
   input:focus, textarea:focus, select:focus, div[data-baseweb="input"], div[data-baseweb="base-input"] {{
       border-color: transparent !important;
       box-shadow: none !important;
       outline: none !important;
   }}
   
   /* 검색창 전용 스타일 */
   .stTextInput > div > div > input {{
       border: 1px solid #f0f2f6 !important;
       border-radius: 8px !important;
   }}

   button[data-baseweb="tab"] {{ font-size: 20px !important; font-weight: bold !important; }}
   div[data-baseweb="tab-highlight"] {{ background-color: #FF4B4B !important; height: 4px !important; }}

   [data-testid="stImage"] img {{ height: 220px !important; object-fit: contain !important; background-color: #f9f9f9; border-radius: 8px; }}
   div.stButton > button {{ width: 100% !important; height: 35px !important; font-size: 13px !important; }}
   </style>
   """, unsafe_allow_html=True)

# --- 3. 로그인 및 세션 관리 ---
user_query = st.query_params.get("user")

if not user_query:
    st.markdown('<div class="main-title">📖 독서 기록장</div>', unsafe_allow_html=True)
    user_id_input = st.text_input("사용자 아이디를 입력하여 시작하세요", placeholder="아이디 입력 (예: 치이카와)")
    if st.button("내 서재로 들어가기"):
        if user_id_input:
            st.query_params["user"] = user_id_input
            st.rerun()
    st.stop()

st.session_state.user_id = user_query
USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

if 'collection' not in st.session_state:
   st.session_state.collection = []; st.session_state.wishlist = []
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

# --- 4. 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 사용자: **{st.session_state.user_id}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    if st.button("🗑️ 데이터 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 5. 상단 타이틀 및 장르 통계 (복구 완료) ---
st.markdown(f'<div class="main-title">📖 {st.session_state.user_id}의 독서 기록</div>', unsafe_allow_html=True)

t_col1, t_col2 = st.columns([1, 4])
with t_col1:
   st.markdown(f"""<div style="text-align: center;"><div style="font-size: 14px; color: #666;">{datetime.now().year}년 누적</div><div style="font-size: 40px; font-weight: bold; color: #87CEEB;">{len(st.session_state.collection)}권</div></div>""", unsafe_allow_html=True)

with t_col2:
   # 🚨 장르별 통계 제목 및 항목 복구
   st.markdown("<div style='font-size: 16px; font-weight: bold; margin-bottom: 10px;'>📚 장르별 통계</div>", unsafe_allow_html=True)
   if st.session_state.collection:
       counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
       genre_items = "".join([f"<div style='background:#f8f9fa;border:1px solid #eee;border-radius:8px;padding:5px 12px;text-align:center;'><div style='font-size:11px;color:#888;'>{g}</div><div style='font-size:14px;font-weight:bold;'>{c}권</div></div>" for g, c in counts.items()])
       st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:8px;'>{genre_items}</div>", unsafe_allow_html=True)

st.divider()

# --- 6. 도서 검색 ---
st.markdown("### 🔍 도서 검색")
q = st.text_input("제목/저자 입력", key="search_input", label_visibility="collapsed", placeholder="책 제목을 입력하세요")
if q:
   res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
   imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
   genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
   if imgs:
       scols = st.columns(4)
       for i, url in enumerate(imgs[:8]):
           with scols[i % 4]:
                st.image(url, use_container_width=True)
                g_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                bc1, bc2 = st.columns(2)
                if bc1.button("📖 읽음", key=f"r_{i}"):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": g_val})
                    save_all(); st.rerun()
                if bc2.button("🩵 위시", key=f"w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": g_val}); save_all(); st.rerun()

st.divider()

# --- 7. 메인 탭 ---
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
   l_top_c1, l_top_c2 = st.columns([1, 1])
   with l_top_c1: edit_mode = st.toggle("🔧 편집 모드 활성화")
   p_idx = []
   if st.session_state.collection:
       for r in range((len(st.session_state.collection) + 3) // 4):
           dcols = st.columns(4)
           for c in range(4):
               idx = r * 4 + c
               if idx < len(st.session_state.collection):
                   itm = st.session_state.collection[idx]
                   with dcols[c]:
                       st.image(itm["img"], use_container_width=True)
                       if edit_mode:
                           if st.checkbox("선택", key=f"p_{idx}", value=True): p_idx.append(idx)
                           new_genre = st.text_input("장르", itm.get('genre', '미지정'), key=f"eg_{idx}", label_visibility="collapsed")
                           new_dr = st.date_input("날짜", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"ed_{idx}", label_visibility="collapsed")
                           eb1, eb2 = st.columns(2)
                           if eb1.button("저장", key=f"sv_{idx}"):
                               st.session_state.collection[idx].update({"genre": new_genre, "start": new_dr[0].isoformat(), "end": new_dr[1].isoformat()}); save_all(); st.rerun()
                           if eb2.button("삭제", key=f"dc_{idx}"): st.session_state.collection.pop(idx); save_all(); st.rerun()
                       else:
                           st.caption(f"장르: {itm.get('genre', '미지정')}"); st.text(f"📅 {itm.get('start', '미정')} ~ {itm.get('end', '미정')}")
       if edit_mode and p_idx:
           with l_top_c2:
               buf = io.BytesIO(); sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
               x, y = 100, 100
               for i in p_idx:
                    img = st.session_state.collection[i]["img"]; ratio = TARGET_H_PX / float(img.size[1]); img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                    if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                    sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
               sheet.save(buf, format="PDF", resolution=300.0)
               st.download_button("📥 선택 PDF 인쇄", buf.getvalue(), "books.pdf", use_container_width=True)

with tab_wish:
   st.markdown("<div style='height: 56px;'></div>", unsafe_allow_html=True)
   if st.session_state.wishlist:
       for r in range((len(st.session_state.wishlist) + 3) // 4):
           wcols = st.columns(4)
           for c in range(4):
               idx = r * 4 + c
               if idx < len(st.session_state.wishlist):
                   item = st.session_state.wishlist[idx]
                   with wcols[c]:
                        r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                        img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                        st.image(img_obj, use_container_width=True)
                        st.caption(f"장르: {item.get('genre', '미지정')}")
                        wb1, wb2 = st.columns(2)
                        if wb1.button("📖 읽음", key=f"wr_{idx}"):
                            st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                        if wb2.button("🗑️ 삭제", key=f"wd_{idx}"): st.session_state.wishlist.pop(idx); save_all(); st.rerun()