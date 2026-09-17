from datetime import date, datetime
import re
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 0. 유틸리티 함수 및 상수 정의
# ==========================================
DB_FILE = "rental_system.db"

TIME_SLOTS = [
    "08:00-08:20",
    "09:10-09:20",
    "10:10-10:20",
    "11:10-11:20",
    "12:10-13:00",
    "13:50-14:00",
    "14:50-15:00",
    "15:50-16:00",
    "협의요청",
]


def clean_phone_id(input_str: str) -> str:
    """핸드폰 번호 입력 시 하이픈(-) 및 공백 제거 (admin 계정 예외 처리)"""
    if not input_str:
        return ""
    cleaned = input_str.strip()
    if cleaned.lower() == "admin":
        return "admin"
    return re.sub(r"[^\d]", "", cleaned)


# ==========================================
# 1. SQLite 데이터베이스 영구 저장소 구축
# ==========================================
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """데이터베이스 테이블 생성 및 초기 기본 데이터 시드"""
    conn = get_db()
    cur = conn.cursor()

    # 1) 사용자 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER'
        )
    """)

    # 2) 기자재 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '대여 가능'
        )
    """)

    # 3) 대여 예약 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservation (
            res_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            approval TEXT DEFAULT '대기',
            checkout TEXT DEFAULT '미불출',
            return_status TEXT DEFAULT '미반납',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4) 예약-기자재 매핑 테이블 (1개 예약당 여러 장비)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            res_id TEXT NOT NULL,
            equip_id TEXT NOT NULL,
            FOREIGN KEY (res_id) REFERENCES reservation (res_id) ON DELETE CASCADE,
            FOREIGN KEY (equip_id) REFERENCES equipment (id)
        )
    """)

    # 초기 관리자 계정 생성 (admin / admin123)
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, name, role) VALUES ('admin',"
            " 'admin123', '총괄 관리자', 'ADMIN')"
        )

    # 초기 샘플 기자재 등록
    cur.execute("SELECT COUNT(*) FROM equipment")
    if cur.fetchone()[0] == 0:
        sample_eq = [
            (
                "EQ-101",
                "카메라",
                "Blackmagic Pocket Cinema Camera 6K Pro",
                "대여 가능",
            ),
            ("EQ-102", "카메라", "Sony FX3 시네마 카메라", "대여 가능"),
            (
                "EQ-103",
                "삼각대/그립",
                "Libec 650EX 비디오 삼각대",
                "대여 가능",
            ),
            (
                "EQ-104",
                "삼각대/그립",
                "SmallRig 숄더 리그 키트",
                "대여 가능",
            ),
            (
                "EQ-105",
                "음향",
                "Hollyland Lark M1 무선 마이크",
                "대여 가능",
            ),
            (
                "EQ-106",
                "조명",
                "Amaran 200d LED 지속광 조명",
                "점검 중",
            ),
            ("EQ-107", "기타", "Atomos Ninja V 5인치 모니터", "대여 가능"),
        ]
        cur.executemany(
            "INSERT INTO equipment (id, category, name, status) VALUES (?,"
            " ?, ?, ?)",
            sample_eq,
        )

    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 페이지 설정 및 세션 초기화
# ==========================================
st.set_page_config(
    page_title="전문 기자재 대여 및 통합 일정 관리 시스템 Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None


# DB 조회 유틸리티 함수들
def fetch_all_equipments():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT category, name, id, status FROM equipment ORDER BY category,"
        " name, id",
        conn,
    )
    conn.close()
    return df


def fetch_all_reservations():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservation ORDER BY created_at DESC")
    rows = cur.fetchall()

    rentals = []
    for r in rows:
        res_id = r["res_id"]
        cur.execute(
            """
            SELECT e.id, e.category, e.name, e.status 
            FROM reservation_items ri
            JOIN equipment e ON ri.equip_id = e.id
            WHERE ri.res_id = ?
        """,
            (res_id,),
        )
        eq_rows = cur.fetchall()
        eq_list = [dict(eq) for eq in eq_rows]

        rentals.append({
            "res_id": r["res_id"],
            "user_id": r["user_id"],
            "user_name": r["user_name"],
            "start_date": r["start_date"],
            "end_date": r["end_date"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
            "approval": r["approval"],
            "checkout": r["checkout"],
            "return_status": r["return_status"],
            "note": r["note"],
            "equipments": eq_list,
        })
    conn.close()
    return rentals


# ==========================================
# 3. 사이드바 - 회원 인증 (로그인 / 회원가입)
# ==========================================
st.sidebar.title("🔐 회원 인증 센터")

if st.session_state.logged_in_user is None:
    tab_login, tab_register = st.sidebar.tabs(["🔑 로그인", "📝 회원가입"])

    with tab_login:
        st.subheader("로그인")
        raw_login_id = st.text_input(
            "아이디 (핸드폰 번호)",
            placeholder="010-1234-5678 또는 01012345678",
            key="login_id",
        )
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")

        if st.button("로그인", use_container_width=True, type="primary"):
            clean_id = clean_phone_id(raw_login_id)
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (clean_id, login_pw),
            )
            user_row = cur.fetchone()
            conn.close()

            if user_row:
                st.session_state.logged_in_user = {
                    "username": user_row["username"],
                    "name": user_row["name"],
                    "phone": user_row["username"],
                    "role": user_row["role"],
                }
                st.success(f"{user_row['name']}님, 환영합니다.")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    with tab_register:
        st.subheader("신규 회원가입")
        raw_reg_phone = st.text_input(
            "핸드폰 번호 (아이디)", placeholder="010-1234-5678", key="reg_phone"
        )
        reg_name = st.text_input("성명", placeholder="홍길동", key="reg_name")
        reg_pw = st.text_input("비밀번호", type="password", key="reg_pw")
        reg_pw_confirm = st.text_input(
            "비밀번호 확인", type="password", key="reg_pw_confirm"
        )

        if st.button("회원가입 완료", use_container_width=True):
            clean_reg_phone = clean_phone_id(raw_reg_phone)
            if not clean_reg_phone or not reg_name or not reg_pw:
                st.error("모든 입력 항목을 올바르게 작성해 주세요.")
            elif (
                not clean_reg_phone.isdigit() and clean_reg_phone != "admin"
            ):
                st.error("핸드폰 번호는 숫자 형식으로 입력해 주세요.")
            elif reg_pw != reg_pw_confirm:
                st.error("비밀번호 확인이 일치하지 않습니다.")
            else:
                conn = get_db()
                cur = conn.cursor()
                try:
                    cur.execute(
                        "INSERT INTO users (username, password, name, role)"
                        " VALUES (?, ?, ?, 'USER')",
                        (clean_reg_phone, reg_pw, reg_name),
                    )
                    conn.commit()
                    st.success(
                        "회원가입이 완료되었습니다. 로그인 탭에서 로그인해"
                        " 주세요."
                    )
                except sqlite3.IntegrityError:
                    st.error("이미 가입된 핸드폰 번호(아이디)입니다.")
                finally:
                    conn.close()

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

# ==========================================
# 4. 메인 대시보드 탭 구성
# ==========================================
st.title("🎥 전문 기자재 대여 및 통합 일정 관리 시스템 Pro")

is_admin = (
    st.session_state.logged_in_user
    and st.session_state.logged_in_user.get("role") == "ADMIN"
)

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
        st.warning(
            "⚠️ 장비 대여 신청을 이용하시려면 먼저 사이드바에서 로그인해"
            " 주세요."
        )
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

        eq_df = fetch_all_equipments()
        eq_map = {}
        disabled_items = []

        for _, item in eq_df.iterrows():
            label = f"[{item['id']}] [{item['category']}] {item['name']} ({item['status']})"
            if item["status"] == "대여 가능":
                eq_map[label] = item.to_dict()
            else:
                disabled_items.append(label)

        selected_display_names = st.multiselect(
            "대여할 장비를 선택해 주세요 (대여 불가능한 장비는 목록에서"
            " 제외됩니다):",
            options=list(eq_map.keys()),
            placeholder="장비를 선택해 주세요...",
        )

        if disabled_items:
            st.caption(
                "⚠️ 현재 점검/수리/불가로 신청 대상에서 제외된 장비:"
                f" {', '.join(disabled_items)}"
            )

        st.subheader("📅 사용 기간 및 교시별 지정 시간 선택")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_d = st.date_input("대여 시작일", value=date.today())
            start_t = st.selectbox("대여 희망 시각", TIME_SLOTS, index=0)
        with col_d2:
            end_d = st.date_input("반납 예정일", value=date.today())
            end_t = st.selectbox("반납 예정 시각", TIME_SLOTS, index=7)

        note = st.text_area(
            "사용 목적 및 기타 요청사항", placeholder="예: 단편영화 제작 촬영"
        )

        if st.button(
            "🚀 장비 대여 신청서 제출",
            type="primary",
            use_container_width=True,
        ):
            if not selected_display_names:
                st.error("대여할 장비를 최소 1개 이상 선택해 주세요.")
            elif start_d > end_d:
                st.error("반납 예정일이 대여 시작일보다 빠를 수 없습니다.")
            else:
                selected_equip_objs = [
                    eq_map[name] for name in selected_display_names
                ]

                # 중복 예약 DB 검증
                rentals = fetch_all_reservations()
                overlap_conflict = False
                conflict_details = ""
                s_str, e_str = str(start_d), str(end_d)

                for r in rentals:
                    if r["approval"] in ["승인", "대기"]:
                        if not (
                            r["end_date"] < s_str or r["start_date"] > e_str
                        ):
                            r_eq_ids = [eq["id"] for eq in r["equipments"]]
                            for req_eq in selected_equip_objs:
                                if req_eq["id"] in r_eq_ids:
                                    overlap_conflict = True
                                    conflict_details = (
                                        f"장비 [{req_eq['id']}]는 해당 기간에 이미"
                                        " 기존"
                                        f" 예약({r['user_name']}, {r['start_date']}~{r['end_date']})이"
                                        " 존재합니다."
                                    )
                                    break

                if overlap_conflict:
                    st.error(f"❌ 대여 신청 불가: {conflict_details}")
                else:
                    res_no = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO reservation 
                        (res_id, user_id, user_name, start_date, end_date, start_time, end_time, approval, checkout, return_status, note)
                        VALUES (?, ?, ?, ?, ?, ?, ?, '대기', '미불출', '미반납', ?)
                    """,
                        (
                            res_no,
                            app_id,
                            app_name,
                            s_str,
                            e_str,
                            start_t,
                            end_t,
                            note,
                        ),
                    )

                    for req_eq in selected_equip_objs:
                        cur.execute(
                            "INSERT INTO reservation_items (res_id, equip_id)"
                            " VALUES (?, ?)",
                            (res_no, req_eq["id"]),
                        )

                    conn.commit()
                    conn.close()

                    st.balloons()
                    st.success(
                        "대여 신청이 성공적으로 완료되었습니다! (예약 번호:"
                        f" {res_no})"
                    )

# ---------------------------------------------------------
# TAB 2: 관리자 승인 및 불출/반납 관리
# ---------------------------------------------------------
with tab2:
    st.header("⚙️ 관리자 대여 승인 및 불출/반납 관리")

    if not is_admin:
        st.info(
            "💡 관리자 계정으로 로그인하시면 대여 승인, 불출, 반납 상태를"
            " 직접 변경하실 수 있습니다."
        )

    rentals = fetch_all_reservations()

    if not rentals:
        st.info("현재 등록된 대여 신청 내역이 없습니다.")
    else:
        for idx, rental in enumerate(rentals):
            with st.container():
                st.markdown(f"#### 📌 예약 번호: `{rental['res_id']}`")

                col_info, col_app, col_chk, col_ret = st.columns(
                    [2.5, 1.2, 1.2, 1.2]
                )

                with col_info:
                    st.write(
                        f"**신청자:** {rental['user_name']} (`{rental['user_id']}`)"
                    )
                    st.caption(
                        f"📅 일시: {rental['start_date']} [{rental.get('start_time', '08:00-08:20')}] ~ {rental['end_date']} [{rental.get('end_time', '15:50-16:00')}]"
                    )

                with col_app:
                    if is_admin:
                        new_app = st.selectbox(
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
                        new_app = rental["approval"]

                with col_chk:
                    if is_admin:
                        new_chk = st.selectbox(
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
                        new_chk = rental["checkout"]

                with col_ret:
                    if is_admin:
                        new_ret = st.selectbox(
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
                        new_ret = rental["return_status"]

                # 관리자 변경 사항 DB 저장
                if is_admin and (
                    new_app != rental["approval"]
                    or new_chk != rental["checkout"]
                    or new_ret != rental["return_status"]
                ):
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        UPDATE reservation 
                        SET approval = ?, checkout = ?, return_status = ? 
                        WHERE res_id = ?
                    """,
                        (new_app, new_chk, new_ret, rental["res_id"]),
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()

                with st.expander(
                    f"🔍 [상세보기] 예약 번호 {rental['res_id']} 대여 내역 및"
                    " 기자재 명세서 (카테고리별 분류)",
                    expanded=False,
                ):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**📄 기본 대여 정보**")
                        st.write(
                            f"- **신청자:** {rental['user_name']}"
                            f" ({rental['user_id']})"
                        )
                        st.write(
                            f"- **대여 일시:** {rental['start_date']}"
                            f" [{rental.get('start_time', '')}]"
                        )
                        st.write(
                            f"- **반납 일시:** {rental['end_date']}"
                            f" [{rental.get('end_time', '')}]"
                        )
                        st.write(f"- **사용 목적:** {rental.get('note', '없음')}")

                    with c2:
                        st.markdown(
                            "**📋 카테고리별 신청 기자재 명세서**"
                        )

                        df_eq = pd.DataFrame(rental["equipments"])
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
# TAB 3: 대여 일정 현황 및 조정
# ---------------------------------------------------------
with tab3:
    st.header("📅 대여 일정 현황 및 일정 조정")

    rentals = fetch_all_reservations()

    if not rentals:
        st.info("등록된 대여 일정이 없습니다.")
    else:
        flat_rentals = []
        for r in rentals:
            eq_names = [
                f"[{eq['category']}] {eq['name']}" for eq in r["equipments"]
            ]
            flat_rentals.append({
                "res_id": r["res_id"],
                "user_name": r["user_name"],
                "user_id": r["user_id"],
                "equipments_summary": ", ".join(eq_names),
                "start_time_full": (
                    f"{r['start_date']} ({r.get('start_time', '')})"
                ),
                "end_time_full": f"{r['end_date']} ({r.get('end_time', '')})",
                "approval": r["approval"],
                "checkout": r["checkout"],
                "return_status": r["return_status"],
            })

        df_rentals = pd.DataFrame(flat_rentals)
        df_display = df_rentals[[
            "res_id",
            "user_name",
            "user_id",
            "equipments_summary",
            "start_time_full",
            "end_time_full",
            "approval",
            "checkout",
            "return_status",
        ]]
        df_display.columns = [
            "예약 번호",
            "신청자 성명",
            "신청자 ID(핸드폰)",
            "대여 장비 요약",
            "대여 일시",
            "반납 일시",
            "대여 승인",
            "불출 완료",
            "반납 완료",
        ]

        st.subheader("📊 전체 대여 일정 표")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        csv_data = df_display.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 대여 현황 CSV 엑셀 다운로드",
            data=csv_data,
            file_name=f"rental_status_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        if is_admin:
            st.divider()
            st.subheader("🛠️ 일정 조정 (관리자 전용)")
            res_list = [r["res_id"] for r in rentals]
            target_res = st.selectbox(
                "일정을 조정할 예약 번호를 선택해 주세요:", res_list
            )

            target_item = next(
                r for r in rentals if r["res_id"] == target_res
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
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE reservation SET start_date = ?, end_date = ? WHERE"
                    " res_id = ?",
                    (str(new_start), str(new_end), target_res),
                )
                conn.commit()
                conn.close()
                st.success(
                    f"예약 번호 {target_res}의 대여 일정이 성공적으로"
                    " 수정되었습니다."
                )
                st.rerun()

# ---------------------------------------------------------
# TAB 4: 장비 등록 및 관리
# ---------------------------------------------------------
with tab4:
    st.header("📦 장비 등록 및 관리 (관리자 전용)")

    if not is_admin:
        st.warning(
            "⚠️ 장비 등록 및 관리는 관리자 계정으로 로그인하셔야 접근이"
            " 가능합니다."
        )
    else:
        st.subheader(
            "➕ 신규 기자재 등록 (입력 순서: 1. 카테고리 → 2. 장비명 → 3."
            " 일련번호)"
        )
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1:
            new_cat = st.selectbox(
                "1. 카테고리", ["카메라", "음향", "조명", "삼각대/그립", "기타"]
            )
        with col_e2:
            new_name = st.text_input("2. 장비명", placeholder="예: Sony FX3")
        with col_e3:
            new_id = st.text_input(
                "3. 일련번호 (ID)", placeholder="예: EQ-108"
            )
        with col_e4:
            new_status = st.selectbox(
                "4. 초기 장비 상태",
                ["대여 가능", "점검 중", "수리 중", "폐기/불가"],
            )

        if st.button("기자재 등록 완료", type="primary"):
            if not new_cat or not new_id or not new_name:
                st.error("모든 항목을 입력해 주세요.")
            else:
                conn = get_db()
                cur = conn.cursor()
                try:
                    cur.execute(
                        "INSERT INTO equipment (id, category, name, status)"
                        " VALUES (?, ?, ?, ?)",
                        (
                            new_id.strip(),
                            new_cat.strip(),
                            new_name.strip(),
                            new_status,
                        ),
                    )
                    conn.commit()
                    st.success(
                        f"신규 기자재 [{new_id.strip()}] {new_name.strip()}"
                        " 등록이 완료되었습니다."
                    )
                except sqlite3.IntegrityError:
                    st.error(
                        "이미 존재하는 일련번호(ID)입니다. 다른 일련번호를"
                        " 입력해 주세요."
                    )
                finally:
                    conn.close()
                    st.rerun()

        st.divider()

        st.subheader("📋 등록 기자재 목록 및 상태 즉시 수정")
        st.caption(
            "💡 '장비 상태' 셀을 직접 선택하여 변경하시면 DB에 실시간으로"
            " 반영됩니다."
        )

        df_eq_manage = fetch_all_equipments()
        if not df_eq_manage.empty:
            df_eq_manage = df_eq_manage[["category", "name", "id", "status"]]
            df_eq_manage.columns = [
                "카테고리 (분류)",
                "장비명",
                "일련번호 (ID)",
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
                disabled=["카테고리 (분류)", "장비명", "일련번호 (ID)"],
                use_container_width=True,
                hide_index=True,
                key="eq_editor",
            )

            # DB 상태 동기화
            conn = get_db()
            cur = conn.cursor()
            for _, row in edited_df.iterrows():
                cur.execute(
                    "UPDATE equipment SET status = ? WHERE id = ?",
                    (row["장비 상태"], row["일련번호 (ID)"]),
                )
            conn.commit()
            conn.close()

            st.divider()

            st.subheader("🗑️ 등록 기자재 삭제")

            all_eqs = fetch_all_equipments().to_dict("records")
            eq_del_options = {
                f"[{eq['id']}] {eq['name']} ({eq['category']})": eq["id"]
                for eq in all_eqs
            }

            if eq_del_options:
                selected_del_label = st.selectbox(
                    "삭제할 기자재를 선택해 주세요 (일련번호 및 장비명"
                    " 포함):",
                    options=list(eq_del_options.keys()),
                )

                if st.button("선택 장비 삭제"):
                    target_id = eq_del_options[selected_del_label]
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM equipment WHERE id = ?", (target_id,)
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"장비 {selected_del_label} 삭제가 완료되었습니다."
                    )
                    st.rerun()

# ---------------------------------------------------------
# TAB 5: 회원 정보 관리
# ---------------------------------------------------------
with tab5:
    st.header("👥 회원 정보 관리 (관리자 전용)")

    if not is_admin:
        st.warning(
            "⚠️ 회원 정보 관리는 관리자 계정으로 로그인하셔야 접근이"
            " 가능합니다."
        )
    else:
        st.subheader("📋 전체 회원 현황")

        conn = get_db()
        df_users = pd.read_sql_query(
            "SELECT username AS '아이디 (핸드폰)', name AS '성명', role AS '권한',"
            " password AS '비밀번호' FROM users",
            conn,
        )
        conn.close()

        st.dataframe(df_users, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🛠️ 회원 비밀번호 변경 및 회원 삭제")

        user_list = df_users["아이디 (핸드폰)"].tolist()
        target_user_id = st.selectbox(
            "관리할 대상 회원을 선택해 주세요 (아이디):", user_list
        )

        if target_user_id:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username = ?", (target_user_id,)
            )
            t_user = cur.fetchone()
            conn.close()

            st.info(
                f"선택 회원: **{t_user['name']}** (`{target_user_id}`) | 권한:"
                f" `{t_user['role']}`"
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
                        st.error("변경할 비밀번호를 입력해 주세요.")
                    else:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE users SET password = ? WHERE username = ?",
                            (mod_pw, target_user_id),
                        )
                        conn.commit()
                        conn.close()
                        st.success(
                            f"회원 `{target_user_id}`의 비밀번호 변경이"
                            " 성공적으로 완료되었습니다."
                        )
                        st.rerun()

            with col_m2:
                st.markdown("**🗑️ 회원 삭제**")
                st.caption("주의: 회원 삭제 시 복구할 수 없습니다.")
                if st.button("선택 회원 삭제", type="primary"):
                    if (
                        target_user_id
                        == st.session_state.logged_in_user["phone"]
                    ):
                        st.error(
                            "현재 로그인 중인 본인 관리자 계정은 삭제할 수"
                            " 없습니다."
                        )
                    elif target_user_id == "admin":
                        st.error(
                            "최초 시스템 관리자 계정(admin)은 삭제할 수"
                            " 없습니다."
                        )
                    else:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            "DELETE FROM users WHERE username = ?",
                            (target_user_id,),
                        )
                        conn.commit()
                        conn.close()
                        st.success(
                            f"회원 `{target_user_id}` 삭제가 완료되었습니다."
                        )
                        st.rerun()
