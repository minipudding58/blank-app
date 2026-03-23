import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter
 
# --- 기본 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)
 
st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")
 
# --- 🎨 스타일 레이아웃 (공백 및 빨간 테두리 제거) ---
st.markdown(f"""
   <style>
   .block-container {{ padding-top: 1rem !important; }}
    
   button[data-baseweb="tab"] {{
       font-size: 20px !important;
       font-weight: bold !important;
       color: #31333F !important;
   }}
   
   div[data-baseweb="tab-highlight"] {{
       background-color: #FF4B4B !important; 
       height: 4px !important;
   }}

   /* 🚨 모든 입력창에서 빨간 테두리 제거 */
   input:focus, textarea:focus, select:focus, div[data-baseweb="input"] {{
       border-color: #eeeeee !important;
       box-shadow: none !important;
       outline: none !important;
   }}
   div[data-baseweb="input"] > div:focus-within {{
       border-color: #d3d3d3 !important;
       box-shadow: none !important;
   }}

   [data-testid="stImage"] img {{
       height: 220px !important;
       object-fit: contain !important;
       background-color: #f9f9f9;
       border-radius: 8px;
       margin-bottom: 8px;
   }}
 
   div.stButton > button {{
       width: 100% !important;
       height: 35px !important;
       font-size: 13px !important;
       margin-top: 0px !important;
   }}

   /* 편집 버튼 위치 및 간격 조정 */
   .stToggle {{
       margin-top: -10px !important;
       margin-bottom: 5px !important;
   }}

   .stat-container {{ text-align: center; }}
   .genre-wrapper {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-end; }}
   .genre-card {{
       background-color: #f8f9fa;
       border: 1px solid #eee;
       border-radius: 8px;
       padding: 4px 10px;
       text-align: center;
   }}
   </style>
   """, unsafe_allow_html=True)

# --- 데이터 관리 ---
if 'user_id' not in st.session_state:
   st.session_state.user_id = st.query_params.get("user", "치이카와")
 
USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

with st.sidebar:
    st.markdown(f"### 👤 현재 사용자: **{st.session_state.user_id}**")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    if st.button("🗑️ 데이터 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE): os.remove(USER_DATA_FILE)
        st.session_state.collection = []; st.session_state.wishlist = []
        st.rerun()

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
 
# --- 상단 레이아웃 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
 
t_col1, t_col2 = st.columns([1, 4])
with t_col1:
   st.markdown(f"""<div class="stat-container"><div style="font-size: 14px; color: #666;">{datetime.now().year}년 누적</div><div style="font-size: 40px; font-weight: bold; color: #87CEEB;">{len(st.session_state.collection)}권</div></div>""", unsafe_allow_html=True)
with t_col2:
   if st.session_state.collection:
       counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
       genre_items = "".join([f"<div class='genre-card'><div style='font-size:11px;color:#888;'>{g}</div><div style='font-size:14px;font-weight:bold;'>{c}권</div></div>" for g, c in counts.items()])
       st.markdown(f"""<div style='font-size: 14px; font-weight: bold; color: #333; margin-bottom: 5px;'>📚 장르별 통계</div><div class='genre-wrapper'>{genre_items}</div>""", unsafe_allow_html=True)
 
st.divider()
 
# --- 검색 (버튼 수평 배치 및 텍스트 수정) ---
st.markdown("### 🔍 새로운 도서 검색")
q = st.text_input("제목/저자 입력", key="search_input", label_visibility="collapsed")
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
                
                # 🚨 읽음/위시 버튼 수평 배치
                b_col1, b_col2 = st.columns(2)
                if b_col1.button("📖 읽음", key=f"r_{i}"):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": g_val})
                    save_all(); st.rerun()
                if b_col2.button("🩵 위시", key=f"w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": g_val}); save_all(); st.rerun()
 
st.divider()
 
# --- 탭 영역 ---
tab_lib, tab_wish = st.tabs(["📚 내 서재", "🩵 위시리스트"])

with tab_lib:
   if st.session_state.collection:
       edit_mode = st.toggle("🔧 편집 모드 활성화")
       p_idx = []
       rows = (len(st.session_state.collection) + 3) // 4
       for r in range(rows):
           dcols = st.columns(4)
           for c in range(4):
               idx = r * 4 + c
               if idx < len(st.session_state.collection):
                   itm = st.session_state.collection[idx]
                   with dcols[c]:
                       st.image(itm["img"], use_container_width=True)
                       if edit_mode:
                           # 🚨 1. 선택 (무조건 위!)
                           if st.checkbox("선택", key=f"p_{idx}", value=True): p_idx.append(idx)
                           
                           # 🚨 2. 장르 수정 (아래)
                           new_genre = st.text_input("장르 수정", value=itm.get('genre', '미지정'), key=f"edit_g_{idx}", label_visibility="collapsed")
                           
                           try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                           except: val = [date.today(), date.today()]
                           new_dr = st.date_input("날짜", val, key=f"ed_{idx}", label_visibility="collapsed")
                           
                           eb_cols = st.columns(2)
                           if eb_cols[0].button("저장", key=f"sv_{idx}"):
                               if len(new_dr) == 2:
                                   st.session_state.collection[idx]["genre"] = new_genre
                                   st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                                   save_all(); st.rerun()
                           if eb_cols[1].button("삭제", key=f"dc_{idx}"):
                               st.session_state.collection.pop(idx); save_all(); st.rerun()
                       else:
                           st.caption(f"장르: {itm.get('genre', '미지정')}")
                           st.text(f"📅 {itm.get('start', '미정')} ~ {itm.get('end', '미정')}")
 
       if edit_mode and p_idx:
           buf = io.BytesIO()
           sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
           x, y = 100, 100
           for i in p_idx:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
           sheet.save(buf, format="PDF", resolution=300.0)
           st.download_button(f"📥 선택 PDF 인쇄", buf.getvalue(), "my_books.pdf", use_container_width=True)

with tab_wish:
   if st.session_state.wishlist:
       wish_edit = st.toggle("🔧 위시 편집 모드")
       # 🚨 위시리스트 공백 복구
       st.markdown("<br>", unsafe_allow_html=True) 
       
       rows_w = (len(st.session_state.wishlist) + 3) // 4
       for r in range(rows_w):
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
                        wb_cols = st.columns(2)
                        if wb_cols[0].button("📖 읽음", key=f"wr_{idx}"): 
                            st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()
                        if wb_cols[1].button("🗑️ 삭제", key=f"w_d_{idx}"):
                            st.session_state.wishlist.pop(idx); save_all(); st.rerun()