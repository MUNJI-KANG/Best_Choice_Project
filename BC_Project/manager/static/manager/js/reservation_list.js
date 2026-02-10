// 예약 목록 관리 JS

document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // 공통 유틸
    // =========================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // =========================
    // 모달 관련 함수
    // =========================
    function cancelCancelMode() {
        document.querySelectorAll('.slot-checkbox').forEach(cb => {
            cb.checked = false;
            cb.style.display = 'none';
        });
        const defaultBtns = document.getElementById('modal-default-buttons');
        const cancelBtns = document.getElementById('modal-cancel-buttons');
        if (defaultBtns) defaultBtns.style.display = 'block';
        if (cancelBtns) cancelBtns.style.display = 'none';
    }

    function openReservationModal(data) {
        const modal = document.getElementById('reservationModal');
        if (!modal) return;

        const facilityNameEl = document.getElementById('modal-facility-name');
        const facilityAddrEl = document.getElementById('modal-facility-address');
        const memberTelEl = document.getElementById('modal-member-tel');
        const member_id = document.getElementById('modal-member');
        const resNumEl = document.getElementById('modal-reservation-num');
        const regDateEl = document.getElementById('modal-reg-date');
        const timeSlotsContainer = document.getElementById('modal-time-slots');

        if (facilityNameEl) facilityNameEl.textContent = data.facility_name || '미정';
        if (facilityAddrEl) facilityAddrEl.textContent = data.facility_address || '미정';
        if (memberTelEl) memberTelEl.textContent = data.member_phone_num || '미정';
        if (member_id) member_id.textContent = data.member_id || '미정';
        if (resNumEl) resNumEl.textContent = data.reservation_num || '';
        if (regDateEl) regDateEl.textContent = data.reg_date || '';

        if (timeSlotsContainer) {
            timeSlotsContainer.innerHTML = '';

            if (data.slot_list && data.slot_list.length > 0) {
                data.slot_list.forEach(slot => {
                    const timeLine = document.createElement('div');
                    timeLine.className = 'time-line' + (slot.is_cancelled ? ' cancelled' : '');
                    timeLine.innerHTML = `
                        ${slot.date} | ${slot.start} ~ ${slot.end}
                        ${
                            slot.is_cancelled
                                ? '<span class="cancel-tag">(취소됨)</span>'
                                : '<input type="checkbox" class="slot-checkbox" ' +
                                  'data-date="' + slot.date + '" ' +
                                  'data-start="' + slot.start + '" ' +
                                  'data-end="' + slot.end + '" ' +
                                  'style="display:none; margin-left:10px;">'
                        }
                    `;
                    timeSlotsContainer.appendChild(timeLine);
                });
            } else {
                timeSlotsContainer.textContent = '미정';
            }
        }

        // 모달에 예약 데이터 저장
        modal.setAttribute('data-reservation-num', data.reservation_num || '');
        modal.setAttribute('data-reservation-data', JSON.stringify(data));

        // 취소 모드 초기화
        cancelCancelMode();

        // 전체 취소 여부 확인
        const allCancelled = data.slot_list && data.slot_list.length > 0 &&
            data.slot_list.every(slot => slot.is_cancelled);
        
        // 예약 날짜가 지났는지 확인 (is_past 값 사용)
        const isPast = data.is_past === true;
        
        const startCancelBtn = document.getElementById('startCancelBtn');
        if (startCancelBtn) {
            // 전체 취소되었거나 예약 날짜가 지난 경우 버튼 숨김
            if (allCancelled || isPast) {
                startCancelBtn.style.display = 'none';
            } else {
                startCancelBtn.style.display = 'inline-block';
            }
            
            // 예약 날짜가 지난 경우 비활성화 및 툴팁 추가
            if (isPast) {
                startCancelBtn.disabled = true;
                startCancelBtn.title = '예약 날짜가 지나 취소할 수 없습니다.';
            } else {
                startCancelBtn.disabled = false;
                startCancelBtn.title = '';
            }
        }

        modal.classList.add('show');
    }

    function closeReservationModal() {
        const modal = document.getElementById('reservationModal');
        if (modal) {
            modal.classList.remove('show');
        }
        cancelCancelMode();
    }

    function startCancelMode() {
        document.querySelectorAll('.slot-checkbox').forEach(cb => {
            cb.style.display = 'inline-block';
        });
        const defaultBtns = document.getElementById('modal-default-buttons');
        const cancelBtns = document.getElementById('modal-cancel-buttons');
        if (defaultBtns) defaultBtns.style.display = 'none';
        if (cancelBtns) cancelBtns.style.display = 'block';
    }

    function cancelSelectedSlots() {
        const modal = document.getElementById('reservationModal');
        if (!modal) return;

        const selected = Array.from(document.querySelectorAll('.slot-checkbox:checked'))
            .map(el => ({
                date: el.dataset.date,
                start: el.dataset.start,
                end: el.dataset.end
            }));

        if (selected.length === 0) {
            alert('취소할 시간을 선택하세요.');
            return;
        }

        if (!confirm('선택한 시간대를 취소하시겠습니까?')) return;

        const reservationNum = modal.getAttribute('data-reservation-num');
        if (!reservationNum) {
            alert('예약 정보가 없습니다.');
            return;
        }

        const csrftoken = getCookie('csrftoken');

        fetch(`/manager/api/reservations/cancel-timeslot/${reservationNum}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ slots: selected })
        })
            .then(res => res.json())
            .then(data => {
                if (data.result === 'ok') {
                    alert(data.msg || '취소 완료');
                    location.reload();
                } else {
                    alert(data.msg || '취소 실패');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('서버 오류 발생');
            });
    }

    // 전역에서 onclick 으로 접근 가능한 함수들 export
    window.closeReservationModal = closeReservationModal;
    window.startCancelMode = startCancelMode;
    window.cancelCancelMode = cancelCancelMode;
    window.cancelSelectedSlots = cancelSelectedSlots;

    // =========================
    // 필터 / 정렬 / 페이지 사이즈
    // =========================
    const params = new URLSearchParams(window.location.search);
    const perPageEl = document.getElementById("perPageSelect");
    const sortEl = document.getElementById("sortSelect");
    const statusEl = document.getElementById("statusSelect");

    // 상태 필터 (누적 예약일 때만 있음)
    if (statusEl) {
        const nowStatus = params.get("status") || "active";
        statusEl.value = nowStatus;
        statusEl.addEventListener("change", function () {
            params.set("status", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    // 정렬 필터
    if (sortEl) {
        const nowSort = params.get("sort") || "reg_date";
        sortEl.value = nowSort;
        sortEl.addEventListener("change", function () {
            params.set("sort", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    // 페이지당 개수
    if (perPageEl) {
        const nowPer = params.get("per_page") || "15";
        perPageEl.value = nowPer;
        perPageEl.addEventListener("change", function () {
            params.set("per_page", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    // =========================
    // 예약 리스트 렌더링
    // =========================
    function renderReservationList(data) {
        const box = document.getElementById("reservationList");
        if (!box) return;

        box.innerHTML = "";

        // 헤더에 "취소 일자" 컬럼이 있는지로 colspan/취소일자 셀 여부 판단
        const hasCancelDateCol = Array.from(
            document.querySelectorAll(".facility-table thead th")
        ).some(th => th.textContent.includes("취소 일자"));

        let colspan = hasCancelDateCol ? 8 : 7;

        if (!data || data.length === 0) {
            box.innerHTML = `<tr><td colspan="${colspan}">등록된 예약이 없습니다.</td></tr>`;
            return;
        }

        box.innerHTML = data.map(item => {
            const statusClass = item.delete_yn == 1 ? 'cancelled' : 'active';
            const cancelDateCell = hasCancelDateCol
                ? `<td>${item.delete_date || '-'}</td>`
                : '';

            // 예약번호 클릭 → 상세 모달
            const reservationNumCell = `
                <td>
                    <a href="#"
                       class="reservation-detail-link"
                       data-reservation-data='${JSON.stringify(item)}'
                       style="color: #3b7cff; text-decoration: none; cursor: pointer;">
                        ${item.reservation_num || ''}
                    </a>
                </td>
            `;
            time_info = `<p class="time-list-wrapper"><span class="time-list date">${item.slot_list[0].date}</span> | `; 
            for (time_item of item.slot_list) {
                if (time_item.is_cancelled){
                    time_info += `<span class="time-list cancelled">${time_item.time_str}</span>`;
                }
                else {
                    time_info += `<span class="time-list">${time_item.time_str}</span>`
                }
            }
            time_info += `</p>`
            return `
                <tr class="reservation-row ${statusClass}">
                    <td>${item.row_no}</td>
                    ${reservationNumCell}
                    <td>${item.sport_type || '미정'}</td>
                    <td>${time_info || '미정'}</td>
                    <td>${item.member_id || ''}</td>
                    <td>${item.member_phone_num || '알 수 없음'}</td>
                    <td>${item.reg_date || ''}</td>
                    ${cancelDateCell}
                </tr>
            `;
        }).join("");

        // 상세 보기 이벤트 연결
        document.querySelectorAll('.reservation-detail-link').forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const raw = this.getAttribute('data-reservation-data');
                if (!raw) return;
                try {
                    const data = JSON.parse(raw);
                    openReservationModal(data);
                } catch (err) {
                    console.error('예약 데이터 파싱 오류:', err);
                }
            });
        });
    }

    // JSON 데이터 파싱
    try {
        const dataElem = document.getElementById("reservationData");
        if (dataElem) {
            const text = (dataElem.textContent || '').trim();
            const list = text ? JSON.parse(text) : [];
            renderReservationList(list);
        }
    } catch (e) {
        console.error("JSON 오류:", e);
    }

    // =========================
    // 검색 기능
    // =========================
    const searchBtn = document.getElementById('searchBtn');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const searchKeywordInput = document.getElementById('searchKeywordInput');
    const searchTypeSelect = document.getElementById('searchTypeSelect');

    function performSearch() {
        const params = new URLSearchParams(window.location.search);
        const searchType = searchTypeSelect ? searchTypeSelect.value : 'reservation_num';
        const searchKeyword = searchKeywordInput ? searchKeywordInput.value.trim() : '';

        if (searchKeyword) {
            params.set('search_type', searchType);
            params.set('search_keyword', searchKeyword);
        } else {
            params.delete('search_type');
            params.delete('search_keyword');
        }
        params.set('page', 1);
        window.location.search = params.toString();
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', function () {
            performSearch();
        });
    }

    if (searchKeywordInput) {
        searchKeywordInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function () {
            const params = new URLSearchParams(window.location.search);
            params.delete('search_type');
            params.delete('search_keyword');
            params.set('page', 1);
            window.location.search = params.toString();
        });
    }

    // =========================
    // 모달 바깥 클릭 시 닫기
    // =========================
    window.onclick = function (event) {
        const modal = document.getElementById('reservationModal');
        if (!modal) return;
        if (event.target === modal) {
            closeReservationModal();
        }
    };
});
