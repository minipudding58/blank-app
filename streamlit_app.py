import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# --- ⚙️ 1. 기본 설정 (A4 인쇄 규격 및 세션) ---
DPI = 300
TARGET_H_PX_PRINT = int((40 / 25.4) * DPI) 
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🎨 2. 스타일 (누적 독서량 ✨1권✨ 디자인 및 테두리 제거) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* 입력창 클릭 시 빨간 테두리 제거 및 하늘색 강조 */
    div[data-baseweb="input"] {{
        border: 1px solid #ccc !important;
        box-shadow: none !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border: 1px solid #87CEEB !important;
        box-shadow: 0 0 0 0.2rem rgba(135, 206, 235, 0.25) !important;
    }}

    /* 누적 독서량 박스 원상복구 (image_f7b2fb.png 기준) */
    .total-container {{
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #eee;
    }}
    .total-label {{
        font-size: 16px;
        color: #666;
        margin-bottom: 5px;
    }}
    .total-count {{
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
    }}

    /* 장르 카드 디자인 */
    .genre-card {{
        background-color: #ffffff;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    .section-title {{
        font-size: 20px !important;
        font-weight: bold !important;
        margin-top: 20px;
        margin-bottom: 15px;
        display: block;
        color: #31333F;
    }}
    
    /* 책 이미지 높이 고정 */
    [data-testid="stImage"] img {{
        height: 220px !important;
        object-fit: contain !important;
        background-color: #fcfcfc;
        border-radius: 8px;
    }}

    /* 버튼 스타일 조정 */
    div.stButton > button {{
        border-radius: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🗝️ 3. 로그인 및 새로고침 유지 로직 ---
# URL 파라미터가 있으면 우선 사용, 없으면 세션 확인
query_params = st.query_params
if "user" in query_params:
    st.session_state.user_id = query_params["user"]

if 'user_id' not in st.session_state:
    st.title("📖 독서 기록 시작하기")
    u_input = st.text_input("나만의 닉네임을 입력하세요", placeholder="예: 치이카와")
    if st.button("기록장 열기") and u_input:
        st.session_state.user_id = u_input
        st.query_params["user"] = u_input
        st.rerun()
    st.stop()

USER_DATA_FILE = f"data_{st.session_state.user_id}.json"

# --- 🔗 4. 데이터 로드 및 복구 ---
if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.wishlist = d.get("wishlist", [])
                for itm in d.get("collection", []):
                    u = itm.get("url")
                    if u:
                        try:
                            r = requests.get(u, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                            if r.status_code == 200:
                                st.session_state.collection.append({
                                    "img": Image.open(io.BytesIO(r.content)).convert("RGB"), 
                                    "url": u,
                                    "start": itm.get("start", date.today().isoformat()),
                                    "end": itm.get("end", date.today().isoformat()),
                                    "genre": itm.get("genre", "미지정")
                                })
                        except: continue
        except: pass

def save_all():
    data = {
        "wishlist": st.session_state.wishlist, 
        "collection": [{"url": i["url"], "start": i["start"], "end": i["end"], "genre": i.get("genre", "미지정")} for i in st.session_state.collection]
    }
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🏠 5. 사이드바 (사용자 메뉴) ---
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.user_id}** 님의 서재")
    st.write("---")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()
    st.write("---")
    if st.button("🔥 내 기록 전체 삭제", use_container_width=True):
        if os.path.exists(USER_DATA_FILE):
            os.remove(USER_DATA_FILE)
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# --- 📊 6. 상단 대시보드 (✨1권✨ 디자인 복구) ---
st.title(f"📖 {st.session_state.user_id}의 서재")

# 누적 독서량 박스 (image_f7b2fb.png 형태 복구)
st.markdown(f"""
    <div class="total-container">
        <div class="total-label">누적</div>
        <div class="total-count">✨ {len(st.session_state.collection)}권 읽음 ✨</div>
    </div>
    """, unsafe_allow_html=True)

# 장르별 통계 한 줄 배치
if st.session_state.collection:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
    g_cols = st.columns(len(counts) if len(counts) > 0 else 1)
    for i, (genre, count) in enumerate(counts.items()):
        with g_cols[i % len(g_cols)]:
            st.markdown(f"""
                <div class="genre-card">
                    <div style="font-size:14px; color:#555;">{genre}</div>
                    <div style="font-size:18px; font-weight:bold;">{count}권</div>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# --- 🔍 7. 책 검색 (검색 실패 해결 및 장르 연동) ---
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
q = st.text_input("검색어 입력", placeholder="제목 또는 저자명을 입력하세요", label_visibility="collapsed")

if q:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q}"
    try:
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res_text = response.text
        
        # 알라딘 검색 결과에서 도서 블록을 더 넓은 범위로 탐색
        items = re.findall(r'<(?:table|div)[^>]*(?:class="ss_book_list"|class="ss_book_box")[^>]*>.*?</(?:table|div)>', res_text, re.DOTALL)
        
        # 만약 위 패턴으로 안 잡히면 이미지 기반으로 강제 파싱
        if not items:
            img_urls = re.findall(r'https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', res_text)
            if img_urls:
                # 중복 제거 후 4개만 사용
                img_urls = list(dict.fromkeys(img_urls))[:4]
                scols = st.columns(4)
                for i, url in enumerate(img_urls):
                    with scols[i]:
                        st.image(url, use_container_width=True)
                        sel_genre = st.text_input("장르", value="미지정", key=f"sg_{i}", label_visibility="collapsed")
                        b_cols = st.columns(2)
                        if b_cols[0].button("📖 읽음", key=f"r_{i}", use_container_width=True):
                            img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                            })
                            save_all(); st.rerun()
                        if b_cols[1].button("🩵 위시", key=f"w_{i}", use_container_width=True):
                            st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                            save_all(); st.rerun()
            else:
                st.warning("검색 결과가 없습니다. 제목을 더 정확하게 입력해보세요.")
        else:
            # 정상적인 블록 파싱 성공 시
            scols = st.columns(4)
            for i, block in enumerate(items[:4]):
                with scols[i]:
                    img_match = re.search(r'https://image\.aladin\.co\.kr/(?:product|pimg)/\d+/\d+/cover[^"\'\s>]+', block)
                    if img_match:
                        url = img_match.group(0)
                        # 장르 추출 (ss_f_g_l 클래스 기반)
                        genre_match = re.search(r'class="ss_f_g_l"[^>]*>([^<]+)</a>', block)
                        g_val = genre_match.group(1) if genre_match else "미지정"
                        
                        st.image(url, use_container_width=True)
                        sel_genre = st.text_input("장르", value=g_val, key=f"sg_b_{i}", label_visibility="collapsed")
                        
                        b_cols = st.columns(2)
                        if b_cols[0].button("📖 읽음", key=f"rb_{i}", use_container_width=True):
                            img_data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                                "url": url, "start": date.today().isoformat(), "end": date.today().isoformat(), "genre": sel_genre
                            })
                            save_all(); st.rerun()
                        if b_cols[1].button("🩵 위시", key=f"wb_{i}", use_container_width=True):
                            st.session_state.wishlist.append({"url": url, "genre": sel_genre})
                            save_all(); st.rerun()
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")

st.divider()

# --- 📚 8. 목록 관리 및 PDF 저장 ---
l_col, r_col = st.columns(2)
with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책 목록</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        p_idx = []
        del_m = st.toggle("삭제 모드 활성화")
        dcols = st.columns(3)
        for idx, itm in enumerate(st.session_state.collection):
            with dcols[idx % 3]:
                st.image(itm["img"], use_container_width=True)
                if st.checkbox("선택", key=f"p_{idx}", value=True):
                    p_idx.append(idx)
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                
                # 날짜 수정 로직
                try:
                    val = [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])]
                except:
                    val = [date.today(), date.today()]
                
                new_dr = st.date_input("기간", val, key=f"ed_{idx}", label_visibility="collapsed")
                
                b_edit_cols = st.columns([2, 1])
                if b_edit_cols[0].button("저장", key=f"sv_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                        st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and b_edit_cols[1].button("❌", key=f"dc_{idx}", use_container_width=True):
                    st.session_state.collection.pop(idx)
                    save_all(); st.rerun()
        
        if p_idx:
            # PDF 생성
            sheet = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
            x, y = 150, 150
            for i in p_idx:
                img = st.session_state.collection[i]["img"]
                ratio = TARGET_H_PX_PRINT / float(img.size[1])
                img_res = img.resize((int(img.size[0] * ratio), TARGET_H_PX_PRINT), Image.LANCZOS)
                if x + img_res.size[0] > A4_W_PX - 150:
                    x = 150
                    y += TARGET_H_PX_PRINT + 60
                sheet.paste(img_res, (x, y))
                x += img_res.size[0] + 60
            
            buf = io.BytesIO()
            sheet.save(buf, format="PDF", resolution=300.0)
            st.download_button(f"📥 선택한 {len(p_idx)}권 PDF로 저장", buf.getvalue(), f"{st.session_state.user_id}_reading_list.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                url = item.get('url') if isinstance(item, dict) else item
                try:
                    r_img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).content
                    img_obj = Image.open(io.BytesIO(r_img)).convert("RGB")
                    st.image(img_obj, use_container_width=True)
                    st.caption(item.get('genre', '미지정') if isinstance(item, dict) else "미지정")
                    
                    wb_cols = st.columns(2)
                    if wb_cols[0].button("📖읽음", key=f"wr_{i}", use_container_width=True):
                        st.session_state.collection.append({
                            "img": img_obj, "url": url, 
                            "start": date.today().isoformat(), "end": date.today().isoformat(), 
                            "genre": item.get('genre', '미지정') if isinstance(item, dict) else "미지정"
                        })
                        st.session_state.wishlist.pop(i)
                        save_all(); st.rerun()
                    if wb_cols[1].button("🗑️", key=f"w_d_{i}", use_container_width=True):
                        st.session_state.wishlist.pop(i)
                        save_all(); st.rerun()
                except:
                    st.error("이미지 로드 실패")

# --- ⚙️ 9. 자동 저장 및 마무리 ---
# (코드 하단에 추가적인 로그를 남기지 않음)