-- 1. 사용자 테이블 (아이디 = 핸드폰 번호)
CREATE TABLE users (
    user_id VARCHAR(20) PRIMARY KEY, -- 핸드폰 번호 (예: 010-1234-5678)
    password VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    role VARCHAR(10) DEFAULT 'USER' -- 'USER' 또는 'ADMIN'
);

-- 2. 장비 정보 테이블
CREATE TABLE equipment (
    equipment_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    total_stock INT DEFAULT 1,
    available_stock INT DEFAULT 1
);

-- 3. 대여 신청 메인 테이블
CREATE TABLE rentals (
    reservation_id VARCHAR(30) PRIMARY KEY, -- 예약 넘버 (예: RES-20260916-001)
    user_id VARCHAR(20) NOT NULL,          -- 신청자 ID (핸드폰 번호)
    user_name VARCHAR(50) NOT NULL,        -- 신청자 성명
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    approval_status VARCHAR(20) DEFAULT '대기',  -- '대기', '승인', '거절'
    checkout_status VARCHAR(20) DEFAULT '미불출', -- '미불출', '불출완료'
    return_status VARCHAR(20) DEFAULT '미반납',   -- '미반납', '반납완료'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 4. 대여 기자재 상세 목록 테이블 (1개 예약당 여러 장비 매핑)
CREATE TABLE rental_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id VARCHAR(30) NOT NULL,
    equipment_id INT NOT NULL,
    equipment_name VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (reservation_id) REFERENCES rentals(reservation_id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);
