import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date, datetime, timedelta

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
    """데이터베이스 및 기본 관리자/사용자 계정 초기화"""
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
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (equip_id) REFERENCES equipment (id),
            FOREIGN KEY (user_id) REFERENCES users (username)
        )
    ''')
    
    # 시드 데이터: 초기 관리자 및 기본 유저 등록
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ("admin", hash_password("admin123"), "시스템 관리자", "ADMIN"),
            ("user1", hash_password("user123"), "김철수", "USER"),
            ("user2", hash_password("user123"), "이영희", "USER")
        ]
        cursor.executemany("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)", default_users)
    
    # 시드 데이터: 단일 일련번호 샘플 등록 (eq001 -> 26fx01 변경 반영)
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
# 2. 세션 및 인증 로직
# ==========================================
if "user_info" not in st.session_state:
    st.session_state.user_info = None

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
# 3. 레이아웃 & 사이드바 로그인 UI
# ==========================================
st.set_page_config(page_title="장비 대여 관리 시스템 Pro", layout="wide")

st.sidebar.title("🔐 계정 로그인")

if st.session_state.user_info is None:
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
    
    st.sidebar.info("💡 **테스트 계정 정보**\n- 관리자: admin / admin123\n- 일반 유저: user1 / user123")
    
    st.title("📹 장비 대여 시스템")
    st.warning("⚠️ 서비스를 이용하려면 사이드바에서 먼저 로그인하기 바람.")
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
# 4. 권한 기반 메인 UI (Tabs)
# ==========================================
st.title("📹 장비 대여 및 일정 관리 시스템 Pro")

if user_info["role"] == "ADMIN":
    tabs = st.tabs(["📋 기자재 관리", "📝 대여 신청", "⚙️ 관리자 대여 승인/불출", "📅 전체 일정 현황", "👥 계정 관리"])
else:
    tabs = st.tabs(["📋 기자재 목록", "📝 대여 신청", "📜 내 신청 내역", "📅 전체 일정 현황"])

# ------------------------------------------
# TAB 1: 기자재 목록 및 관리 ('일련번호' 명칭 변경)
# ------------------------------------------
with tabs[0]:
    st.subheader("보유 기자재 목록")
    conn = get_db_connection()
    df_eq = pd.read_sql_query("SELECT id AS '일련번호', name AS '장비명', category AS '카테고리', status AS '상태' FROM equipment", conn)
    conn.close()
    st.dataframe(df_eq, use_container_width=True)
    
    if user_info["role"] == "ADMIN":
        st.divider()
        st.subheader("➕ 신규 기자재 등록 (관리자 전용)")
        with st.form("add_equip_form"):
            col_id, col_name, col_cat = st.columns(3)
            with col_id:
                new_id = st.text_input("일련번호 (예: 26fx01)")
            with col_name:
                new_name = st.text_input("장비명")
            with col_cat:
                new_cat = st.selectbox("카테고리", ["카메라", "음향", "조명", "삼각대/그립", "기타"])
            submit_eq = st.form_submit_button("기자재 등록")
            
            if submit_eq:
                if new_id and new_name:
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
# TAB 2: 대여 신청
# ------------------------------------------
with tabs[1]:
    st.subheader("장비 대여 신청서 작성")
    
    conn = get_db_connection()
    equip_df = pd.read_sql_query("SELECT id, name FROM equipment", conn)
    conn.close()
    
    equip_options = {f"[{row['id']}] {row['name']}": row['id'] for _, row in equip_df.iterrows()}
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("신청자 성명", value=f"{user_info['name']} ({user_info['username']})", disabled=True)
        selected_equip_label = st.selectbox("대여할 장비 선택 (일련번호 기준)", list(equip_options.keys()))
        selected_equip_id = equip_options[selected_equip_label]

    with col2:
        today = date.today()
        rental_period = st.date_input(
            "대여 기간 선택 (시작일 ~ 반납일)",
            value=(today, today + timedelta(days=1)),
            min_value=today
        )

    if len(rental_period) == 2:
        start_d, end_d = rental_period
        start_str, end_str = start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")
        
        is_available, conflicts = check_overlap(selected_equip_id, start_str, end_str)
        
        if is_available:
            st.success(f"✅ 선택한 기간 ({start_str} ~ {end_str})에 대여 신청이 가능함.")
            if st.button("대여 신청서 제출"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reservation (equip_id, user_id, user_name, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
                    (selected_equip_id, user_info["username"], user_info["name"], start_str, end_str)
                )
                conn.commit()
                conn.close()
                st.balloons()
                st.success("대여 신청이 완료되었음. 관리자의 승인을 기다려주기 바람.")
        else:
            st.error("❌ 선택한 기간에 이미 승인/대기 중인 예약이 존재함.")
            st.warning(f"중복 예약: {conflicts[0]['user_name']} ({conflicts[0]['start_date']} ~ {conflicts[0]['end_date']})")

# ------------------------------------------
# TAB 3: 관리자 승인 또는 내 신청 내역
# ------------------------------------------
if user_info["role"] == "ADMIN":
    with tabs[2]:
        st.subheader("⚙️ 관리자 대여 승인 및 불출/반납 관리")
        
        conn = get_db_connection()
        query = '''
            SELECT r.id, r.equip_id, e.name as equip_name, r.user_name, r.user_id, r.start_date, r.end_date, r.status 
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
                
                with st.expander(f"예약 #{row['id']} | {row['equip_name']} (일련번호: {row['equip_id']}) - 신청자: {row['user_name']} ({row['user_id']}) [{status_label}]"):
                    st.write(f"- 대여 기간: **{row['start_date']} ~ {row['end_date']}**")
                    
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
            SELECT r.id AS '신청ID', e.name AS '장비명', r.start_date AS '시작일', 
                   r.end_date AS '반납일', r.status AS '상태'
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
               r.start_date AS '시작일', r.end_date AS '반납예정일', r.status AS '상태'
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
        st.subheader("👥 신규 계정 등록 및 권한 설정 (관리자 전용)")
        
        with st.form("create_user_form"):
            new_username = st.text_input("아이디 (ID)")
            new_password = st.text_input("비밀번호", type="password")
            new_name = st.text_input("사용자 성명")
            new_role = st.selectbox("권한", ["USER", "ADMIN"])
            submit_user = st.form_submit_button("신규 계정 생성")
            
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