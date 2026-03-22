import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import quote

# 앱 화면 설정
st.set_page_config(page_title="독서 스티커 메이커", layout="centered")
st.title("📖 나만의 독서 스티커 메이커")
st.info("책 제목들을 쉼표(,)로 구분해서 적어주세요. 세로 4cm로 맞춰드려요!")

# 사용자 입력창
titles_input = st.text_area("책 제목 입력", "호구 김민서, 오늘 밤 세계에서 이 사랑이 사라진다 해도")
go_button = st.button("인쇄용 스티커 판 만들기 ✨")

if go_button:
    book_list = [t.strip() for t in titles_input.split(",") if t.strip()]
    
    DPI = 300
    A4_W, A4_H = int(8.27 * DPI), int(11.69 * DPI)
    PX_PER_CM = DPI / 2.54
    TARGET_H_PX = int(4 * PX_PER_CM) 
    
    sheet = Image.new('RGB', (A4_W, A4_H), 'white')
    margin = int(0.5 * PX_PER_CM)
    curr_x, curr_y = margin, margin
    
    with st.spinner('표지를 찾는 중입니다...'):
        for title in book_list:
            search_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=All&SearchWord={quote(title)}"
            res = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            t = res.text
            start = t.find("https://image.aladin.co.kr/product/")
            
            if start != -1:
                img_url = t[start:t.find(".jpg", start)+4]
                img_res = requests.get(img_url)
                img = Image.open(BytesIO(img_res.content))
                
                ratio = TARGET_H_PX / float(img.size[1])
                target_w_px = int(float(img.size[0]) * ratio)
                img_final = img.resize((target_w_px, TARGET_H_PX), Image.Resampling.LANCZOS)

                if curr_x + target_w_px + margin > A4_W:
                    curr_x = margin
                    curr_y += TARGET_H_PX + margin
                
                sheet.paste(img_final, (curr_x, curr_y))
                curr_x += target_w_px + margin

    st.image(sheet, use_container_width=True)
    buf = BytesIO()
    sheet.save(buf, format="PNG")
    st.download_button("📥 인쇄용 이미지 다운로드", buf.getvalue(), "my_stickers.png", "image/png")
