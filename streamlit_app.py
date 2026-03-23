import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- 기본 설정 (박제) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# ==========================================
# 🎨 스타일 (탭 디자인 + 수평 정렬 강제)
# ==========================================
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; max-width: 1200px; }}
    
    /* 1. 탭(Tab) 디자인: 폰트 키우고 볼드 처리, 선택 시 하단 바 강조 */
    button[data-baseweb="tab"] {{
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #1E1E1E !important;
        padding: 12px 30px !important;
    }}
    
    /* 선택된 탭 하단 막대기 (길고 여유롭게) */
    div[data-baseweb="tab-highlight"] {{
        background-color: #FF4B4B !important; 
        height: 5px !important;
        border-radius: 10px !important;
    }}

    /* 2. 버튼 수평 정렬 강제 (Flexbox 사용) */
    div[data-testid="column"] {{
        display: flex !important;
        flex-direction: column !important;
    }}
    
    div[data-testid="stHorizontalBlock"] {{
        gap: 8px !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }}

    /* 버튼 스타일 통일 */
    div.stButton > button {{
        width: 100% !important;
        height: 38px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 0px !important;
    }}

    /* 삭제 버튼 전용 (빨간 테두리) */
    .del-btn button {{
        border: 1px solid #FF6B6B !important;
        color: #FF6B6B !important;
        background-color: white !important;
    }}

    /* 책 이미지 세로 길이 고정 (200px) */
    [data-testid="stImage"] img {{
        height: 200px !important;
        object-fit: contain !important;
        background-color: #f9f9f9;
        border-radius: 10px;
        border: 1px solid #eee;
    }}

    /* 타이틀 및 통계 스타일 */
    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin-bottom: 12px; display: block; color: #31333F; }}
    .stat-container {{ text-align: center; }}
    .genre-card {{ background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 5px 12px; min-width: 60px; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "치이카와")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로직 ---
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
    data = {"wishlist": st.session_state.wishlist,
            "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]}
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- 상단 레이아웃 ---
st.title(f"📖 {st.session_state.user_id}의 독서 기록")
st.write(""); st.write("")

t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    st.markdown(f"<div class='stat-container'><div style='font-size: 14px; color: #666;'>{datetime.now().year}년 누적</div><div style='font-size: 40px; font-weight: bold; color: #87CEEB;'>✨{len(st.session_state.collection)}권✨</div></div>", unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items = "".join([f"<div class='genre-card'><div class='genre-label'>{g}</div><div class='genre-value'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:10px;'>{genre_items}</div>", unsafe_allow_html=True)
    else: st.caption("기록이 없습니다.")

st.divider()

# --- 검색 섹션 ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력창", placeholder="제목/저자 입력...", label_visibility="collapsed")
if q:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    genre_raw = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                g_val = genre_raw[i] if i < len(genre_raw) else "미지정"
                sel_genre = st.text_input("장르", value=g_val, key=f"sg_{i}", label_visibility="collapsed")
                
                # 버튼 수평 정렬
                b_cols = st.columns(2)
                with b_cols[0]:
                    if st.button("📖 읽음", key=f"r_{i}"):
                        img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                        st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                        save_all(); st.rerun()
                with b_cols[1]:
                    if st.button("🩵 위시", key=f"w_{i}"):
                        st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

# --- 하단 탭 영역 (핵심 수정) ---
tab_lib, tab_wish = st.tabs(["내 서재", "위시리스트"])

with tab_lib:
    if st.session_state.collection:
        del_m = st.toggle("편집/삭제 모드")
        p_idx = []
        dcols = st.columns(4) # 4열로 확장
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 4]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄", key=f"p_{idx}", value=True): p_idx.append(idx)
                
                if del_m:
                    new_g = st.text_input("장르", itm.get('genre', '미지정'), key=f"eg_{idx}", label_visibility="collapsed")
                    # 날짜와 수정/삭제 버튼 수평 정렬
                    try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                    except: val = [date.today(), date.today()]
                    new_dr = st.date_input("날짜", val, key=f"ed_{idx}", label_visibility="collapsed")
                    
                    b_edit_cols = st.columns([2, 1])
                    with b_edit_cols[0]:
                        if st.button("수정", key=f"sv_{idx}"):
                            st.session_state.collection[idx]["genre"] = new_g
                            if len(new_dr) == 2:
                                st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                            save_all(); st.rerun()
                    with b_edit_cols[1]:
                        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                        if st.button("❌", key=f"dc_{idx}"):
                            st.session_state.collection.pop(idx); save_all(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{itm.get('genre', '미지정')}**")
                    st.caption(f"{itm['end']}")
        
        if p_idx:
            # PDF 생성 로직 (생략 없음)
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 100, 100
            for i in p_idx:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 100: x = 100; y += TARGET_H_PX + 40
                sheet.paste(img_res, (x, y)); x += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 {len(p_idx)}권 PDF 저장", buf.getvalue(), "books.pdf")
    else: st.info("서재가 비어있습니다.")

with tab_wish:
    if st.session_state.wishlist:
        wcols = st.columns(4)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 4]:
                r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(item.get('genre', '미지정'))
                
                # 수평 정렬
                wb_cols = st.columns(2)
                with wb_cols[0]:
                    if st.button("✅읽음", key=f"wr_{i}"):
                        st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                with wb_cols[1]:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"w_d_{i}"):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else: st.info("위시리스트가 비어있습니다.")