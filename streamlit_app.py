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

# --- 🎨 스타일 (장르 칸을 아주 슬림하게!) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* 누적 독서 영역 (테두리 없음) */
    .stat-container {{ text-align: center; }}

    /* ✅ 장르 카드 가로폭 줄이기 핵심 */
    .genre-wrapper {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 5px 12px;
        min-width: 60px; /* 가로폭을 확 줄임 */
        max-width: 100px;
        text-align: center;
    }}
    .genre-label {{ font-size: 12px; color: #888; }}
    .genre-value {{ font-size: 16px; font-weight: bold; color: #333; }}

    .section-title {{ font-size: 18px !important; font-weight: bold !important; margin-bottom: 10px; display: block; }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "치이카와")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로드 기능 ---
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
    st.markdown(f"""
        <div class="stat-container">
            <div style="font-size: 14px; color: #666;">{datetime.now().year}년 누적</div>
            <div style="font-size: 40px; font-weight: bold; color: #87CEEB;">✨{len(st.session_state.collection)}권✨</div>
        </div>
    """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        # ✅ HTML 코드가 노출되지 않도록 f-string과 구조를 정밀하게 짰습니다.
        genre_items = "".join([f"<div class='genre-card'><div class='genre-label'>{g}</div><div class='genre-value'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-wrapper'>{genre_items}</div>", unsafe_allow_html=True)
    else:
        st.caption("기록이 없습니다.")

st.divider()

# --- 검색/추가 및 리스트 관리 (기존 모든 기능 포함) ---
q = st.text_input("🔍 책 검색", placeholder="제목/저자 입력", label_visibility="collapsed")
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
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_{i}"):
                    img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_data)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_genre}); save_all(); st.rerun()

st.divider()

l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        p_idx = []
        del_m = st.toggle("삭제 모드")
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄", key=f"p_{idx}", value=True): p_idx.append(idx)
                st.caption(f"{itm.get('genre', '미지정')}")
                try: val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: val = [date.today(), date.today()]
                new_dr = st.date_input("날짜", val, key=f"ed_{idx}", label_visibility="collapsed")
                if st.button("수정", key=f"sv_{idx}"):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_dr[0].isoformat(), new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and st.button("❌", key=f"dc_{idx}"):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()

        if p_idx:
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

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                r_img = requests.get(item['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(item.get('genre', '미지정'))
                if st.button("✅ 읽음", key=f"wr_{i}"):
                    st.session_state.collection.append({"img": img_obj, "url": item['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": item.get('genre', '미지정')})
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()