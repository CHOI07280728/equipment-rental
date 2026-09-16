<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>스마트 장비 대여 관리 시스템</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen text-gray-800">

    <!-- 상단 네비게이션 -->
    <nav class="bg-slate-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <h1 class="text-xl font-bold">🎥 스마트 장비 대여 시스템</h1>
        <div id="authStatus" class="flex gap-4 items-center text-sm">
            <!-- 로그인 상태 표시 영역 -->
        </div>
    </nav>

    <div class="max-w-6xl mx-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">

        <!-- 1. 회원가입 및 로그인 폼 -->
        <div class="bg-white p-6 rounded-xl shadow-md">
            <h2 class="text-lg font-bold mb-4 text-slate-800 border-b pb-2">👤 회원 관리</h2>
            
            <div id="authForms">
                <!-- 회원가입 -->
                <div class="mb-6">
                    <h3 class="text-sm font-semibold text-gray-600 mb-2">신규 회원가입</h3>
                    <input type="text" id="regPhone" placeholder="핸드폰 번호 (ID) ex) 01012345678" class="w-full p-2 border rounded mb-2 text-sm">
                    <input type="text" id="regName" placeholder="성명" class="w-full p-2 border rounded mb-2 text-sm">
                    <button onclick="register()" class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-sm font-medium">회원가입</button>
                </div>

                <!-- 로그인 -->
                <div class="border-t pt-4">
                    <h3 class="text-sm font-semibold text-gray-600 mb-2">로그인</h3>
                    <input type="text" id="loginPhone" placeholder="핸드폰 번호 (ID)" class="w-full p-2 border rounded mb-2 text-sm">
                    <button onclick="login()" class="w-full bg-slate-800 hover:bg-slate-900 text-white py-2 rounded text-sm font-medium">로그인</button>
                </div>
            </div>
        </div>

        <!-- 2. 대여 신청서 (다중 장비 선택) -->
        <div class="bg-white p-6 rounded-xl shadow-md md:col-span-2">
            <h2 class="text-lg font-bold mb-4 text-slate-800 border-b pb-2">📝 장비 대여 신청서</h2>
            
            <div class="grid grid-cols-2 gap-4 mb-4 bg-gray-50 p-4 rounded-lg">
                <div>
                    <label class="block text-xs font-semibold text-gray-500 mb-1">신청자 성명</label>
                    <input type="text" id="appUserName" readonly class="w-full p-2 bg-gray-200 border rounded text-sm font-bold text-gray-700">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-500 mb-1">신청자 ID (핸드폰 번호)</label>
                    <input type="text" id="appUserId" readonly class="w-full p-2 bg-gray-200 border rounded text-sm font-bold text-gray-700">
                </div>
            </div>

            <div class="mb-4">
                <label class="block text-sm font-semibold mb-2">대여 기자재 다중 선택</label>
                <div id="equipmentList" class="grid grid-cols-2 gap-2 border p-3 rounded-lg max-h-48 overflow-y-auto">
                    <!-- 장비 다중 선택 체크박스 동적 생성 -->
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-xs font-semibold text-gray-500 mb-1">대여 시작일</label>
                    <input type="date" id="startDate" class="w-full p-2 border rounded text-sm">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-500 mb-1">반납 예정일</label>
                    <input type="date" id="endDate" class="w-full p-2 border rounded text-sm">
                </div>
            </div>

            <button onclick="submitRental()" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 rounded-lg font-bold shadow">대여 신청서 제출</button>
        </div>

        <!-- 3. 관리자 대여 승인 및 불출/반납 관리 -->
        <div class="bg-white p-6 rounded-xl shadow-md md:col-span-3">
            <h2 class="text-lg font-bold mb-4 text-slate-800 border-b pb-2 flex justify-between items-center">
                <span>⚙️ 관리자 대여 승인 및 불출/반납 현황</span>
                <span class="text-xs text-gray-500 font-normal">* 예약 목록 및 현황 제어</span>
            </h2>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-sm">
                    <thead>
                        <tr class="bg-slate-100 text-slate-600 border-b">
                            <th class="p-3">예약 넘버</th>
                            <th class="p-3">신청자 (성명/ID)</th>
                            <th class="p-3">대여 승인</th>
                            <th class="p-3">불출 현황</th>
                            <th class="p-3">반납 현황</th>
                            <th class="p-3">상세보기</th>
                        </tr>
                    </thead>
                    <tbody id="rentalTableBody">
                        <!-- 데이터 로딩 영역 -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 기자재 목록 상세보기 모달 -->
    <div id="detailModal" class="fixed inset-0 bg-black/50 hidden flex justify-center items-center p-4">
        <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div class="flex justify-between items-center border-b pb-3 mb-4">
                <h3 class="text-lg font-bold">📦 대여 기자재 상세 목록</h3>
                <button onclick="closeModal()" class="text-gray-400 hover:text-black font-bold">✕</button>
            </div>
            <div class="mb-4">
                <p class="text-xs text-gray-500">예약 번호: <span id="modalResId" class="font-bold text-slate-800"></span></p>
            </div>
            <ul id="modalEquipmentList" class="divide-y border-t border-b py-2 mb-4 max-h-60 overflow-y-auto">
                <!-- 선택한 장비 목록 표시 -->
            </ul>
            <button onclick="closeModal()" class="w-full bg-slate-800 text-white py-2 rounded-lg text-sm font-medium">닫기</button>
        </div>
    </div>

    <script>
        // 초기 시뮬레이션 데이터
        let currentUser = null;
        let equipments = [
            { id: 101, name: "시네마 카메라 (Blackmagic 6K)" },
            { id: 102, name: "삼각대 (Libec 650EX)" },
            { id: 103, name: "무선 마이크 (Hollyland Lark M1)" },
            { id: 104, name: "지속광 조명 (Amaran 200d)" },
            { id: 105, name: "프리미어용 모니터링 탭" }
        ];

        let rentals = [];
        let users = {};

        // 초기화
        window.onload = function() {
            renderEquipmentList();
            renderAdminTable();
            updateAuthUI();
        };

        // 회원가입 (핸드폰 번호 = 아이디)
        function register() {
            const phone = document.getElementById('regPhone').value.trim();
            const name = document.getElementById('regName').value.trim();

            if (!phone || !name) {
                alert('핸드폰 번호와 성명을 모두 입력해줌.');
                return;
            }

            users[phone] = { id: phone, name: name };
            alert(`회원가입 완료! (ID: ${phone})`);
            document.getElementById('regPhone').value = '';
            document.getElementById('regName').value = '';
        }

        // 로그인
        function login() {
            const phone = document.getElementById('loginPhone').value.trim();
            if (!users[phone]) {
                alert('존재하지 않는 회원 정보임. 가입 후 이용 바람.');
                return;
            }
            currentUser = users[phone];
            updateAuthUI();
            alert(`${currentUser.name}님 환영함.`);
        }

        // 로그아웃
        function logout() {
            currentUser = null;
            updateAuthUI();
        }

        // 사용자 인증 UI 및 신청서 자동 입력 연동
        function updateAuthUI() {
            const authStatus = document.getElementById('authStatus');
            const appUserName = document.getElementById('appUserName');
            const appUserId = document.getElementById('appUserId');

            if (currentUser) {
                authStatus.innerHTML = `
                    <span>로그인: <b>${currentUser.name}</b> (${currentUser.id})</span>
                    <button onclick="logout()" class="bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-xs">로그아웃</button>
                `;
                appUserName.value = currentUser.name;
                appUserId.value = currentUser.id;
            } else {
                authStatus.innerHTML = `<span class="text-gray-400">로그인이 필요함</span>`;
                appUserName.value = '로그인 필요';
                appUserId.value = '로그인 필요';
            }
        }

        // 장비 다중 선택 체크박스 랜더링
        function renderEquipmentList() {
            const container = document.getElementById('equipmentList');
            container.innerHTML = equipments.map(item => `
                <label class="flex items-center gap-2 p-2 rounded hover:bg-gray-100 border text-xs cursor-pointer">
                    <input type="checkbox" value="${item.id}" data-name="${item.name}" class="eq-checkbox accent-blue-600">
                    <span>${item.name}</span>
                </label>
            `).join('');
        }

        // 대여 신청서 제출
        function submitRental() {
            if (!currentUser) {
                alert('로그인 후 신청 가능함.');
                return;
            }

            const selectedBoxes = document.querySelectorAll('.eq-checkbox:checked');
            if (selectedBoxes.length === 0) {
                alert('대여할 기자재를 1개 이상 선택해줌.');
                return;
            }

            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            if (!startDate || !endDate) {
                alert('대여 및 반납 날짜를 지정해줌.');
                return;
            }

            const selectedItems = Array.from(selectedBoxes).map(box => ({
                id: box.value,
                name: box.getAttribute('data-name')
            }));

            const resNumber = 'RES-' + Date.now().toString().slice(-6);

            const newRental = {
                resId: resNumber,
                userName: currentUser.name,
                userId: currentUser.id,
                items: selectedItems,
                startDate: startDate,
                endDate: endDate,
                approval: '대기',
                checkout: '미불출',
                returnStatus: '미반납'
            };

            rentals.push(newRental);
            alert(`대여 신청이 완료됨! (예약 번호: ${resNumber})`);
            
            // 체크박스 초기화
            selectedBoxes.forEach(box => box.checked = false);
            renderAdminTable();
        }

        // 관리자 테이블 랜더링
        function renderAdminTable() {
            const tbody = document.getElementById('rentalTableBody');
            if (rentals.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-gray-400">신청된 대여 내역이 없음.</td></tr>`;
                return;
            }

            tbody.innerHTML = rentals.map((item, idx) => `
                <tr class="border-b hover:bg-gray-50">
                    <td class="p-3 font-mono font-bold text-blue-600">${item.resId}</td>
                    <td class="p-3"><b>${item.userName}</b><br><span class="text-xs text-gray-500">${item.userId}</span></td>
                    <td class="p-3">
                        <select onchange="updateStatus(${idx}, 'approval', this.value)" class="p-1 border rounded text-xs font-semibold ${item.approval === '승인' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                            <option value="대기" ${item.approval === '대기' ? 'selected' : ''}>대기</option>
                            <option value="승인" ${item.approval === '승인' ? 'selected' : ''}>승인</option>
                            <option value="거절" ${item.approval === '거절' ? 'selected' : ''}>거절</option>
                        </select>
                    </td>
                    <td class="p-3">
                        <select onchange="updateStatus(${idx}, 'checkout', this.value)" class="p-1 border rounded text-xs font-semibold ${item.checkout === '불출 완료' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100'}">
                            <option value="미불출" ${item.checkout === '미불출' ? 'selected' : ''}>미불출</option>
                            <option value="불출 완료" ${item.checkout === '불출 완료' ? 'selected' : ''}>불출 완료</option>
                        </select>
                    </td>
                    <td class="p-3">
                        <select onchange="updateStatus(${idx}, 'returnStatus', this.value)" class="p-1 border rounded text-xs font-semibold ${item.returnStatus === '반납 완료' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100'}">
                            <option value="미반납" ${item.returnStatus === '미반납' ? 'selected' : ''}>미반납</option>
                            <option value="반납 완료" ${item.returnStatus === '반납 완료' ? 'selected' : ''}>반납 완료</option>
                        </select>
                    </td>
                    <td class="p-3">
                        <button onclick="openDetailModal(${idx})" class="bg-slate-700 hover:bg-slate-800 text-white px-2.5 py-1 rounded text-xs">자세히 보기</button>
                    </td>
                </tr>
            `).join('');
        }

        // 관리자 상태 업데이트
        function updateStatus(index, field, value) {
            rentals[index][field] = value;
            renderAdminTable();
        }

        // 기자재 상세 모달 열기
        function openDetailModal(index) {
            const rental = rentals[index];
            document.getElementById('modalResId').innerText = rental.resId;
            
            const listContainer = document.getElementById('modalEquipmentList');
            listContainer.innerHTML = rental.items.map(eq => `
                <li class="py-2 flex justify-between items-center text-sm">
                    <span class="font-medium text-gray-700">🎬 ${eq.name}</span>
                    <span class="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">수량: 1대</span>
                </li>
            `).join('');

            document.getElementById('detailModal').classList.remove('hidden');
        }

        // 모달 닫기
        function closeModal() {
            document.getElementById('detailModal').classList.add('hidden');
        }
    </script>
</body>
</html>
