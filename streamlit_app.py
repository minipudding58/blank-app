import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- 기초 규격 설정 ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 스타일 설정 (여백 압축 및 장르 칸 슬림화) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1rem !important; padding-bottom: 0rem !important; }}
    
    /* 누적 독서 영역 (테두리 없음) */
    .stat-container {{ text-align: center; padding: 5px; }}

    /* ✅ 장르 카드 슬림화 핵심 로직 */
    .genre-wrapper {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 5px;
    }}
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 6px;
        padding: 4px 10px;
        /* 가로폭을 아주 작게 제한 */
        min-width: 60px; 
        max-width: 100px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .genre-name {{ font-size: 11px; color: #888; line-height: 1.2; }}
    .genre-val {{ font-size: 15px; font-weight: bold; color: #333; line-height: 1.2; }}

    .section-title {{ font-size: 19px !important; font-weight: bold !important; display: block; margin-bottom: 8px; }}
    
    /* 버튼 규격 */
    div.stButton > button, div.stDownloadButton > button {{ width: 100% !important; height: 42px !important; }}
    </style>
    """, unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "User")

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 데이터 로드 로직 ---
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

t_col1, t_col2 = st.columns([1, 3.5])

with t_col1:
    st.markdown(f"""
        <div class="stat-container">
            <span style='font-size: 15px; color: #666;'>{datetime.now().year}년 누적</span><br>
            <span style='color:#87CEEB; font-size:45px; font-weight:bold;'>✨{len(st.session_state.collection)}권✨</span>
        </div>
    """, unsafe_allow_html=True)

with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        # ✅ 슬림한 카드형태로 출력
        g_html = "<div class='genre-wrapper'>"
        for g_name, g_count in counts.items():
            g_html += f"""
                <div class='genre-card'>
                    <div class='genre-name'>{g_name}</div>
                    <div class='genre-val'>{g_count}권</div>
                </div>
            """
        g_html += "</div>"
        st.markdown(g_html, unsafe_allow_html=True)
    else:
        st.caption("기록된 도서가 없습니다.")

st.divider()

# --- 검색 및 추가 ---
st.markdown("<span class='section-title'>🔍 도서 추가</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="제목이나 저자...", label_visibility="collapsed")
if q:
    res = requests.get(f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}", headers={"User-Agent": "Mozilla/5.0"}).text
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)
    if imgs:
        cols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with cols[i]:
                st.image(url, use_container_width=True)
                g_val = genres[i] if i < len(genres) else "미지정"
                sel_g = st.text_input("장르", value=g_val, key=f"s_g_{i}", label_visibility="collapsed")
                c1, c2 = st.columns(2)
                if c1.button("📖 읽음", key=f"r_btn_{i}"):
                    img_d = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    st.session_state.collection.append({"img": Image.open(io.BytesIO(img_d)).convert("RGB"), "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_g})
                    save_all(); st.rerun()
                if c2.button("🩵 위시", key=f"w_btn_{i}"):
                    st.session_state.wishlist.append({"url": url, "genre": sel_g}); save_all(); st.rerun()

st.divider()

# --- 하단 리스트 ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        p_idx = []
        c1, c2 = st.columns([1, 2])
        if c1.button("🗑️ 전체 삭제"): st.session_state.collection = []; save_all(); st.rerun()
        is_del = c2.toggle("삭제 모드 활성화")
        
        row_cols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with row_cols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("인쇄", key=f"chk_{idx}", value=True): p_idx.append(idx)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                
                try: d_val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except: d_val = [date.today(), date.today()]
                
                new_d = st.date_input("날짜", d_val, key=f"dt_{idx}", label_visibility="collapsed")
                b1, b2 = st.columns([2, 1])
                if b1.button("수정", key=f"upd_{idx}"):
                    if len(new_d) == 2:
                        st.session_state.collection[idx]["start"], st.session_state.collection[idx]["end"] = new_d[0].isoformat(), new_d[1].isoformat()
                        save_all(); st.rerun()
                if is_del and b2.button("❌", key=f"del_{idx}"):
                    st.session_state.collection.pop(idx); save_all(); st.rerun()
        
        if p_idx:
            pdf = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            cur_x, cur_y = 100, 100
            for i in p_idx:
                img = st.session_state.collection[i]["img"]
                h_ratio = TARGET_H_PX / float(img.size[1])
                res_img = img.resize((int(img.size[0] * h_ratio), TARGET_H_PX), Image.LANCZOS)
                if cur_x + res_img.size[0] > A4_W_PX - 100: cur_x = 100; cur_y += TARGET_H_PX + 40
                pdf.paste(res_img, (cur_x, cur_y)); cur_x += res_img.size[0] + 40
            buf = io.BytesIO(); pdf.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 PDF 저장 ({len(p_idx)}권)", buf.getvalue(), "books.pdf")

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        w_row = st.columns(3)
        for i, itm in enumerate(st.session_state.wishlist):
            with w_row[i % 3]:
                try:
                    r_raw = requests.get(itm['url'], headers={"User-Agent": "Mozilla/5.0"}).content
                    w_img = Image.open(io.BytesIO(r_raw)).convert("RGB")
                    st.image(w_img, use_container_width=True)
                    st.caption(f"장르: {itm.get('genre', '미지정')}")
                    wc1, wc2 = st.columns(2)
                    if wc1.button("✅ 완료", key=f"w_r_{i}"):
                        st.session_state.collection.append({"img": w_img, "url": itm['url'], "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": itm.get('genre', '미지정')})
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                    if wc2.button("🗑️", key=f"w_d_{i}"):
                        st.session_state.wishlist.pop(i); save_all(); st.rerun()
                except: st.error("이미지 오류")