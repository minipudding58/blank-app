import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
import calendar
from collections import Counter

# --- 기초 규격 설정 (인쇄 및 정렬용) ---
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI) # 목록용 세로 길이 고정
A4_W_PX = int((210 / 25.4) * DPI)
A4_H_PX = int((297 / 25.4) * DPI)

st.set_page_config(page_title="나의 독서 기록", page_icon="📖", layout="wide")

# --- 🔗 [UI] 닉네임 입력 (로그인) 및 데이터 로드 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user", "")

if not st.session_state.user_id:
    st.title("📖 독서 기록 시작하기")
    
    # ✅ 2번 해결: 닉네임 입력창 빨간 테두리 제거 CSS
    st.markdown("""
        <style>
        div[data-baseweb="input"] { border: none !important; box-shadow: none !important; }
        </style>
        """, unsafe_allow_html=True)
    u_input = st.text_input("닉네임 입력", placeholder="치이카와")
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
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 🎨 스타일 설정 (테두리 제거 및 장르 칸 배치) ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem !important; }}
    
    /* 상단 박제 영역 스타일 */
    .stat-container {{ text-align: center; }}
    .genre-wrapper {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .genre-card {{
        background-color: #f8f9fa;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 5px 12px;
        min-width: 60px;
        text-align: center;
    }}
    .genre-label {{ font-size: 12px; color: #888; }}
    .genre-value {{ font-size: 16px; font-weight: bold; color: #333; }}

    /* ✅ 타이틀 폰트 및 크기 통일 */
    .section-title {{ 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin-bottom: 12px; 
        display: block; 
        color: #31333F; /* 기본 텍스트 색상 */
    }}

    /* ✅ 2번 해결: 검색창 빨간 테두리 및 그림자 완전 제거 */
    .stTextInput div[data-baseweb="input"] {{
        border: none !important;
        box-shadow: none !important;
    }}

    /* 버튼 스타일 및 여백 */
    div.stButton > button, div.stDownloadButton > button {{
        width: 100% !important;
        height: 45px !important;
        border-radius: 5px;
    }}
    .stDateInput div[data-baseweb="input"] {{
        height: 45px !important;
        border-radius: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 최상단 타이틀 복구
st.markdown(f"<h1>📖 {st.session_state.user_id}의 독서 기록</h1>", unsafe_allow_html=True)

# ✅ 타이틀 하단 요청하신 공백 두 칸
st.write("")
st.write("")

# --- 📊 상단 대시보드 ---
# 누적독서 & 장르 현황 (배경색 없음)
t_col1, t_col2 = st.columns([1, 4])
with t_col1:
    st.markdown(f"""
        <div class="stat-container">
            <div style="font-size: 14px; color: #666;">{datetime.now().year}년 누적</div>
            <div style="font-size: 40px; font-weight: bold; color: #87CEEB;">✨{len(st.session_state.collection)}권✨</div>
        </div>
    """, unsafe_allow_html=True)

# ✅ 장르별 독서 현황 완벽 복구
with t_col2:
    st.markdown("<span class='section-title'>📚 장르별 독서 현황</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        counts = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        genre_items = "".join([f"<div class='genre-card'><div class='genre-label'>{g}</div><div class='genre-value'>{c}권</div></div>" for g, c in counts.items()])
        st.markdown(f"<div class='genre-wrapper'>{genre_items}</div>", unsafe_allow_html=True)
    else:
        st.caption("기록이 없습니다.")

st.divider()

# --- 🔍 책 검색 섹션 (장르 정밀 연동 강화) ---
# 책 제목 입력 폰트 크기 확대
st.markdown("<span class='section-title'>🔍 책 검색</span>", unsafe_allow_html=True)
query = st.text_input("제목 입력창", placeholder="제목/저자 입력...", label_visibility="collapsed")

if query:
    search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={query}"
    res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}).text
    # 엑박 방지 이미지 추출
    imgs = list(dict.fromkeys(re.findall(r'https://image.aladin.co.kr/product/\d+/\d+/cover[^"\'\s>]+', res)))
    # ✅ 1번 해결: 알라딘 카테고리 정밀 추출 (마지막 카테고리 매칭)
    # 카테고리 매칭 방식을 '만화' 같은 포괄적 단어가 아닌 세부 장르(마지막 카테고리)로 수정
    genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', res)

    if imgs:
        scols = st.columns(4)
        for i, url in enumerate(imgs[:4]):
            with scols[i]:
                st.image(url, use_container_width=True)
                # 추출한 세부 장르 가져오기 (없으면 미지정)
                g_val = genres[i] if i < len(genres) else "미지정"
                # ✅ 검색 결과에서 긁어온 세부 장르가 자동으로 입력됨
                sel_genre = st.text_input("장르", value=g_val, key=f"src_g_{i}", label_visibility="collapsed")
                
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

# --- 📚 하단 목록 및 인쇄 기능 (완전 복구) ---
l_col, r_col = st.columns(2)

with l_col:
    st.markdown("<span class='section-title'>✅ 읽은 책</span>", unsafe_allow_html=True)
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
                st.image(itm["img"], use_container_width=True)
                # 인쇄 선택 체크박스 유지
                if st.checkbox("인쇄 선택", key=f"p_{idx}", value=True): print_Indices.append(idx)
                
                st.caption(f"장르: {itm.get('genre', '미지정')}")
                # ✅ 날짜 안 잘리게 넉넉한 입력창
                new_dr = st.date_input("날짜", [date.fromisoformat(itm["start"]), date.fromisoformat(itm["end"])], key=f"e_d_{idx}", label_visibility="collapsed")
                
                # ✅ 넉넉한 수정 버튼 옆으로
                date_c1, date_c2 = st.columns([2, 1])
                if date_c1.button("수정", key=f"sv_{idx}", use_container_width=True):
                    if len(new_dr) == 2:
                        st.session_state.collection[idx]["start"] = new_dr[0].isoformat()
                        st.session_state.collection[idx]["end"] = new_dr[1].isoformat()
                        save_all(); st.rerun()
                if del_m and date_c2.button("❌", key=f"dc_{idx}", use_container_width=True):
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
                sheet.paste(img_res, (x_pos, y_pos)); x_pos += img_res.size[0] + 40
            buf = io.BytesIO(); sheet.save(buf, format="PDF", resolution=300.0)
            # 인쇄 버튼도 넉넉하게
            st.download_button(f"📥 선택 {len(print_Indices)}권 PDF 인쇄", buf.getvalue(), "books.pdf", use_container_width=True)

with r_col:
    st.markdown("<span class='section-title'>🩵 위시리스트</span>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        wcols = st.columns(3)
        for i, item in enumerate(st.session_state.wishlist):
            with wcols[i % 3]:
                # ✅ 세로 길이 고정 및 정렬
                img_raw = requests.get(item['url']).content
                img_obj = Image.open(io.BytesIO(img_raw)).convert("RGB")
                st.image(img_obj, use_container_width=True)
                st.caption(f"장르: {item.get('genre', '미지정')}")
                # ✅ 버튼 디자인 및 정렬 완벽 복구
                c1, c2 = st.columns(2)
                if c1.button("✅ 선택", key=f"wr_{i}", use_container_width=True):
                    st.session_state.collection.append({
                        "img": img_obj, "url": item['url'], 
                        "start": date.today().isoformat(), "end": date.today().isoformat(), 
                        "genre": item.get('genre', '미지정')
                    })
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()
                if c2.button("🗑️ 삭제", key=f"wd_{i}", use_container_width=True):
                    st.session_state.wishlist.pop(i); save_all(); st.rerun()