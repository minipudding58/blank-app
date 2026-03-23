import streamlit as st
import requests
from PIL import Image
import io
import re
import json
import os
from datetime import datetime, date
from collections import Counter

# ==========================================
# ⚙️ 1. 전역 설정 및 상수 (A4 출력 최적화)
# ==========================================
DPI = 300
TARGET_H_PX = int((40 / 25.4) * DPI)  # 책 표지 높이 약 40mm
A4_W_PX = int((210 / 25.4) * DPI)     # A4 너비
A4_H_PX = int((297 / 25.4) * DPI)     # A4 높이

st.set_page_config(
    page_title="나의 독서 기록장",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 2. CSS 스타일 (레이아웃 및 버튼 정렬)
# ==========================================
st.markdown(f"""
    <style>
    /* 전체 배경 및 컨테이너 설정 */
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 1200px;
    }}
    
    /* [핵심] 위시리스트 탭에서 내 서재 토글 버튼 위치와 맞추기 위한 공백 */
    .wish-top-spacer {{
        height: 74px !important; 
        display: block;
        width: 100%;
    }}

    /* 타이틀 및 헤더 스타일 */
    .main-title {{ 
        font-size: 42px; 
        font-weight: 800; 
        color: #1E1E1E; 
        margin-bottom: 5px !important;
        letter-spacing: -1px;
    }}
    
    .top-header-wrapper {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 60px;
        margin-bottom: 30px;
        padding: 20px 0;
        border-bottom: 1px solid #F0F0F0;
    }}
    
    .header-label {{ 
        font-size: 16px !important; 
        font-weight: 600 !important; 
        color: #666 !important;
        margin-bottom: 10px;
        display: block;
    }}
    
    .total-count-display {{
        font-size: 54px;
        font-weight: 900;
        color: #87CEEB;
        line-height: 1;
    }}
    
    .genre-card-item {{ 
        background-color: #FFFFFF; 
        border: 1px solid #EAEAEA; 
        border-radius: 14px; 
        padding: 12px 18px; 
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        min-width: 80px;
    }}

    /* 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        padding: 0 40px !important;
    }}
    .stTabs [data-baseweb="tab"] p {{
        font-size: 19px !important;
        font-weight: 700 !important;
    }}

    /* [핵심] 이미지 및 버튼 수평 정렬 시스템 */
    [data-testid="stImage"] img {{ 
        height: 220px !important; 
        object-fit: contain !important; 
        border-radius: 10px;
        border: 1px solid #F0F0F0;
        transition: transform 0.2s;
    }}
    
    .stButton button {{
        width: 100% !important;
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }}

    /* 수평 버튼 전용 스타일 */
    .edit-btn-blue button {{
        background-color: transparent !important;
        border: 1px solid #87CEEB !important;
    }}
    .edit-btn-blue button p {{ color: #87CEEB !important; }}
    
    .del-btn-red button {{
        background-color: transparent !important;
        border: 1px solid #FF6B6B !important;
    }}
    .del-btn-red button p {{ color: #FF6B6B !important; }}

    .date-text {{ 
        font-size: 13px; 
        color: #999; 
        display: block; 
        margin-top: 10px;
        font-family: 'Pretendard', sans-serif;
    }}
    
    /* 검색창 및 입력창 커스텀 */
    div[data-baseweb="input"] {{ 
        background-color: #F7F7F7 !important;
        border-radius: 10px !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🗝️ 3. 세션 관리 및 데이터 로드/저장
# ==========================================
# 쿼리 파라미터 안전 처리 (AttributeError 방지)
try:
    params = st.query_params
    if "user" in params:
        st.session_state.user_id = params["user"]
except:
    pass

if 'user_id' not in st.session_state:
    st.markdown("<div class='main-title'>📖 독서 기록장 입장</div>", unsafe_allow_html=True)
    with st.container():
        u_input = st.text_input("닉네임을 입력하세요", placeholder="예: 먼작귀", label_visibility="collapsed")
        if st.button("기록장 열기") and u_input:
            st.session_state.user_id = u_input
            try: st.query_params["user"] = u_input
            except: pass
            st.rerun()
    st.stop()

USER_DATA_PATH = f"data_{st.session_state.user_id}.json"

# 세션 초기화
if 'collection' not in st.session_state:
    st.session_state.collection = []
    st.session_state.wishlist = []
    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {"query": "", "items": []}

    # 데이터 파일 읽기
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                st.session_state.wishlist = loaded.get("wishlist", [])
                # 이미지 객체 복구 로직
                for item in loaded.get("collection", []):
                    try:
                        resp = requests.get(item["url"], timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                        if resp.status_code == 200:
                            st.session_state.collection.append({
                                "img": Image.open(io.BytesIO(resp.content)).convert("RGB"), 
                                "url": item["url"], 
                                "start": item.get("start", date.today().isoformat()),
                                "end": item.get("end", date.today().isoformat()), 
                                "genre": item.get("genre", "미지정")
                            })
                    except Exception as e:
                        continue
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")

def commit_changes():
    """현재 세션 상태를 JSON 파일로 물리 저장"""
    try:
        payload = {
            "wishlist": st.session_state.wishlist, 
            "collection": [
                {
                    "url": i["url"], 
                    "start": i.get("start", date.today().isoformat()), 
                    "end": i.get("end", date.today().isoformat()), 
                    "genre": i.get("genre", "미지정")
                } for i in st.session_state.collection
            ]
        }
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"데이터 저장 오류: {e}")

# ==========================================
# 📊 4. 메인 대시보드 레이아웃
# ==========================================
st.markdown(f"<div class='main-title'>{st.session_state.user_id}님의 서재</div>", unsafe_allow_html=True)

header_c1, header_c2 = st.columns([1, 3.5])
with header_c1:
    st.markdown(f"<span class='header-label'>{datetime.now().year}년 읽은 책</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='total-count-display'>{len(st.session_state.collection)}<span style='font-size:24px; color:#333;'> 권</span></div>", unsafe_allow_html=True)

with header_c2:
    st.markdown("<span class='header-label'>📚 카테고리 통계</span>", unsafe_allow_html=True)
    if st.session_state.collection:
        genre_stats = Counter([itm.get("genre", "미지정") for itm in st.session_state.collection])
        stat_html = "".join([f"<div class='genre-card-item'>{g}<br><b>{c}권</b></div>" for g, c in genre_stats.items()])
        st.markdown(f"<div style='display:flex; gap:14px; flex-wrap:wrap;'>{stat_html}</div>", unsafe_allow_html=True)
    else:
        st.info("책을 추가하면 장르별 통계가 표시됩니다.")

st.divider()

# ==========================================
# 🔍 5. 실시간 도서 검색 및 캐싱 로직
# ==========================================
st.markdown("<span class='header-label'>🔍 새로운 도서 찾기</span>", unsafe_allow_html=True)
q_input = st.text_input("검색", placeholder="책 제목이나 저자명을 입력하고 엔터를 누르세요", label_visibility="collapsed")

if q_input and q_input != st.session_state.search_cache["query"]:
    try:
        # 알라딘 검색 스크래핑
        search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={q_input}"
        raw_res = requests.get(search_url, headers={"User-Agent":"Mozilla/5.0"}).text
        
        # 정규표현식으로 데이터 추출
        found_imgs = list(dict.fromkeys(re.findall(r'https://image\.aladin\.co\.kr/[^"\'\s>]+cover[^"\'\s>]+', raw_res)))
        found_genres = re.findall(r'\[<a[^>]+>([^<]+)</a>\]', raw_res)
        
        st.session_state.search_cache["items"] = []
        for i in range(min(4, len(found_imgs))):
            st.session_state.search_cache["items"].append({
                "url": found_imgs[i],
                "genre": found_genres[i] if i < len(found_genres) else "미지정"
            })
        st.session_state.search_cache["query"] = q_input
    except Exception as e:
        st.error(f"검색 엔진 연결 오류: {e}")

# 검색 결과 렌더링
if st.session_state.search_cache["items"]:
    search_cols = st.columns(4)
    for idx, item in enumerate(st.session_state.search_cache["items"]):
        with search_cols[idx]:
            st.image(item["url"], use_container_width=True)
            s_genre = st.text_input("장르수정", value=item["genre"], key=f"s_genre_{idx}", label_visibility="collapsed")
            
            btn_c = st.columns(2)
            if btn_c[0].button("📖 읽음", key=f"add_lib_{idx}", use_container_width=True):
                img_data = requests.get(item["url"], headers={"User-Agent":"Mozilla/5.0"}).content
                st.session_state.collection.append({
                    "img": Image.open(io.BytesIO(img_data)).convert("RGB"), 
                    "url": item["url"], 
                    "start": date.today().isoformat(), 
                    "end": date.today().isoformat(), 
                    "genre": s_genre
                })
                commit_changes(); st.rerun()
            
            if btn_c[1].button("🩵 위시", key=f"add_wish_{idx}", use_container_width=True):
                st.session_state.wishlist.append({"url": item["url"], "genre": s_genre})
                commit_changes(); st.rerun()

st.divider()

# ==========================================
# 📚 6. 메인 콘텐츠 탭 (서재 / 위시리스트)
# ==========================================
tab_main, tab_wish = st.tabs(["📚 내 서재 목록", "🩵 읽고 싶은 책"])

# --- 6-1. 내 서재 탭 ---
with tab_main:
    # 편집 모드 토글
    is_edit_mode = st.toggle("편집 및 PDF 출력 모드 활성화", key="master_edit_switch")
    pdf_selected_indices = []
    
    if st.session_state.collection:
        lib_cols = st.columns(4)
        for i, item in enumerate(st.session_state.collection):
            with lib_cols[i % 4]:
                st.image(item["img"], use_container_width=True)
                
                if is_edit_mode:
                    # 체크박스 선택 (PDF용)
                    if st.checkbox("이 책 포함", key=f"chk_{i}", value=True):
                        pdf_selected_indices.append(i)
                    
                    # 상세 정보 수정
                    new_g = st.text_input("장르", value=item['genre'], key=f"edit_g_{i}", label_visibility="collapsed")
                    try:
                        curr_dates = (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
                    except:
                        curr_dates = (date.today(), date.today())
                    new_d = st.date_input("날짜", curr_dates, key=f"edit_d_{i}", label_visibility="collapsed")
                    
                    # 수정/삭제 버튼 가로 정렬
                    eb_c = st.columns(2)
                    with eb_c[0]:
                        st.markdown('<div class="edit-btn-blue">', unsafe_allow_html=True)
                        if st.button("저장", key=f"save_btn_{i}"):
                            sd = new_d[0].isoformat() if isinstance(new_d, (list, tuple)) else new_d.isoformat()
                            ed = new_d[1].isoformat() if isinstance(new_d, (list, tuple)) and len(new_d) > 1 else sd
                            st.session_state.collection[i].update({"genre": new_g, "start": sd, "end": ed})
                            commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with eb_c[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"del_btn_{i}"):
                            st.session_state.collection.pop(i); commit_changes(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 일반 모드 표기
                    st.markdown(f"**{item['genre']}**")
                    date_range = f"{item['start'].replace('-','/')} ~ {item['end'].replace('-','/')}"
                    st.markdown(f'<span class="date-text">{date_range}</span>', unsafe_allow_html=True)

        # PDF 생성 섹션
        if is_edit_mode and pdf_selected_indices:
            st.divider()
            if st.button(f"📥 선택한 {len(pdf_selected_indices)}권으로 PDF 책장 만들기", use_container_width=True):
                with st.spinner("고화질 이미지 배치 중..."):
                    canvas = Image.new('RGB', (A4_W_PX, A4_H_PX), (255, 255, 255))
                    x_cursor, y_cursor = 160, 160
                    for idx in pdf_selected_indices:
                        book_img = st.session_state.collection[idx]["img"]
                        h_ratio = TARGET_H_PX / float(book_img.size[1])
                        w_size = int(book_img.size[0] * h_ratio)
                        resized_img = book_img.resize((w_size, TARGET_H_PX), Image.LANCZOS)
                        
                        if x_cursor + w_size > A4_W_PX - 160:
                            x_cursor = 160
                            y_cursor += TARGET_H_PX + 70
                        
                        canvas.paste(resized_img, (x_cursor, y_cursor))
                        x_cursor += w_size + 70
                    
                    pdf_buffer = io.BytesIO()
                    canvas.save(pdf_buffer, format="PDF", resolution=300.0)
                    st.download_button("📂 생성된 PDF 다운로드", pdf_buffer.getvalue(), "my_shelf_export.pdf", use_container_width=True)
    else:
        st.info("서재가 비어있습니다. 위에서 책을 검색해 보세요!")

# --- 6-2. 위시리스트 탭 ---
with tab_wish:
    # 내 서재 탭의 토글 버튼만큼 공백 삽입
    st.markdown('<div class="wish-top-spacer"></div>', unsafe_allow_html=True)
    
    if st.session_state.wishlist:
        wish_cols = st.columns(4)
        for i, wish_item in enumerate(st.session_state.wishlist):
            with wish_cols[i % 4]:
                try:
                    # 위시리스트 이미지 실시간 로드
                    w_resp = requests.get(wish_item['url'], headers={"User-Agent":"Mozilla/5.0"}).content
                    w_img_obj = Image.open(io.BytesIO(w_resp))
                    st.image(w_img_obj, use_container_width=True)
                    
                    # 버튼 수평 정렬
                    wish_btn_c = st.columns(2)
                    with wish_btn_c[0]:
                        # 읽기 완료 클릭 시 즉시 이동 로직
                        if st.button("📖 읽기 완료!", key=f"w_done_{i}", use_container_width=True):
                            st.session_state.collection.append({
                                "img": w_img_obj.convert("RGB"), 
                                "url": wish_item['url'], 
                                "start": date.today().isoformat(), 
                                "end": date.today().isoformat(), 
                                "genre": wish_item.get('genre', '미지정')
                            })
                            st.session_state.wishlist.pop(i) # 위시에서 제거
                            commit_changes() # 파일 저장
                            st.rerun() # UI 갱신
                    
                    with wish_btn_c[1]:
                        st.markdown('<div class="del-btn-red">', unsafe_allow_html=True)
                        # 삭제하기 -> 삭제 변경
                        if st.button("🗑️ 삭제", key=f"w_del_{i}", use_container_width=True):
                            st.session_state.wishlist.pop(i)
                            commit_changes()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    continue
    else:
        st.info("읽고 싶은 책이 아직 없습니다. 검색을 통해 위시에 담아보세요!")

