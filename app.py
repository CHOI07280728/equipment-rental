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

# 기자재 데이터베이스 (장비 상태 속성 포함)
if "equipments" not in st.session_state:
    st.session_state.equipments = [
        {
            "id": "EQ-101",
            "category": "카메라",
            "name": "Blackmagic Pocket Cinema Camera 6K Pro",
            "status": "대여 가능",
        },
        {
            "id": "EQ-102",
            "category": "카메라",
            "name": "Sony FX3 시네마 카메라",
            "status": "대여 가능",
        },
        {
            "id": "EQ-103",
            "category": "삼각대",
            "name": "Libec 650EX 비디오 삼각대",
            "status": "대여 가능",
        },
        {
            "id": "EQ-104",
            "category": "액세서리",
            "name": "SmallRig 숄더 리그 키트",
            "status": "대여 가능",
        },
        {
            "id": "EQ-105",
            "category": "음향",
            "name": "Hollyland Lark M1 무선 마이크",
            "status": "대여 가능",
        },
        {
            "id": "EQ-106",
            "category": "조명",
            "name": "Amaran 200d LED 지속광 조명",
            "status": "점검 중",
        },
        {
            "id": "EQ-107",
            "category": "디스플레이",
            "name": "Atomos Ninja V 5인치 모니터",
            "status": "대여 가능",
        },
    ]

if "rentals" not in st.session_state:
    st.session_state.rentals = [
        {
            "res_id": "RES-20260916-001",
            "user_name": "홍길동",
            "user_id": "01012345678",
            "equipments": [
                {
                    "id": "EQ-101",
                    "category": "카메라",
                    "name": "Blackmagic Pocket Cinema Camera 6K Pro",
                    "status": "대여 중",
                },
                {
                    "id": "EQ-103",
                    "category": "삼각대",
                    "name": "Libec 650EX 비디오 삼각대",
                    "status": "대여 중",
                },
                {
                    "id": "EQ-105",
                    "category": "음향",
                    "name": "Hollyland Lark M1 무선 마이크",
                    "status": "대여 중",
                },
            ],
            "start_date": "2026-09-16",
            "end_date": "2026-09-18",
            "approval": "승인",
            "checkout": "불출 완료",
            "return_status": "미반납",
            "note": "단편영화 촬영 지원",
        }
    ]

# 3. 사이드바 - 회원 인증 (로그인 / 회원가입)
st.sidebar.title("🔐 회원 인증 Center")

if st.session_state.logged_in_user is None:
    tab_login, tab_register = st.sidebar.tabs(["🔑 로그인", "📝 회원가입"])

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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 장비 대여 신청서",
    "⚙️ 관리자 승인 및 불출/반납 관리",
    "📅 대여 일정 현황 및 조정",
    "📦 장비 등록 및 관리",
    "👥 회원 정보 관리",
])

# ---------------------------------------------------------
# TAB 1: 장비 대여 신청서
# ---------------------------------------------------------
with tab1:
    st.header("📝 장비 대여 신청서 작성")

    if st.session_state.logged_in_user is None:
        st.warning("⚠️ 장비 대여 신청을 위해 먼저 사이드바에서 로그인해줌.")
    else:
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

        st.subheader("📦 대여 기자재 선택 (일련번호 및 실시간 상태 표기)")

        eq_map = {
            f"[{item['id']}] [{item['category']}] {item['name']} ({item.get('status', '대여 가능')})": item
            for item in st.session_state.equipments
        }

        selected_display_names = st.multiselect(
            "대여할 장비를 선택해줌 (일련번호 포함):",
            options=list(eq_map.keys()),
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
            if not selected_display_names:
                st.error("대여할 장비를 1개 이상 선택해줌.")
            elif start_d > end_d:
                st.error("반납 예정일이 대여 시작일보다 빠를 수 없음.")
            else:
                selected_equip_objs = [
                    eq_map[name] for name in selected_display_names
                ]
                res_no = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                new_item = {
                    "res_id": res_no,
                    "user_name": app_name,
                    "user_id": app_id,
                    "equipments": selected_equip_objs,
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
# TAB 2: 관리자 대여 승인 및 불출/반납 관리 (카테고리별 그룹화 화면 개선)
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

                col_info, col_app, col_chk, col_ret = st.columns(
                    [2.5, 1.2, 1.2, 1.2]
                )

                with col_info:
                    st.write(
                        f"**신청자:** {rental['user_name']} (`{rental['user_id']}`)"
                    )
                    st.caption(
                        f"📅 기간: {rental['start_date']} ~ {rental['end_date']}"
                    )

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

                # [개선] 카테고리별로 기자재를 그룹화하여 깔끔하게 디스플레이
                with st.expander(
                    f"🔍 [상세보기] 예약 넘버 {rental['res_id']} 대여 내역 및 기자재 명세서 (카테고리별 분류)",
                    expanded=False,
                ):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**📄 기본 대여 정보**")
                        st.write(
                            f"- **신청자:** {rental['user_name']} ({rental['user_id']})"
                        )
                        st.write(
                            f"- **대여 기간:** {rental['start_date']} ~ {rental['end_date']}"
                        )
                        st.write(f"- **사용 목적:** {rental.get('note', '없음')}")

                    with c2:
                        st.markdown(
                            "**📋 카테고리별 신청 기자재 명세서**"
                        )

                        eq_list = rental["equipments"]
                        formatted_eqs = []

                        for eq in eq_list:
                            if isinstance(eq, dict):
                                formatted_eqs.append(eq)
                            else:
                                formatted_eqs.append(
                                    {
                                        "category": "기타",
                                        "id": "-",
                                        "name": str(eq),
                                        "status": "정보 없음",
                                    }
                                )

                        df_eq = pd.DataFrame(formatted_eqs)
                        if not df_eq.empty:
                            categories = df_eq["category"].unique()
                            for cat in categories:
                                st.markdown(f"##### 📁 {cat}")
                                sub_df = df_eq[df_eq["category"] == cat][
                                    ["id", "name", "status"]
                                ]
                                sub_df.columns = [
                                    "일련번호 (ID)",
                                    "기자재명",
                                    "현재 상태",
                                ]
                                st.dataframe(
                                    sub_df,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                st.divider()

# ---------------------------------------------------------
# TAB 3: 대여 일정 현황 및 일정 조정
# ---------------------------------------------------------
with tab3:
    st.header("📅 대여 일정 현황 및 일정 조정")

    if not st.session_state.rentals:
        st.info("등록된 대여 일정이 없음.")
    else:
        flat_rentals = []
        for r in st.session_state.rentals:
            eq_names = [
                f"[{eq['category']}] {eq['name']}"
                if isinstance(eq, dict)
                else str(eq)
                for eq in r["equipments"]
            ]
            flat_rentals.append(
                {
                    "res_id": r["res_id"],
                    "user_name": r["user_name"],
                    "user_id": r["user_id"],
                    "equipments_summary": ", ".join(eq_names),
                    "start_date": r["start_date"],
                    "end_date": r["end_date"],
                    "approval": r["approval"],
                    "checkout": r["checkout"],
                    "return_status": r["return_status"],
                }
            )

        df_rentals = pd.DataFrame(flat_rentals)
        df_display = df_rentals[
            [
                "res_id",
                "user_name",
                "user_id",
                "equipments_summary",
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
            "대여 장비 요약",
            "시작일",
            "반납 예정일",
            "대여 승인",
            "불출 완료",
            "반납 완료",
        ]

        st.subheader("📊 전체 대여 일정 표")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

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

# ---------------------------------------------------------
# TAB 4: 장비 등록 및 관리 (상태 즉시 수정 & 삭제 가독성 고도화)
# ---------------------------------------------------------
with tab4:
    st.header("📦 장비 등록 및 관리 (관리자 전용)")

    if not is_admin:
        st.warning("⚠️ 장비 등록 및 관리는 관리자 계정으로 로그인해야 접근 가능함.")
    else:
        st.subheader("➕ 신규 기자재 등록")
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1:
            new_cat = st.text_input(
                "카테고리 (분류)", placeholder="예: 카메라, 조명, 음향"
            )
        with col_e2:
            new_id = st.text_input(
                "일련번호 (ID)", placeholder="예: EQ-108"
            )
        with col_e3:
            new_name = st.text_input(
                "기자재명", placeholder="예: Canon EOS R5"
            )
        with col_e4:
            new_status = st.selectbox(
                "초기 장비 상태",
                ["대여 가능", "점검 중", "수리 중", "폐기/불가"],
            )

        if st.button("장비 등록 완료", type="primary"):
            if not new_cat or not new_id or not new_name:
                st.error("카테고리, 일련번호, 기자재명을 모두 입력해줌.")
            elif any(
                eq["id"] == new_id.strip() for eq in st.session_state.equipments
            ):
                st.error("이미 존재하는 일련번호(ID)임. 다른 일련번호를 사용해줌.")
            else:
                st.session_state.equipments.append(
                    {
                        "id": new_id.strip(),
                        "category": new_cat.strip(),
                        "name": new_name.strip(),
                        "status": new_status,
                    }
                )
                st.success(
                    f"신규 장비 [{new_id.strip()}] {new_name.strip()} 등록이 완료되었음."
                )
                st.rerun()

        st.divider()

        # [개선 1] 상태 컬럼 실시간 수정 가능한 st.data_editor 도입
        st.subheader("📋 등록된 기자재 목록 및 상태 즉각 수정")
        st.caption("💡 아래 표의 '장비 상태' 셀을 클릭하면 즉시 상태를 변경할 수 있음.")

        df_eq_manage = pd.DataFrame(st.session_state.equipments)
        if not df_eq_manage.empty:
            df_eq_manage = df_eq_manage[["category", "id", "name", "status"]]
            df_eq_manage.columns = [
                "카테고리 (분류)",
                "일련번호 (ID)",
                "기자재명",
                "장비 상태",
            ]

            edited_df = st.data_editor(
                df_eq_manage,
                column_config={
                    "장비 상태": st.column_config.SelectboxColumn(
                        "장비 상태",
                        options=["대여 가능", "점검 중", "수리 중", "폐기/불가"],
                        required=True,
                    )
                },
                disabled=["카테고리 (분류)", "일련번호 (ID)", "기자재명"],
                use_container_width=True,
                hide_index=True,
                key="eq_editor",
            )

            # 변경된 데이터 세션 상태 반영
            updated_equipments = []
            for _, row in edited_df.iterrows():
                updated_equipments.append(
                    {
                        "id": row["일련번호 (ID)"],
                        "category": row["카테고리 (분류)"],
                        "name": row["기자재명"],
                        "status": row["장비 상태"],
                    }
                )
            st.session_state.equipments = updated_equipments

            st.divider()

            # [개선 2] 삭제 시 일련번호 + 기자재명 + 카테고리가 모두 표기되는 셀렉트박스
            st.subheader("🗑️ 등록 장비 삭제")

            eq_del_options = {
                f"[{eq['id']}] {eq['name']} ({eq['category']})": eq["id"]
                for eq in st.session_state.equipments
            }

            if eq_del_options:
                selected_del_label = st.selectbox(
                    "삭제할 장비 선택 (일련번호 및 기자재명 포함):",
                    options=list(eq_del_options.keys()),
                )

                if st.button("선택 장비 삭제"):
                    target_id = eq_del_options[selected_del_label]
                    st.session_state.equipments = [
                        eq
                        for eq in st.session_state.equipments
                        if eq["id"] != target_id
                    ]
                    st.success(f"장비 {selected_del_label} 삭제가 완료되었음.")
                    st.rerun()

# ---------------------------------------------------------
# TAB 5: 회원 정보 관리
# ---------------------------------------------------------
with tab5:
    st.header("👥 회원 정보 관리 (관리자 전용)")

    if not is_admin:
        st.warning("⚠️ 회원 정보 관리는 관리자 계정으로 로그인해야 접근 가능함.")
    else:
        st.subheader("📋 전체 회원 현황")

        user_list_data = []
        for uid, uinfo in st.session_state.users.items():
            user_list_data.append(
                {
                    "아이디 (핸드폰)": uid,
                    "성명": uinfo["name"],
                    "권한": uinfo.get("role", "USER"),
                    "비밀번호": uinfo["password"],
                }
            )

        df_users = pd.DataFrame(user_list_data)
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🛠️ 회원 비밀번호 변경 및 회원 삭제")

        target_user_id = st.selectbox(
            "관리할 대상 회원 선택 (아이디):",
            list(st.session_state.users.keys()),
        )

        if target_user_id:
            target_user_info = st.session_state.users[target_user_id]
            st.info(
                f"선택 회원: **{target_user_info['name']}** (`{target_user_id}`) | 권한: `{target_user_info.get('role', 'USER')}`"
            )

            col_m1, col_m2 = st.columns(2)

            with col_m1:
                st.markdown("**🔑 비밀번호 변경**")
                mod_pw = st.text_input(
                    "새 비밀번호 입력",
                    type="password",
                    key="admin_mod_pw_input",
                )
                if st.button("비밀번호 변경 적용"):
                    if not mod_pw:
                        st.error("변경할 비밀번호를 입력해줌.")
                    else:
                        st.session_state.users[target_user_id][
                            "password"
                        ] = mod_pw
                        st.success(
                            f"회원 `{target_user_id}`의 비밀번호 변경이 완료되었음."
                        )
                        st.rerun()

            with col_m2:
                st.markdown("**🗑️ 회원 삭제**")
                st.caption("주의: 회원 삭제 시 복구할 수 없음.")
                if st.button("선택 회원 삭제", type="primary"):
                    if (
                        target_user_id
                        == st.session_state.logged_in_user["phone"]
                    ):
                        st.error("현재 로그인 중인 관리자 본인 계정은 삭제할 수 없음.")
                    else:
                        del st.session_state.users[target_user_id]
                        st.success(f"회원 `{target_user_id}` 삭제가 완료되었음.")
                        st.rerun()
