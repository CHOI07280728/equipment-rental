from datetime import date, datetime
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="스마트 장비 대여 및 통합 일정 관리 시스템",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. 세션 상태(Session State) 초기화
# 관리자 계정(admin/admin123)을 세션 데이터베이스에 사전 등록
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {
            "name": "총괄 관리자",
            "phone": "admin",
            "password": "admin123",
            "role": "ADMIN",
        }
    }

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "equipments" not in st.session_state:
    st.session_state.equipments = [
        {
            "id": 101,
            "name": "Blackmagic Pocket Cinema Camera 6K Pro",
            "category": "카메라",
        },
        {"id": 102, "name": "Sony FX3 시네마 카메라", "category": "카메라"},
        {"id": 103, "name": "Libec 650EX 비디오 삼각대", "category": "삼각대"},
        {"id": 104, "name": "SmallRig 숄더 리그 키트", "category": "액세서리"},
        {
            "id": 105,
            "name": "Hollyland Lark M1 무선 마이크",
            "category": "음향",
        },
        {"id": 106, "name": "Amaran 200d LED 지속광 조명", "category": "조명"},
        {"id": 107, "name": "Atomos Ninja V 5인치 모니터", "category": "디스플레이"},
    ]

if "rentals" not in st.session_state:
    st.session_state.rentals = [
        {
            "res_id": "RES-20260916-001",
            "user_name": "홍길동",
            "user_id": "01012345678",
            "equipments": [
                "[카메라] Blackmagic Pocket Cinema Camera 6K Pro",
                "[삼각대] Libec 650EX 비디오 삼각대",
            ],
            "start_date": "2026-09-16",
            "end_date": "2026-09-18",
            "approval": "승인",
            "checkout": "불출 완료",
            "return_status": "미반납",
            "note": "단편영화 촬영 지원",
        }
    ]

# 3. 사이드바 - 로그인 및 회원가입
st.sidebar.title("🔐 회원 인증 Center")

if st.session_state.logged_in_user is None:
    tab_login, tab_register = st.sidebar.tabs(["🔑 로그인", "📝 회원가입"])

    # 로그인 탭
    with tab_login:
        st.subheader("로그인")
        login_id = st.text_input("아이디 (핸드폰 번호)", key="login_id")
        login_pw = st.text_input(
            "비밀번호", type="password", key="login_pw"
        )

        if st.button("로그인", use_container_width=True, type="primary"):
            if login_id in st.session_state.users:
                user_info = st.session_state.users[login_id]
                if user_info["password"] == login_pw:
                    st.session_state.logged_in_user = user_info
                    st.success(f"{user_info['name']}님, 로그인 성공함.")
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않음.")
            else:
                st.error("존재하지 않는 아이디임.")

    # 회원가입 탭 (핸드폰 번호가 아이디 역할)
    with tab_register:
        st.subheader("신규 회원가입")
        reg_phone = st.text_input(
            "핸드폰 번호 (아이디)",
            placeholder="01012345678",
            key="reg_phone",
        )
        reg_name = st.text_input("성명", placeholder="홍길동", key="reg_name")
        reg_pw = st.text_input(
            "비밀번호", type="password", key="reg_pw"
        )
        reg_pw_confirm = st.text_input(
            "비밀번호 확인", type="password", key="reg_pw_confirm"
        )

        if st.button("회원가입 완료", use_container_width=True):
            if not reg_phone or not reg_name or not reg_pw:
                st.error("모든 입력 항목을 기입해줌.")
            elif reg_phone in st.session_state.users:
                st.error("이미 가입된 핸드폰 번호(아이디)임.")
            elif reg_pw != reg_pw_confirm:
                st.error("비밀번호 확인이 일치하지 않음.")
            else:
                st.session_state.users[reg_phone] = {
                    "name": reg_name,
                    "phone": reg_phone,
                    "password": reg_pw,
                    "role": "USER",
                }
                st.success("회원가입이 완료되었음. 로그인 탭에서 로그인해줌.")

else:
    user = st.session_state.logged_in_user
    st.sidebar.success(f"**{user['name']}** 님 접속 중")
    st.sidebar.info(f"아이디: {user['phone']}")
    st.sidebar.caption(
        f"권한: {'ADMIN (관리자)' if user.get('role') == 'ADMIN' else '일반 사용자'}"
    )

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

# 메인 타이틀
st.title("🎥 전문 장비 대여 및 통합 일정 관리 시스템")

# 메인 탭 구성
tab1, tab2, tab3 = st.tabs(
    [
        "📝 장비 대여 신청서",
        "⚙️ 관리자 승인 및 불출/반납 관리",
        "📅 대여 일정 현황 및 조정",
    ]
)

# ---------------------------------------------------------
# TAB 1: 장비 대여 신청서
# ---------------------------------------------------------
with tab1:
    st.header("📝 장비 대여 신청서 작성")

    if st.session_state.logged_in_user is None:
        st.warning("⚠️ 장비 대여 신청을 위해 먼저 사이드바에서 로그인해줌.")
    else:
        # 로그인 사용자의 성명과 ID(핸드폰 번호) 자동 연동
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            app_name = st.text_input(
                "신청자 성명",
                value=st.session_state.logged_in_user["name"],
                disabled=True,
            )
        with col_u2:
            app_id = st.text_input(
                "신청자 ID (핸드폰 번호)",
                value=st.session_state.logged_in_user["phone"],
                disabled=True,
            )

        st.subheader("📦 대여 기자재 다중 선택")
        eq_options = [
            f"[{item['category']}] {item['name']}"
            for item in st.session_state.equipments
        ]
        selected_eqs = st.multiselect(
            "대여할 장비를 여러 개 선택해줌 (다중 선택 가능):",
            eq_options,
            placeholder="장비를 선택해줌...",
        )

        st.subheader("📅 대여 기간 지정")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_d = st.date_input("대여 시작일", value=date.today())
        with col_d2:
            end_d = st.date_input("반납 예정일", value=date.today())

        note = st.text_area(
            "사용 목적 및 기타 요청사항", placeholder="예: 단편영화 제작 촬영"
        )

        if st.button(
            "🚀 장비 대여 신청서 제출", type="primary", use_container_width=True
        ):
            if not selected_eqs:
                st.error("대여할 장비를 1개 이상 선택해줌.")
            elif start_d > end_d:
                st.error("반납 예정일이 대여 시작일보다 빠를 수 없음.")
            else:
                res_no = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                new_item = {
                    "res_id": res_no,
                    "user_name": app_name,
                    "user_id": app_id,
                    "equipments": selected_eqs,
                    "start_date": str(start_d),
                    "end_date": str(end_d),
                    "approval": "대기",
                    "checkout": "미불출",
                    "return_status": "미반납",
                    "note": note,
                }
                st.session_state.rentals.append(new_item)
                st.success(
                    f"대여 신청이 성공적으로 완료되었음! (예약 넘버: {res_no})"
                )

# ---------------------------------------------------------
# TAB 2: 관리자 대여 승인 및 불출/반납 관리
# ---------------------------------------------------------
with tab2:
    st.header("⚙️ 관리자 대여 승인 및 불출/반납 관리")

    is_admin = (
        st.session_state.logged_in_user
        and st.session_state.logged_in_user.get("role") == "ADMIN"
    )

    if not is_admin:
        st.info("💡 관리자 계정으로 로그인 시 대여 승인, 불출, 반납 상태를 직접 변경할 수 있음.")

    if not st.session_state.rentals:
        st.info("현재 등록된 대여 신청 내역이 없음.")
    else:
        for idx, rental in enumerate(st.session_state.rentals):
            with st.container():
                st.markdown(f"#### 📌 예약 넘버: `{rental['res_id']}`")

                col_info, col_app, col_chk, col_ret, col_detail = st.columns(
                    [2, 1.2, 1.2, 1.2, 1.2]
                )

                with col_info:
                    st.write(
                        f"**신청자:** {rental['user_name']} (`{rental['user_id']}`)"
                    )
                    st.caption(
                        f"📅 기간: {rental['start_date']} ~ {rental['end_date']}"
                    )

                # 대여 승인
                with col_app:
                    if is_admin:
                        rental["approval"] = st.selectbox(
                            "대여 승인",
                            ["대기", "승인", "거절"],
                            index=["대기", "승인", "거절"].index(
                                rental["approval"]
                            ),
                            key=f"app_{idx}",
                        )
                    else:
                        st.write("**대여 승인**")
                        st.badge(rental["approval"])

                # 불출 완료
                with col_chk:
                    if is_admin:
                        rental["checkout"] = st.selectbox(
                            "불출 완료",
                            ["미불출", "불출 완료"],
                            index=["미불출", "불출 완료"].index(
                                rental["checkout"]
                            ),
                            key=f"chk_{idx}",
                        )
                    else:
                        st.write("**불출 완료**")
                        st.badge(rental["checkout"])

                # 반납 완료
                with col_ret:
                    if is_admin:
                        rental["return_status"] = st.selectbox(
                            "반납 완료",
                            ["미반납", "반납 완료"],
                            index=["미반납", "반납 완료"].index(
                                rental["return_status"]
                            ),
                            key=f"ret_{idx}",
                        )
                    else:
                        st.write("**반납 완료**")
                        st.badge(rental["return_status"])

                # 자세히 보기 (팝업 모달 방식)
                with col_detail:
                    st.write("**상세 보기**")
                    with st.popover("🔍 자세히 보기"):
                        st.markdown(
                            f"**[예약 넘버: {rental['res_id']}]**"
                        )
                        st.write(
                            f"👤 **신청자:** {rental['user_name']} ({rental['user_id']})"
                        )
                        st.write(
                            f"📅 **대여 기간:** {rental['start_date']} ~ {rental['end_date']}"
                        )
                        st.write(f"📝 **사용 목적:** {rental.get('note', '없음')}")
                        st.divider()
                        st.markdown("📋 **대여 기자재 목록:**")
                        for eq in rental["equipments"]:
                            st.write(f"- {eq}")

                st.divider()

# ---------------------------------------------------------
# TAB 3: 대여 일정 현황 및 일정 조정
# ---------------------------------------------------------
with tab3:
    st.header("📅 대여 일정 현황 및 일정 조정")

    if not st.session_state.rentals:
        st.info("등록된 대여 일정이 없음.")
    else:
        df_rentals = pd.DataFrame(st.session_state.rentals)
        df_display = df_rentals[
            [
                "res_id",
                "user_name",
                "user_id",
                "start_date",
                "end_date",
                "approval",
                "checkout",
                "return_status",
            ]
        ]
        df_display.columns = [
            "예약 넘버",
            "신청자 성명",
            "신청자 ID(핸드폰)",
            "시작일",
            "반납 예정일",
            "대여 승인",
            "불출 완료",
            "반납 완료",
        ]

        st.subheader("📊 전체 대여 일정 표")
        st.dataframe(df_display, use_container_width=True)

        if is_admin:
            st.subheader("🛠️ 일정 조정 (관리자 전용)")
            res_list = [r["res_id"] for r in st.session_state.rentals]
            target_res = st.selectbox("일정을 조정할 예약 넘버 선택:", res_list)

            target_item = next(
                r for r in st.session_state.rentals if r["res_id"] == target_res
            )

            c1, c2 = st.columns(2)
            with c1:
                new_start = st.date_input(
                    "변경할 대여 시작일",
                    value=datetime.strptime(
                        target_item["start_date"], "%Y-%m-%d"
                    ).date(),
                    key="mod_start",
                )
            with c2:
                new_end = st.date_input(
                    "변경할 반납 예정일",
                    value=datetime.strptime(
                        target_item["end_date"], "%Y-%m-%d"
                    ).date(),
                    key="mod_end",
                )

            if st.button("일정 변경 적용"):
                target_item["start_date"] = str(new_start)
                target_item["end_date"] = str(new_end)
                st.success(f"예약 넘버 {target_res}의 대여 일정이 정상 수정되었음.")
                st.rerun()
