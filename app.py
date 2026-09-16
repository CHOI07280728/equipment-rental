import streamlit as st
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="스마트 장비 대여 관리 시스템", layout="wide")

# 2. 세션 상태(Session State) 초기화 (데이터 유지)
if "users" not in st.session_state:
    st.session_state.users = {}  # {phone: {"name": name, "phone": phone}}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "equipments" not in st.session_state:
    st.session_state.equipments = [
        {"id": 101, "name": "시네마 카메라 (Blackmagic 6K)", "category": "카메라"},
        {"id": 102, "name": "삼각대 (Libec 650EX)", "category": "삼각대"},
        {"id": 103, "name": "무선 마이크 (Hollyland Lark M1)", "category": "음향"},
        {"id": 104, "name": "지속광 조명 (Amaran 200d)", "category": "조명"},
        {"id": 105, "name": "프리미어용 모니터링 탭", "category": "디스플레이"},
    ]

if "rentals" not in st.session_state:
    st.session_state.rentals = []

# 타이틀
st.title("🎥 스마트 장비 대여 관리 시스템")

# 3. 사이드바 - 로그인 및 회원가입 (핸드폰 번호 ID)
st.sidebar.header("👤 회원 관리")

if st.session_state.logged_in_user is None:
    tab_login, tab_register = st.sidebar.tabs(["로그인", "회원가입"])
    
    with tab_register:
        st.subheader("신규 회원가입")
        reg_phone = st.text_input("핸드폰 번호 (ID)", placeholder="01012345678", key="reg_phone")
        reg_name = st.text_input("성명", placeholder="홍길동", key="reg_name")
        if st.button("회원가입 완료", use_container_width=True):
            if reg_phone and reg_name:
                st.session_state.users[reg_phone] = {"name": reg_name, "phone": reg_phone}
                st.success(f"회원가입 성공! (ID: {reg_phone})")
            else:
                st.error("핸드폰 번호와 성명을 모두 입력해줌.")
                
    with tab_login:
        st.subheader("로그인")
        login_phone = st.text_input("핸드폰 번호 (ID)", key="login_phone")
        if st.button("로그인", use_container_width=True):
            if login_phone in st.session_state.users:
                st.session_state.logged_in_user = st.session_state.users[login_phone]
                st.rerun()
            else:
                st.error("존재하지 않는 회원 ID(핸드폰 번호)임.")
else:
    user = st.session_state.logged_in_user
    st.sidebar.success(f"**{user['name']}** 님 로그인 중")
    st.sidebar.info(f"ID (핸드폰): {user['phone']}")
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

# 4. 메인 메뉴 구성
tab1, tab2, tab3 = st.tabs(["📝 장비 대여 신청서", "⚙️ 관리자 대여 승인 및 불출/반납 관리", "📅 대여 일정 현황"])

# ---------------------------------------------------------
# TAB 1: 장비 대여 신청서 (다중 선택 기능 포함)
# ---------------------------------------------------------
with tab1:
    st.header("📝 장비 대여 신청서")
    
    # 신청자 정보 자동 입력
    col_user1, col_user2 = st.columns(2)
    with col_user1:
        app_name = st.text_input(
            "신청자 성명", 
            value=st.session_state.logged_in_user["name"] if st.session_state.logged_in_user else "로그인 필요", 
            disabled=True
        )
    with col_user2:
        app_id = st.text_input(
            "신청자 ID (핸드폰 번호)", 
            value=st.session_state.logged_in_user["phone"] if st.session_state.logged_in_user else "로그인 필요", 
            disabled=True
        )

    # 장비 다중 선택 시스템
    st.subheader("📦 대여 기자재 다중 선택")
    equipment_options = [f"[{item['category']}] {item['name']}" for item in st.session_state.equipments]
    selected_equipments = st.multiselect("대여할 장비를 여러 개 선택해줌:", equipment_options)

    # 일정 선택
    st.subheader("📅 대여 기간 설정")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("대여 시작일", value=date.today())
    with col_date2:
        end_date = st.date_input("반납 예정일", value=date.today())

    # 신청 제출
    if st.button("🚀 대여 신청서 제출", type="primary", use_container_width=True):
        if st.session_state.logged_in_user is None:
            st.error("로그인 후 대여 신청이 가능함.")
        elif not selected_equipments:
            st.error("대여할 기자재를 최소 1개 이상 선택해줌.")
        elif start_date > end_date:
            st.error("반납 예정일이 대여 시작일보다 빠를 수 없음.")
        else:
            res_number = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_rental = {
                "res_id": res_number,
                "user_name": app_name,
                "user_id": app_id,
                "equipments": selected_equipments,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "approval": "대기",
                "checkout": "미불출",
                "return_status": "미반납"
            }
            st.session_state.rentals.append(new_rental)
            st.success(f"대여 신청이 완료됨! (예약 번호: {res_number})")

# ---------------------------------------------------------
# TAB 2: 관리자 대여 승인 및 불출/반납 관리
# ---------------------------------------------------------
with tab2:
    st.header("⚙️ 관리자 대여 승인 및 불출/반납 관리")
    
    if not st.session_state.rentals:
        st.info("현재 등록된 대여 신청 내역이 없음.")
    else:
        for idx, rental in enumerate(st.session_state.rentals):
            with st.container():
                st.markdown(f"### 📌 예약 넘버: `{rental['res_id']}`")
                col_info, col_app, col_chk, col_ret, col_detail = st.columns([2, 1.5, 1.5, 1.5, 1.5])
                
                with col_info:
                    st.write(f"**신청자:** {rental['user_name']} ({rental['user_id']})")
                    st.caption(f"기간: {rental['start_date']} ~ {rental['end_date']}")
                
                with col_app:
                    rental["approval"] = st.selectbox(
                        "대여 승인", 
                        ["대기", "승인", "거절"], 
                        index=["대기", "승인", "거절"].index(rental["approval"]),
                        key=f"app_{idx}"
                    )
                
                with col_chk:
                    rental["checkout"] = st.selectbox(
                        "불출 현황", 
                        ["미불출", "불출 완료"], 
                        index=["미불출", "불출 완료"].index(rental["checkout"]),
                        key=f"chk_{idx}"
                    )
                
                with col_ret:
                    rental["return_status"] = st.selectbox(
                        "반납 현황", 
                        ["미반납", "반납 완료"], 
                        index=["미반납", "반납 완료"].index(rental["return_status"]),
                        key=f"ret_{idx}"
                    )
                
                with col_detail:
                    # 자세히 보기 팝업(Expander/Modal 역할)
                    with st.popover("🔍 자세히 보기"):
                        st.markdown(f"**[예약 번호 {rental['res_id']} 상세 목록]**")
                        st.write("📋 **선택한 대여 기자재:**")
                        for eq in rental["equipments"]:
                            st.write(f"- {eq}")
                
                st.divider()

# ---------------------------------------------------------
# TAB 3: 대여 일정 현황
# ---------------------------------------------------------
with tab3:
    st.header("📅 대여 일정 현황")
    if st.session_state.rentals:
        df_rentals = pd.DataFrame(st.session_state.rentals)
        df_display = df_rentals[["res_id", "user_name", "start_date", "end_date", "approval", "checkout", "return_status"]]
        df_display.columns = ["예약 넘버", "신청자", "시작일", "반납일", "대여 승인", "불출 현황", "반납 현황"]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("등록된 일정 데이터가 없음.")
