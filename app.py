import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date, datetime, timedelta

# ==========================================
# 0. 상수 정의 (대여/반납 지정 시간 옵션)
# ==========================================
TIME_SLOTS = [
    "08:00-08:20",
    "09:10-09:20",
    "10:10-10:20",
    "11:10-11:20",
    "12:10-13:00",
    "13:50-14:00",
    "14:50-15:00",
    "15:50-16:00",
    "협의요청"
]

# ==========================================
# 1. DB 및 보안 관련 함수 (SHA-256 Hashing)
# ==========================================
DB_FILE = "rental_system.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """비밀번호 SHA-256 단방향 해싱"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    """데이터베이스, 기본 계정 및 자동 컬럼 마이그레이션 초기화"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1) 사용자 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER'
        )
    ''')
    
    # 2) 기자재 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'AVAILABLE'
        )
    ''')
    
    # 3) 대여 예약 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equip_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            start_time TEXT DEFAULT '08:00-08:20',
            end_time TEXT DEFAULT '15:50-16:00',
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (equip_id) REFERENCES equipment (id),
            FOREIGN KEY (user_id) REFERENCES users (username)
        )
    ''')
    
    # 기존 DB 파일과의 호환성을 위한 마이그레이션 (컬럼 존재 유무 확인 후 추가)
    cursor.execute("PRAGMA table_info(reservation)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'start_time' not in columns:
        cursor.execute("ALTER TABLE reservation ADD COLUMN start_time TEXT DEFAULT '08:00-08:20'")
    if 'end_time' not in columns:
        cursor.execute("ALTER TABLE reservation ADD COLUMN end_time TEXT DEFAULT '15:50-16:00'")

    # 초기 시스템 관리자 계정 생성 (최초 1회)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "시스템 관리자", "ADMIN")
        )
    
    # 단일 일련번호 샘플 등록
    cursor.execute("SELECT COUNT(*) FROM equipment")
    if cursor.fetchone()[0] == 0:
        sample_equipments = [
            ("26fx01", "Sony FX3 카메라", "카메라")
        ]
        cursor.executemany("INSERT INTO equipment (id, name, category) VALUES (?, ?, ?)", sample_equipments)
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. 회원 및 예약 관리 CRUD 함수
# ==========================================
def login_user(username, password):
    """사용자 인증 처리"""
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    cursor.execute("SELECT username, name, role FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"username": user["username"], "name": user["name"], "role": user["role"]}
    return None

def register_user(username, password, name):
    """일반 사용자 회원가입"""
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, 'USER')",
            (username, hashed_pw, name)
        )
        conn.commit()
        conn.close()
        return True, "회원가입이 성공적으로 완료되었음."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "이미 사용 중인 아이디임."

def update_user_password(username, new_password):
    """관리자용 비밀번호 변경"""
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(new_password)
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
    conn.commit()
    conn.close()

def delete_user(username):
    """관리자용 계정 삭제"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def check_overlap(equip_id, start_str, end_str):
    """기간 중복 예약 검증"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT * FROM reservation 
        WHERE equip_id = ? 
          AND status IN ('APPROVED', 'PENDING', 'RENTED')
          AND (start_date <= ? AND end_date >= ?)
    '''
    cursor.execute(query, (equip_id, end_str, start_str))
    conflicts = cursor.fetchall()
    conn.close()
    return len(conflicts) == 0, conflicts

# ==========================================
# 3. 사이드바 및 인증 UI
# ==========================================
st.set_page_config(page_title="장비 대여 관리 시스템 Pro", layout="wide")

if "user_info" not in st.session_state:
    st.session_state.user_info = None

if st.session_state.user_info is None:
    st.sidebar.title("🔐 접속 인증")
    auth_mode = st.sidebar.radio("서비스 이용 모드", ["로그인", "회원가입"])
    
    if auth_mode == "로그인":
        with st.sidebar.form("login_form"):
            input_user = st.text_input("아이디 (ID)")
            input_pw = st.text_input("비밀번호", type="password")
            submit_login = st.form_submit_button("로그인")
            
            if submit_login:
                user = login_user(input_user, input_pw)
                if user:
                    st.session_state.user_info = user
                    st.sidebar.success(f"{user['name']}님 환영함.")
                    st.rerun()
                else:
                    st.sidebar.error("아이디 또는 비밀번호가 올바르지 않음.")
                    
    elif auth_mode == "회원가입":
        with st.sidebar.form("signup_form"):
            new_user = st.text_input("사용할 아이디 (ID)")
            new_pw = st.text_input("비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")
            new_name = st.text_input("성명 (이름)")
            submit_signup = st.form_submit_button("회원가입 완료")
            
            if submit_signup:
                if not (new_user and new_pw and new_name):
                    st.sidebar.warning("모든 항목을 입력해야 함.")
                elif new_pw != new_pw_confirm:
                    st.sidebar.error("비밀번호가 일치하지 않음.")
                else:
                    success, msg = register_user(new_user, new_pw, new_name)
                    if success:
                        st.sidebar.success(msg)
                    else:
                        st.sidebar.error(msg)

    st.title("📹 장비 대여 및 일정 관리 시스템 Pro")
    st.info("💡 사이드바에서 로그인 후 사용 가능함. 계정이 없다면 회원가입을 먼저 진행해주기 바람.")
    st.stop()

else:
    user_info = st.session_state.user_info
    role_badge = "👑 관리자" if user_info["role"] == "ADMIN" else "👤 일반 사용자"
    st.sidebar.markdown(f"**접속자:** {user_info['name']} (`{user_info['username']}`)")
    st.sidebar.markdown(f"**권한:** {role_badge}")
    
    if st.sidebar.button("로그아웃"):
        st.session_state.user_info = None
        st.rerun()

# ==========================================
# 4. 메인 대시보드 (Tabs)
# ==========================================
st.title("📹 장비 대여 및 일정 관리 시스템 Pro")

if user_info["role"] == "ADMIN":
    tabs = st.tabs(["📋 기자재 관리", "📝 대여 신청", "⚙️ 관리자 대여 승인/불출", "📅 전체 일정 현황", "👥 계정 관리"])
else:
    tabs = st.tabs(["📋 기자재 목록", "📝 대여 신청", "📜 내 신청 내역", "📅 전체 일정 현황"])

# ------------------------------------------
# TAB 1: 보유 기자재 목록 & 신규 등록 (순서: 카테고리 -> 장비명 -> 일련번호)
# ------------------------------------------
with tabs[0]:
    st.subheader("보유 기자재 목록")
    conn = get_db_connection()
    df_eq = pd.read_sql_query(
        "SELECT category AS '카테고리', name AS '장비명', id AS '일련번호', status AS '상태' FROM equipment ORDER BY category, name, id", 
        conn
    )
    conn.close()
    
    df_eq['상태'] = df_eq['상태'].replace({'AVAILABLE': '🟢 대여 가능', 'RENTED': '🔴 대여중 (불출됨)'})
    st.dataframe(df_eq, use_container_width=True)
    
    if user_info["role"] == "ADMIN":
        st.divider()
        st.subheader("➕ 신규 기자재 등록 (관리자 전용)")
        with st.form("add_equip_form"):
            # 입력 순서 조정: 1. 카테고리, 2. 장비명, 3. 일련번호
            col_cat, col_name, col_id = st.columns(3)
            with col_cat:
                new_cat = st.selectbox("1. 카테고리", ["카메라", "음향", "조명", "삼각대/그립", "기타"])
            with col_name:
                new_name = st.text_input("2. 장비명")
            with col_id:
                new_id = st.text_input("3. 일련번호 (예: 26fx01)")
                
            submit_eq = st.form_submit_button("기자재 등록")
            
            if submit_eq:
                if new_id and new_name and new_cat:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO equipment (id, name, category) VALUES (?, ?, ?)", (new_id, new_name, new_cat))
                        conn.commit()
                        conn.close()
                        st.success("기자재가 정상적으로 등록되었음.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 일련번호임.")
                else:
                    st.warning("모든 필드를 입력해야 함.")

# ------------------------------------------
# TAB 2: 대여 신청 (대여/반납 일자 및 교시별 지정 시간 선택)
# ------------------------------------------
with tabs[1]:
    st.subheader("장비 대여 신청서 작성")
    
    conn = get_db_connection()
    cat_df = pd.read_sql_query("SELECT DISTINCT category FROM equipment", conn)
    categories = cat_df['category'].tolist() if not cat_df.empty else []
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.text_input("신청자 성명", value=f"{user_info['name']} ({user_info['username']})", disabled=True)
        
        # 1단계: 카테고리 선택
        selected_cat = st.selectbox("1단계: 카테고리 선택", categories if categories else ["등록된 카테고리 없음"])
        
        selected_equip_id = None
        if selected_cat and categories:
            equip_df = pd.read_sql_query(
                "SELECT id, name FROM equipment WHERE category = ? AND status = 'AVAILABLE'", 
                conn, params=(selected_cat,)
            )
            
            if equip_df.empty:
                st.warning("⚠️ 현재 선택한 카테고리에 대여 가능한 장비가 없음.")
            else:
                equip_options = {f"[{row['id']}] {row['name']}": row['id'] for _, row in equip_df.iterrows()}
                # 2단계: 대여 가능 장비 선택
                selected_label = st.selectbox("2단계: 장비 선택 (대여 가능 장비만 표시됨)", list(equip_options.keys()))
                selected_equip_id = equip_options[selected_label]
                
    conn.close()

    with col_right:
        today = date.today()
        st.markdown("##### 📅 사용 기간 및 대여/반납 시간 설정")
        
        # 달력 기반 사용 기간 선택
        rental_period = st.date_input(
            "사용 기간 선택 (대여일 ~ 반납일)",
            value=(today, today + timedelta(days=1)),
            min_value=today
        )
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            start_time_slot = st.selectbox("대여 시간 선택", TIME_SLOTS, index=0)
        with col_t2:
            end_time_slot = st.selectbox("반납 시간 선택", TIME_SLOTS, index=7)

    if selected_equip_id and len(rental_period) == 2:
        start_d, end_d = rental_period
        start_str, end_str = start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")
        
        st.info(f"📌 **최종 신청 내용**: 대여 `{start_str} [{start_time_slot}]` ~ 반납 `{end_str} [{end_time_slot}]`")
        
        is_available, conflicts = check_overlap(selected_equip_id, start_str, end_str)
        
        if is_available:
            st.success(f"✅ 선택한 기간 ({start_str} ~ {end_str})에 대여 신청이 가능함.")
            if st.button("대여 신청서 제출"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO reservation 
                       (equip_id, user_id, user_name, start_date, end_date, start_time, end_time, status) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')''',
                    (selected_equip_id, user_info["username"], user_info["name"], start_str, end_str, start_time_slot, end_time_slot)
                )
                conn.commit()
                conn.close()
                st.balloons()
                st.success("대여 신청이 완료되었음. 관리자의 승인을 기다려주기 바람.")
                st.rerun()
        else:
            st.error("❌ 해당 기간에 기존 예약/승인건이 존재함.")
            st.warning(f"중복 예약: {conflicts[0]['user_name']} ({conflicts[0]['start_date']} ~ {conflicts[0]['end_date']})")

# ------------------------------------------
# TAB 3: 관리자 승인 또는 내 신청 내역
# ------------------------------------------
if user_info["role"] == "ADMIN":
    with tabs[2]:
        st.subheader("⚙️ 관리자 대여 승인 및 불출/반납 관리")
        
        conn = get_db_connection()
        query = '''
            SELECT r.id, r.equip_id, e.name as equip_name, r.user_name, r.user_id, 
                   r.start_date, r.end_date, r.start_time, r.end_time, r.status 
            FROM reservation r
            JOIN equipment e ON r.equip_id = e.id
            ORDER BY r.id DESC
        '''
        res_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if res_df.empty:
            st.info("등록된 신청 내역이 없음.")
        else:
            for _, row in res_df.iterrows():
                status_label = {
                    "PENDING": "🟠 승인 대기중", 
                    "APPROVED": "🔵 승인완료", 
                    "RENTED": "🟢 불출 완료 (대여중)", 
                    "RETURNED": "⚪ 반납 완료", 
                    "REJECTED": "🔴 거절됨"
                }.get(row['status'], row['status'])
                
                s_time = row['start_time'] if row['start_time'] else "시간 미지정"
                e_time = row['end_time'] if row['end_time'] else "시간 미지정"
                
                with st.expander(f"예약 #{row['id']} | {row['equip_name']} (일련번호: {row['equip_id']}) - 신청자: {row['user_name']} ({row['user_id']}) [{status_label}]"):
                    st.write(f"- 대여 일시: **{row['start_date']} [{s_time}]**")
                    st.write(f"- 반납 일시: **{row['end_date']} [{e_time}]**")
                    
                    c1, c2, c3 = st.columns(3)
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    if row['status'] == "PENDING":
                        if c1.button("대여 승인", key=f"app_{row['id']}"):
                            cursor.execute("UPDATE reservation SET status = 'APPROVED' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                        if c2.button("대여 거절", key=f"rej_{row['id']}"):
                            cursor.execute("UPDATE reservation SET status = 'REJECTED' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                            
                    elif row['status'] == "APPROVED":
                        if c1.button("불출 처리 (장비 인도)", key=f"out_{row['id']}"):
                            cursor.execute("UPDATE reservation SET status = 'RENTED' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE equipment SET status = 'RENTED' WHERE id = ?", (row['equip_id'],))
                            conn.commit()
                            st.rerun()
                            
                    elif row['status'] == "RENTED":
                        if c1.button("반납 완료 처리", key=f"ret_{row['id']}"):
                            cursor.execute("UPDATE reservation SET status = 'RETURNED' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE equipment SET status = 'AVAILABLE' WHERE id = ?", (row['equip_id'],))
                            conn.commit()
                            st.rerun()
                            
                    conn.close()
else:
    with tabs[2]:
        st.subheader("📜 내 대여 신청 내역")
        conn = get_db_connection()
        query = '''
            SELECT r.id AS '신청ID', e.name AS '장비명', 
                   (r.start_date || ' (' || COALESCE(r.start_time, '') || ')') AS '대여 일시', 
                   (r.end_date || ' (' || COALESCE(r.end_time, '') || ')') AS '반납 일시', 
                   r.status AS '상태'
            FROM reservation r
            JOIN equipment e ON r.equip_id = e.id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
        '''
        my_res_df = pd.read_sql_query(query, conn, params=(user_info["username"],))
        conn.close()
        
        if my_res_df.empty:
            st.info("신청한 대여 내역이 없음.")
        else:
            st.dataframe(my_res_df, use_container_width=True)

# ------------------------------------------
# TAB 4: 전체 일정 현황
# ------------------------------------------
with tabs[3]:
    st.subheader("📅 전체 장비 대여 현황")
    conn = get_db_connection()
    df_all = pd.read_sql_query('''
        SELECT r.id AS '예약ID', e.name AS '장비명', r.user_name AS '신청자', 
               (r.start_date || ' [' || COALESCE(r.start_time, '') || ']') AS '대여 일시', 
               (r.end_date || ' [' || COALESCE(r.end_time, '') || ']') AS '반납 일시', 
               r.status AS '상태'
        FROM reservation r
        JOIN equipment e ON r.equip_id = e.id
        ORDER BY r.start_date ASC
    ''', conn)
    conn.close()
    st.dataframe(df_all, use_container_width=True)

# ------------------------------------------
# TAB 5: 계정 관리
# ------------------------------------------
if user_info["role"] == "ADMIN":
    with tabs[4]:
        st.subheader("👥 계정 관리 및 권한 설정 (관리자 전용)")
        
        conn = get_db_connection()
        users_list = pd.read_sql_query("SELECT username, name, role FROM users", conn)
        conn.close()
        
        user_options = {f"{row['name']} ({row['username']}) - {row['role']}": row['username'] for _, row in users_list.iterrows()}
        
        col_pw, col_del = st.columns(2)
        
        with col_pw:
            st.markdown("##### 🔑 사용자 비밀번호 변경")
            with st.form("admin_change_pw_form"):
                target_user_label = st.selectbox("대상 계정 선택", list(user_options.keys()), key="pw_target")
                new_pw = st.text_input("새로운 비밀번호 입력", type="password")
                submit_pw = st.form_submit_button("비밀번호 변경")
                
                if submit_pw:
                    if new_pw:
                        target_username = user_options[target_user_label]
                        update_user_password(target_username, new_pw)
                        st.success(f"계정 (`{target_username}`)의 비밀번호가 변경되었음.")
                    else:
                        st.warning("변경할 비밀번호를 입력해야 함.")

        with col_del:
            st.markdown("##### 🗑️ 계정 삭제")
            with st.form("admin_delete_user_form"):
                del_user_label = st.selectbox("삭제할 계정 선택", list(user_options.keys()), key="del_target")
                submit_del = st.form_submit_button("계정 삭제 처리")
                
                if submit_del:
                    target_username = user_options[del_user_label]
                    if target_username == user_info["username"]:
                        st.error("현재 로그인 중인 본인 계정은 삭제할 수 없음.")
                    elif target_username == "admin":
                        st.error("최초 시스템 관리자(admin) 계정은 삭제할 수 없음.")
                    else:
                        delete_user(target_username)
                        st.success(f"계정 (`{target_username}`)이 정상적으로 삭제되었음.")
                        st.rerun()

        st.divider()
        st.subheader("➕ 신규 계정 직접 발급")
        with st.form("create_user_form"):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_username = st.text_input("아이디 (ID)")
                new_password = st.text_input("비밀번호", type="password")
            with col_u2:
                new_name = st.text_input("사용자 성명")
                new_role = st.selectbox("권한", ["USER", "ADMIN"])
            submit_user = st.form_submit_button("계정 생성")
            
            if submit_user:
                if new_username and new_password and new_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        hashed = hash_password(new_password)
                        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)", 
                                       (new_username, hashed, new_name, new_role))
                        conn.commit()
                        conn.close()
                        st.success(f"계정 ({new_username})이 성공적으로 발급되었음.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 아이디임.")
                else:
                    st.warning("모든 정보를 입력해야 함.")
        
        st.divider()
        st.subheader("등록된 계정 현황")
        conn = get_db_connection()
        users_df = pd.read_sql_query("SELECT username AS '아이디', name AS '성명', role AS '권한' FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)
