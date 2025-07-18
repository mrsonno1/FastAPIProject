# main.py
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from Enduser.routers import login as enduser_login_router
from Enduser.routers import custom_design as enduser_custom_design_router
from Enduser.routers import portfolio as enduser_portfolio_router
from Enduser.routers import cart as enduser_cart_router  # 추가
from Enduser.routers import sample as enduser_sample_router  # 추가
from Enduser.routers import brand as enduser_brand_router  # 추가
from Enduser.routers import released_product as enduser_released_product_router  # 추가
from Enduser.routers import share as enduser_share_router  # 추가
from Enduser.routers import language_setting as enduser_language_setting_router
from Enduser import Email
from Manager.released_product.routers import released_product
from Manager.portfolio.routers import portfolio
from Manager.image.routers import upload
from Manager.custom_design.routers import custom_design
from Manager.country.routers import country
from Manager.color.routers import color
from Manager.brand.routers import brand
from Manager.admin.routers import auth, admin, database
from Manager.rank.routers import rank as rank
from Manager.progress_status.routers import progress_status
from db.database import engine, Base


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# DB 테이블 생성 (프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장)
Base.metadata.create_all(bind=engine)

# docs_url과 redoc_url을 /api 하위 경로로 지정합니다.
app = FastAPI(
    title="LensGrapick",
    version="0.6.0",
    description="LensGrapick API 설명입니다.<br>업데이트 : 2025 07 10 15 00",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    """
    모든 API 응답에 대해 캐시를 비활성화하는 헤더를 추가합니다.
    브라우저가 항상 최신 데이터를 받도록 보장합니다.
    """
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# 허용할 출처(origin) 목록을 정의합니다.
# 개발 중에는 프론트엔드 개발 서버의 주소를 넣습니다.
# 예: React는 3000, Vue는 8080, Svelte는 5173 등
origins = [
    "http://localhost",
    "https://localhost",

    "http://localhost:3000",
    "https://localhost:3000",

    "http://localhost:8080",
    "https://localhost:8080",

    "http://52.79.185.227:3000",
    "https://52.79.185.227:3000",

    "http://10.10.100.85:3000",
    "https://10.10.100.85:3000",

    "http://10.10.101.39:3000",
    "https://10.10.101.39:3000",

    "http://10.10.100.197:3000",
    "https://10.10.100.197:3000",

    "https://admin.lensgrapick.com",
    "https://api.lensgrapick.com",
    "null"  # 로컬 파일(file://)에서의 요청을 허용하기 위해 추가

    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 위에서 정의한 출처 목록
    #allow_origins=["*"],  # 위에서 정의한 출처 목록
    allow_credentials=True, # 쿠키를 포함한 요청을 허용할 것인지
    allow_methods=["*"],    # 모든 HTTP 메서드를 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],    # 모든 HTTP 헤더를 허용
)

unity_router = APIRouter(prefix="/unity")
unity_router.include_router(enduser_login_router.router)
unity_router.include_router(enduser_custom_design_router.router)
unity_router.include_router(enduser_portfolio_router.router)
unity_router.include_router(enduser_cart_router.router)  # 추가
unity_router.include_router(enduser_sample_router.router)  # 추가
unity_router.include_router(enduser_brand_router.router)  # 추가
unity_router.include_router(enduser_released_product_router.router)  # 추가
unity_router.include_router(enduser_share_router.router)  # 추가
unity_router.include_router(enduser_language_setting_router.router)

unity_router.include_router(Email.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
api_router.include_router(color.router)
api_router.include_router(brand.router)
api_router.include_router(country.router)
api_router.include_router(custom_design.router)
api_router.include_router(portfolio.router)
api_router.include_router(released_product.router)
api_router.include_router(rank.router)
api_router.include_router(progress_status.router)


database_router = APIRouter(prefix="/database")

database_router.include_router(database.router)

app.include_router(api_router)
app.include_router(unity_router)
app.include_router(database_router)

# HTML 페이지 라우트 추가
@app.get("/database", response_class=HTMLResponse)
async def database_manager():
    """데이터베이스 관리 페이지"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
        }

        .table-selector {
            margin-bottom: 20px;
        }

        select {
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
            cursor: pointer;
        }

        .button-group {
            margin: 20px 0;
            display: flex;
            gap: 10px;
        }

        button {
            padding: 10px 20px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .btn-primary {
            background-color: #007bff;
            color: white;
        }

        .btn-primary:hover {
            background-color: #0056b3;
        }

        .btn-danger {
            background-color: #dc3545;
            color: white;
        }

        .btn-danger:hover {
            background-color: #c82333;
        }

        .btn-success {
            background-color: #28a745;
            color: white;
        }

        .btn-success:hover {
            background-color: #218838;
        }

        .table-container {
            overflow-x: auto;
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        tr:hover {
            background-color: #f8f9fa;
        }

        .editable {
            background-color: #fff3cd;
            cursor: text;
        }

        .editable:focus {
            outline: 2px solid #007bff;
            background-color: white;
        }

        .checkbox-cell {
            width: 40px;
            text-align: center;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }

        .success {
            background-color: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            z-index: 1000;
        }

        .modal-content {
            position: relative;
            background-color: white;
            margin: 15% auto;
            padding: 20px;
            width: 80%;
            max-width: 500px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .close {
            position: absolute;
            right: 10px;
            top: 10px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: #dc3545;
        }

        .auth-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }

        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }

        .column-selector {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }

        .column-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .column-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
    </style>
</head>
<body>
    <!-- 로그인 폼 -->
    <div id="authContainer" class="auth-container">
        <h2>Database Manager Login</h2>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn-primary" style="width: 100%;">Login</button>
        </form>
        <div id="loginError" class="error" style="display: none; margin-top: 10px;"></div>
    </div>

    <!-- 메인 컨테이너 -->
    <div id="mainContainer" class="container" style="display: none;">
        <h1>Database Manager</h1>

        <div class="table-selector">
            <label for="tableSelect">테이블 선택: </label>
            <select id="tableSelect">
                <option value="">-- 테이블을 선택하세요 --</option>
            </select>
            <button onclick="loadTableData()" class="btn-primary" style="margin-left: 10px;">불러오기</button>
        </div>

        <!-- 컬럼 선택기 -->
        <div id="columnSelector" class="column-selector" style="display: none;">
            <h3>표시할 컬럼 선택:</h3>
            <div class="column-list" id="columnList"></div>
        </div>

        <div id="messageArea"></div>

        <div class="button-group" id="actionButtons" style="display: none;">
            <button onclick="saveChanges()" class="btn-success">변경사항 저장</button>
            <button onclick="deleteSelected()" class="btn-danger">선택 항목 삭제</button>
            <button onclick="addNewRow()" class="btn-primary">새 행 추가</button>
            <button onclick="exportData()" class="btn-primary">CSV 내보내기</button>
        </div>

        <div class="table-container">
            <div id="loadingArea" class="loading" style="display: none;">데이터를 불러오는 중...</div>
            <table id="dataTable" style="display: none;">
                <thead id="tableHead"></thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- 새 행 추가 모달 -->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>새 행 추가</h2>
            <form id="addForm">
                <div id="addFormFields"></div>
                <button type="submit" class="btn-success" style="margin-top: 20px;">추가</button>
            </form>
        </div>
    </div>

    <script>
        let currentTable = '';
        let tableData = [];
        let tableColumns = [];
        let modifiedRows = new Set();
        let selectedColumns = new Set();
        let authToken = '';

        // 로그인 처리
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    authToken = data.access_token;
                    document.getElementById('authContainer').style.display = 'none';
                    document.getElementById('mainContainer').style.display = 'block';
                    await loadTables();
                } else {
                    document.getElementById('loginError').textContent = data.detail || '로그인 실패';
                    document.getElementById('loginError').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('loginError').textContent = '로그인 중 오류 발생: ' + error.message;
                document.getElementById('loginError').style.display = 'block';
            }
        });

        // API 호출 헬퍼 함수
        async function apiCall(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    ...options.headers
                }
            };

            const response = await fetch(url, { ...options, ...defaultOptions });

            if (response.status === 401) {
                document.getElementById('authContainer').style.display = 'block';
                document.getElementById('mainContainer').style.display = 'none';
                throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
            }

            return response;
        }

        // 테이블 목록 로드
        async function loadTables() {
            try {
                const response = await apiCall('/api/admin/database/tables');
                const data = await response.json();
                const tables = Array.isArray(data) ? data : (data.tables || []);

                const select = document.getElementById('tableSelect');
                select.innerHTML = '<option value="">-- 테이블을 선택하세요 --</option>';

                tables.forEach(table => {
                    const option = document.createElement('option');
                    option.value = table;
                    option.textContent = table;
                    select.appendChild(option);
                });
            } catch (error) {
                showMessage('테이블 목록을 불러오는데 실패했습니다: ' + error.message, 'error');
            }
        }

        // 테이블 데이터 로드
        async function loadTableData() {
            const tableName = document.getElementById('tableSelect').value;
            if (!tableName) {
                showMessage('테이블을 선택해주세요.', 'error');
                return;
            }

            currentTable = tableName;
            document.getElementById('loadingArea').style.display = 'block';
            document.getElementById('dataTable').style.display = 'none';
            document.getElementById('actionButtons').style.display = 'none';

            try {
                const response = await apiCall(`/api/admin/database/table/${tableName}`);
                const data = await response.json();

                tableColumns = data.columns;
                tableData = data.rows;

                displayColumnSelector();
                displayTable();

                document.getElementById('loadingArea').style.display = 'none';
                document.getElementById('dataTable').style.display = 'table';
                document.getElementById('actionButtons').style.display = 'flex';

            } catch (error) {
                document.getElementById('loadingArea').style.display = 'none';
                showMessage('데이터를 불러오는데 실패했습니다: ' + error.message, 'error');
            }
        }

        // 컬럼 선택기 표시
        function displayColumnSelector() {
            const columnList = document.getElementById('columnList');
            columnList.innerHTML = '';

            selectedColumns = new Set(tableColumns);

            tableColumns.forEach(column => {
                const item = document.createElement('div');
                item.className = 'column-item';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `col_${column}`;
                checkbox.value = column;
                checkbox.checked = true;
                checkbox.onchange = () => toggleColumn(column);

                const label = document.createElement('label');
                label.htmlFor = `col_${column}`;
                label.textContent = column;

                item.appendChild(checkbox);
                item.appendChild(label);
                columnList.appendChild(item);
            });

            document.getElementById('columnSelector').style.display = 'block';
        }

        // 컬럼 토글
        function toggleColumn(column) {
            if (selectedColumns.has(column)) {
                selectedColumns.delete(column);
            } else {
                selectedColumns.add(column);
            }
            displayTable();
        }

        // 테이블 표시
        function displayTable() {
            const thead = document.getElementById('tableHead');
            const tbody = document.getElementById('tableBody');

            thead.innerHTML = '';
            const headerRow = document.createElement('tr');

            const checkHeader = document.createElement('th');
            checkHeader.className = 'checkbox-cell';
            checkHeader.innerHTML = '<input type="checkbox" onchange="toggleAllCheckboxes(this)">';
            headerRow.appendChild(checkHeader);

            Array.from(selectedColumns).forEach(column => {
                const th = document.createElement('th');
                th.textContent = column;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);

            tbody.innerHTML = '';
            tableData.forEach((row, index) => {
                const tr = document.createElement('tr');
                tr.dataset.index = index;

                const checkCell = document.createElement('td');
                checkCell.className = 'checkbox-cell';
                checkCell.innerHTML = '<input type="checkbox" class="row-checkbox">';
                tr.appendChild(checkCell);

                Array.from(selectedColumns).forEach(column => {
                    const td = document.createElement('td');
                    const value = row[column];

                    if (value === null || value === undefined) {
                        td.textContent = 'NULL';
                        td.style.color = '#999';
                    } else if (typeof value === 'object') {
                        td.textContent = JSON.stringify(value);
                    } else {
                        td.textContent = value;
                    }

                    if (column !== 'id' && !column.endsWith('_at')) {
                        td.contentEditable = true;
                        td.className = 'editable';
                        td.addEventListener('blur', () => handleCellEdit(index, column, td));
                        td.addEventListener('keypress', (e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                td.blur();
                            }
                        });
                    }

                    tr.appendChild(td);
                });

                tbody.appendChild(tr);
            });
        }

        // 셀 편집 처리
        function handleCellEdit(rowIndex, column, cell) {
            const newValue = cell.textContent.trim();
            const oldValue = tableData[rowIndex][column];

            if (newValue !== String(oldValue)) {
                if (newValue === 'NULL' || newValue === '') {
                    tableData[rowIndex][column] = null;
                } else {
                    tableData[rowIndex][column] = newValue;
                }

                modifiedRows.add(rowIndex);
                cell.style.backgroundColor = '#d4edda';
            }
        }

        // 전체 선택/해제
        function toggleAllCheckboxes(checkbox) {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = checkbox.checked);
        }

        // 변경사항 저장
        async function saveChanges() {
            if (modifiedRows.size === 0) {
                showMessage('변경사항이 없습니다.', 'error');
                return;
            }

            const updates = [];
            modifiedRows.forEach(index => {
                const row = tableData[index];
                const id = row.id;

                if (!id) {
                    showMessage('ID가 없는 행은 수정할 수 없습니다.', 'error');
                    return;
                }

                const updateData = {};
                Array.from(selectedColumns).forEach(column => {
                    if (column !== 'id' && !column.endsWith('_at')) {
                        updateData[column] = row[column];
                    }
                });

                updates.push({ id, data: updateData });
            });

            try {
                const response = await apiCall(`/api/admin/database/table/${currentTable}/update`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ updates })
                });

                if (response.ok) {
                    showMessage('변경사항이 저장되었습니다.', 'success');
                    modifiedRows.clear();
                    loadTableData();
                } else {
                    const error = await response.json();
                    showMessage('저장 실패: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('저장 중 오류 발생: ' + error.message, 'error');
            }
        }

        // 선택 항목 삭제
        async function deleteSelected() {
            const checkboxes = document.querySelectorAll('.row-checkbox:checked');
            if (checkboxes.length === 0) {
                showMessage('삭제할 항목을 선택해주세요.', 'error');
                return;
            }

            if (!confirm(`선택한 ${checkboxes.length}개 항목을 삭제하시겠습니까?`)) {
                return;
            }

            const ids = [];
            checkboxes.forEach(checkbox => {
                const row = checkbox.closest('tr');
                const index = row.dataset.index;
                const id = tableData[index].id;
                if (id) ids.push(id);
            });

            try {
                const response = await apiCall(`/api/admin/database/table/${currentTable}/delete`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ids })
                });

                if (response.ok) {
                    showMessage(`${ids.length}개 항목이 삭제되었습니다.`, 'success');
                    loadTableData();
                } else {
                    const error = await response.json();
                    showMessage('삭제 실패: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('삭제 중 오류 발생: ' + error.message, 'error');
            }
        }

        // 새 행 추가
        function addNewRow() {
            const modal = document.getElementById('addModal');
            const formFields = document.getElementById('addFormFields');

            formFields.innerHTML = '';

            tableColumns.forEach(column => {
                if (column !== 'id' && !column.endsWith('_at')) {
                    const div = document.createElement('div');
                    div.className = 'form-group';

                    const label = document.createElement('label');
                    label.textContent = column;

                    const input = document.createElement('input');
                    input.type = 'text';
                    input.name = column;
                    input.placeholder = `Enter ${column}`;

                    div.appendChild(label);
                    div.appendChild(input);
                    formFields.appendChild(div);
                }
            });

            modal.style.display = 'block';
        }

        // 모달 닫기
        function closeModal() {
            document.getElementById('addModal').style.display = 'none';
        }

        // 새 행 추가 폼 제출
        document.getElementById('addForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = {};

            for (let [key, value] of formData.entries()) {
                data[key] = value || null;
            }

            try {
                const response = await apiCall(`/api/admin/database/table/${currentTable}/insert`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    showMessage('새 행이 추가되었습니다.', 'success');
                    closeModal();
                    loadTableData();
                } else {
                    const error = await response.json();
                    showMessage('추가 실패: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('추가 중 오류 발생: ' + error.message, 'error');
            }
        });

        // CSV 내보내기
        function exportData() {
            let csv = Array.from(selectedColumns).join(',') + '\\n';

            tableData.forEach(row => {
                const values = Array.from(selectedColumns).map(column => {
                    const value = row[column];
                    if (value === null || value === undefined) return '';
                    if (typeof value === 'string' && value.includes(',')) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                });
                csv += values.join(',') + '\\n';
            });

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${currentTable}_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
        }

        // 메시지 표시
        function showMessage(message, type) {
            const messageArea = document.getElementById('messageArea');
            messageArea.innerHTML = `<div class="${type}">${message}</div>`;

            setTimeout(() => {
                messageArea.innerHTML = '';
            }, 5000);
        }

        // 모달 외부 클릭 시 닫기
        window.onclick = function(event) {
            const modal = document.getElementById('addModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/",include_in_schema=False)
def read_root():
    return {"message": "Welcome to the FastAPI Token Auth System"}