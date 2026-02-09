document.addEventListener("DOMContentLoaded", function () {

    /* -------------------------------
     * 0. 공통 상수 / 유틸
     * ------------------------------- */
    const DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
    const ORDERED_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
    const DAY_LABELS = {
        sunday: "일요일",
        monday: "월요일",
        tuesday: "화요일",
        wednesday: "수요일",
        thursday: "목요일",
        friday: "금요일",
        saturday: "토요일"
    };

    const DEFAULT_INTERVAL = 60; // 기본 60
    const ALLOWED_INTERVALS = new Set([30, 60]);

    function timeToMinutes(t) {
        const [h, m] = String(t).split(":").map(Number);
        return h * 60 + m;
    }

    function minutesToTime(min) {
        const h = String(Math.floor(min / 60)).padStart(2, "0");
        const m = String(min % 60).padStart(2, "0");
        return `${h}:${m}`;
    }

    function normalizePaymentDigits(value) {
        const digits = String(value ?? "").replace(/[^\d]/g, "");
        return digits === "" ? null : digits;
    }

    function formatWon(digitsOrAny) {
        const digits = String(digitsOrAny ?? "").replace(/[^\d]/g, "");
        if (!digits) return "";
        return `₩${Number(digits).toLocaleString("ko-KR")}`;
    }

    function getIntervalFromEl(el, fallback = DEFAULT_INTERVAL) {
        const v = Number(el?.value);
        return ALLOWED_INTERVALS.has(v) ? v : fallback;
    }

    function isReservationEnabled() {
        const rs = document.getElementById("rsPosible");
        if (!rs) return true;

        // checkbox/radio
        if (typeof rs.checked === "boolean") return rs.checked;

        // select (value "1"=활성, "0"=비활성 패턴 지원)
        if (rs.tagName === "SELECT") return String(rs.value) === "1";

        return Boolean(rs.value);
    }

    function attachPaymentFormatter(inputEl) {
        if (!inputEl) return;

        inputEl.addEventListener("input", function () {
            const raw = this.value.replace(/[^\d]/g, "");
            if (raw === "") {
                this.value = "0";
                return;
            }
            this.value = "₩ " + Number(raw).toLocaleString("ko-KR");
        });

        inputEl.addEventListener("focus", function () {
            const raw = this.value.replace(/[^\d]/g, "");
            this.value = raw === "" ? "0" : raw;
        });

        inputEl.addEventListener("blur", function () {
            const raw = this.value.replace(/[^\d]/g, "");
            this.value = raw === "" || raw === "0" ? "0" : ("₩ " + Number(raw).toLocaleString("ko-KR"));
        });
    }

    /* -------------------------------
     * 1. 핵심: range 기반 슬롯 생성 (공백 보존)
     *    - 절대 open~close 연속 슬롯 생성 금지
     * ------------------------------- */
    function buildSlotsFromRanges(ranges, interval) {
        const slotSet = new Set();
        const slots = [];

        (ranges || []).forEach((r) => {
            if (!r?.start || !r?.end) return;

            const startMin = timeToMinutes(r.start);
            const endMin = timeToMinutes(r.end);
            if (!(startMin < endMin)) return;

            for (let t = startMin; t + interval <= endMin; t += interval) {
                const s = minutesToTime(t);
                const e = minutesToTime(t + interval);
                const key = `${s}-${e}-${r.payment ?? ""}`; 

                if (slotSet.has(key)) continue;
                slotSet.add(key);

                slots.push({
                    start: s,
                    end: e,
                    payment: r.payment ?? null
                });
            }
        });

        // 시간 순 정렬
        slots.sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));
        return slots;
    }

    /* -------------------------------
     * 2. 데이터 구조
     *    timeData[day] = {
     *      interval: 30|60,
     *      ranges: [{start,end,payment}, ...]
     *    }
     * ------------------------------- */
    const timeData = {};
    DAYS.forEach((d) => {
        timeData[d] = { interval: DEFAULT_INTERVAL, ranges: [] };
    });

    /* -------------------------------
     * 3. 기존 JSON 파싱 (레거시/확장 모두 대응)
     *    - 레거시: parsed[day].open/close...
     *    - 확장:  parsed.ranges[day] 배열
     * ------------------------------- */
    const raw = document.getElementById("timeJson")?.textContent.trim();

    try {
        const parsed = raw ? JSON.parse(raw) : {};

        // 확장 구조 우선
        if (parsed?.ranges && typeof parsed.ranges === "object") {
            DAYS.forEach((day) => {
                const arr = Array.isArray(parsed.ranges[day]) ? parsed.ranges[day] : [];
                timeData[day].ranges = arr
                    .filter(r => r && r.start && r.end)
                    .map(r => ({
                        start: r.start,
                        end: r.end,
                        payment: normalizePaymentDigits(r.payment)
                    }));

                const iv = Number(parsed?.intervalByDay?.[day]);
                if (ALLOWED_INTERVALS.has(iv)) timeData[day].interval = iv;
                else {
                    const legacyIv = Number(parsed?.[day]?.interval);
                    if (ALLOWED_INTERVALS.has(legacyIv)) timeData[day].interval = legacyIv;
                }
            });
        } else {
            // 레거시 구조만 있으면, day.open/close -> ranges 1개로 변환
            DAYS.forEach((day) => {
                const old = parsed?.[day];
                if (old?.open && old?.close) {
                    timeData[day].ranges = [{
                        start: old.open,
                        end: old.close,
                        payment: normalizePaymentDigits(old.payment)
                    }];
                    const iv = Number(old.interval);
                    if (ALLOWED_INTERVALS.has(iv)) timeData[day].interval = iv;
                }
            });
        }
    } catch (e) {
        console.warn("시간 JSON 파싱 실패. 기본값 사용", e);
    }

    /* -------------------------------
     * 4. DOM 요소
     * ------------------------------- */
    const dayTabs = document.querySelectorAll(".day-tab");
    const timeSlotsList = document.getElementById("timeSlotsList");
    const activeDaysSummary = document.getElementById("activeDaysSummary");
    const reservationHidden = document.getElementById("reservationTimeInput");

    // 단일 추가
    const btnSingleAdd = document.getElementById("btnSingleAdd");
    const singleStartTime = document.getElementById("singleStartTime");
    const singleEndTime = document.getElementById("singleEndTime");
    const singlePayment = document.getElementById("singlePayment");
    const singleIntervalEl = document.getElementById("singleInterval") || document.getElementById("intervalSelect");

    // 일괄 추가
    const btnBatchAdd = document.getElementById("btnBatchAdd");
    const batchStartTime = document.getElementById("batchStartTime");
    const batchEndTime = document.getElementById("batchEndTime");
    const batchPayment = document.getElementById("batchPayment");
    const batchIntervalEl = document.getElementById("batchInterval") || document.getElementById("batchIntervalSelect");

    // 예약 활성화
    const rsEl = document.getElementById("rsPosible");
    const timeBox = document.getElementById("timeSettingBox");

    attachPaymentFormatter(singlePayment);
    attachPaymentFormatter(batchPayment);

    /* -------------------------------
     * 5. 선택 상태
     * ------------------------------- */
    let currentDay = null;
    let selectedDays = new Set();

    /* -------------------------------
     * 6. 겹침(오버랩) 체크
     *    - 요구가 “중복되지 않는다면 더 담기”이므로
     *      기본은 겹치면 막는다.
     * ------------------------------- */
    function isOverlapping(day, start, end) {
        const s = timeToMinutes(start);
        const e = timeToMinutes(end);
        return (timeData[day].ranges || []).some(r => {
            const rs = timeToMinutes(r.start);
            const re = timeToMinutes(r.end);
            return s < re && rs < e; // overlap
        });
    }

    /* -------------------------------
     * 7. 좌측: range 목록 렌더 (개별 삭제)
     * ------------------------------- */
    function renderTimeRanges(day) {
        if (!timeSlotsList) return;

        if (!day) {
            timeSlotsList.innerHTML = `<div class="no-slots-message">요일을 선택해주세요.</div>`;
            return;
        }

        const ranges = (timeData[day].ranges || []).slice().sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));

        if (ranges.length === 0) {
            timeSlotsList.innerHTML = `<div class="no-slots-message">아래 입력으로 시간 구간을 추가하세요.</div>`;
            return;
        }

        timeSlotsList.innerHTML = ranges.map((r, idx) => {
            const pay = r.payment ? ` (${formatWon(r.payment)})` : "";
            return `
                <div class="time-slot-row" data-index="${idx}" style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                    <div>${r.start} ~ ${r.end}${pay}</div>
                    <button type="button" class="btn-delete-range" data-index="${idx}" title="삭제">삭제</button>
                </div>
            `;
        }).join("");

        timeSlotsList.querySelectorAll(".btn-delete-range").forEach(btn => {
            btn.addEventListener("click", function () {
                const idx = Number(this.dataset.index);
                if (Number.isNaN(idx)) return;

                const sorted = (timeData[day].ranges || []).slice().sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));
                const target = sorted[idx];
                if (!target) return;

                timeData[day].ranges = (timeData[day].ranges || []).filter(r =>
                    !(r.start === target.start && r.end === target.end && (r.payment ?? null) === (target.payment ?? null))
                );

                renderTimeRanges(day);
                updateReservationTime();
                updateActiveDaysSummary();
            });
        });
    }

    /* -------------------------------
     * 8. 우측: 슬롯 요약 렌더 (공백 유지)
     * ------------------------------- */
    function updateActiveDaysSummary() {
        if (!activeDaysSummary) return;

        if (!isReservationEnabled()) {
            activeDaysSummary.innerHTML = `<div class="no-active-days">예약하기가 비활성화되어 있습니다.</div>`;
            return;
        }

        const items = [];

        ORDERED_DAYS.forEach(day => {
            const ranges = timeData[day].ranges || [];
            if (ranges.length === 0) return;

            const interval = timeData[day].interval || DEFAULT_INTERVAL;
            const slots = buildSlotsFromRanges(ranges, interval);

            // 핵심: ranges 기반 슬롯이므로 13~15 같은 공백은 생성되지 않음
            if (slots.length === 0) return;

            const slotText = slots.map(s => {
                const pay = s.payment ? ` (${formatWon(s.payment)})` : "";
                return `${s.start}~${s.end}${pay}`;
            }).join("<br> ");

            items.push({ day, slotText, interval });
        });

        if (items.length === 0) {
            activeDaysSummary.innerHTML = `<div class="no-active-days">설정된 예약 가능 시간이 없습니다.</div>`;
            return;
        }

        activeDaysSummary.innerHTML = items.map(it => `
            <div class="active-day-item" data-day="${it.day}">
                <div class="active-day-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                    <div class="active-day-label">${DAY_LABELS[it.day]} (interval: ${it.interval}분)</div>
                    <button type="button"
        class="btn-delete-day"
        data-day="${it.day}"
        title="이 요일의 모든 시간 구간 삭제">
    <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9z"/>
    </svg>
</button>
                </div>
                <div class="active-day-slots">${it.slotText}</div>
            </div>
        `).join("");

        // 요일 전체 삭제
        activeDaysSummary.querySelectorAll(".btn-delete-day").forEach(btn => {
            btn.addEventListener("click", function () {
                const day = this.dataset.day;
                if (!day) return;

                if (confirm(`${DAY_LABELS[day]}의 모든 시간 구간을 삭제하시겠습니까?`)) {
                    timeData[day].ranges = [];

                    selectedDays.delete(day);
                    const tab = document.querySelector(`.day-tab[data-day="${day}"]`);
                    if (tab) tab.classList.remove("active");

                    if (currentDay === day) {
                        if (selectedDays.size > 0) {
                            currentDay = Array.from(selectedDays)[0];
                            renderTimeRanges(currentDay);
                        } else {
                            currentDay = null;
                            renderTimeRanges(null);
                        }
                    }

                    updateReservationTime();
                    updateActiveDaysSummary();
                    updateMultiSelectUI();
                }
            });
        });
    }

    /* -------------------------------
     * 9. hidden 저장 JSON 생성 (서버 호환 + 확장 ranges)
     *    - server 호환: day.open/close/interval/payment/active
     *    - 확장: ranges, intervalByDay
     * ------------------------------- */
    function updateReservationTime() {
        if (!reservationHidden) return;

        if (!isReservationEnabled()) {
            reservationHidden.value = "{}";
            return;
        }

        const output = {};

        DAYS.forEach(day => {
            const ranges = (timeData[day].ranges || []).filter(r => r?.start && r?.end && r.start < r.end);
            const interval = timeData[day].interval || DEFAULT_INTERVAL;

            if (ranges.length === 0) {
                output[day] = { open: null, close: null, interval, payment: null, active: false };
                return;
            }

            // 서버용 open/close는 min/max로만 제공 (연속 슬롯 생성 금지)
            const starts = ranges.map(r => timeToMinutes(r.start));
            const ends = ranges.map(r => timeToMinutes(r.end));
            const open = minutesToTime(Math.min(...starts));
            const close = minutesToTime(Math.max(...ends));

            // payment는 구간별로 다를 수 있으니 단일값이면 유지, 다르면 null
            const paySet = new Set(ranges.map(r => r.payment ?? ""));
            let paymentOut = null;
            if (paySet.size === 1) {
                const only = Array.from(paySet)[0];
                paymentOut = only === "" ? null : only;
            }

            output[day] = { open, close, interval, payment: paymentOut, active: true };
        });

        // 확장 데이터(관리 화면 재진입/수정용)
        output.ranges = {};
        output.intervalByDay = {};
        DAYS.forEach(day => {
            output.ranges[day] = (timeData[day].ranges || []).map(r => ({
                start: r.start,
                end: r.end,
                payment: r.payment ?? null
            }));
            output.intervalByDay[day] = timeData[day].interval || DEFAULT_INTERVAL;
        });

        console.log("저장되는 데이터:", output);
        reservationHidden.value = JSON.stringify(output);
    }

    /* -------------------------------
     * 10. 요일 탭 클릭: 다중 선택 토글
     * ------------------------------- */
    dayTabs.forEach(tab => {
        tab.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();

            const day = this.dataset.day;
            if (!day) return;

            if (selectedDays.has(day)) {
                selectedDays.delete(day);
                this.classList.remove("active");

                if (selectedDays.size === 0) {
                    currentDay = null;
                    renderTimeRanges(null);
                } else {
                    currentDay = Array.from(selectedDays)[0];
                    renderTimeRanges(currentDay);
                }
            } else {
                selectedDays.add(day);
                this.classList.add("active");
                currentDay = day;
                renderTimeRanges(day);
            }

            updateMultiSelectUI();
            updateActiveDaysSummary();
        });
    });

    /* -------------------------------
     * 10-1. 다중 선택 UI 업데이트
     * ------------------------------- */
    function updateMultiSelectUI() {
        const multiSelectActions = document.getElementById("multiSelectActions");
        const singleDayAddSection = document.getElementById("singleDayAddSection");
        const selectedDaysCount = document.getElementById("selectedDaysCount");

        if (!multiSelectActions || !singleDayAddSection || !selectedDaysCount) return;

        if (selectedDays.size > 1) {
            multiSelectActions.style.display = "block";
            singleDayAddSection.style.display = "none";
            selectedDaysCount.textContent = selectedDays.size;
        } else if (selectedDays.size === 1) {
            multiSelectActions.style.display = "none";
            singleDayAddSection.style.display = "block";
            const day = Array.from(selectedDays)[0];
            currentDay = day;
            renderTimeRanges(day);
        } else {
            multiSelectActions.style.display = "none";
            singleDayAddSection.style.display = "none";
        }
    }

    /* -------------------------------
     * 11. 단일 구간 추가 (겹침 방지 + interval 저장)
     * ------------------------------- */
    if (btnSingleAdd) {
        btnSingleAdd.addEventListener("click", function () {
            if (selectedDays.size !== 1) {
                alert("요일을 하나만 선택해주세요.");
                return;
            }

            const day = currentDay || Array.from(selectedDays)[0];
            if (!day) {
                alert("요일을 선택해주세요.");
                return;
            }

            const start = singleStartTime?.value;
            const end = singleEndTime?.value;

            if (!start || !end) {
                alert("시작 시간과 종료 시간을 모두 입력해주세요.");
                return;
            }
            if (start >= end) {
                alert("시작 시간은 종료 시간보다 빨라야 합니다.");
                return;
            }

            const interval = getIntervalFromEl(singleIntervalEl, timeData[day].interval || DEFAULT_INTERVAL);
            timeData[day].interval = interval;

            const payment = normalizePaymentDigits(singlePayment?.value);

            // 핵심: 겹치지 않으면 추가 가능
            if (isOverlapping(day, start, end)) {
                alert("이미 설정된 시간 구간과 겹칩니다. 겹치지 않게 설정해주세요.");
                return;
            }

            // 완전 동일 구간 중복 방지(겹침과 별개)
            const exactDup = (timeData[day].ranges || []).some(r => r.start === start && r.end === end && (r.payment ?? null) === (payment ?? null));
            if (!exactDup) {
                timeData[day].ranges.push({ start, end, payment });
            }

            renderTimeRanges(day);
            updateReservationTime();
            updateActiveDaysSummary();
        });
    }

    /* -------------------------------
     * 12. 일괄 구간 추가 (다중 요일)
     * ------------------------------- */
    if (btnBatchAdd) {
        btnBatchAdd.addEventListener("click", function () {
            if (selectedDays.size < 2) {
                alert("여러 요일을 선택해주세요.");
                return;
            }

            const start = batchStartTime?.value;
            const end = batchEndTime?.value;

            if (!start || !end) {
                alert("시작 시간과 종료 시간을 모두 입력해주세요.");
                return;
            }
            if (start >= end) {
                alert("시작 시간은 종료 시간보다 빨라야 합니다.");
                return;
            }

            const interval = getIntervalFromEl(batchIntervalEl, DEFAULT_INTERVAL);
            const payment = normalizePaymentDigits(batchPayment?.value);

            // 안전: 하나라도 겹치면 중단
            for (const day of selectedDays) {
                if (isOverlapping(day, start, end)) {
                    alert(`${DAY_LABELS[day]}에 이미 겹치는 시간 구간이 있습니다. 먼저 삭제하거나 겹치지 않게 설정하세요.`);
                    return;
                }
            }

            selectedDays.forEach(day => {
                timeData[day].interval = interval;

                const exactDup = (timeData[day].ranges || []).some(r => r.start === start && r.end === end && (r.payment ?? null) === (payment ?? null));
                if (!exactDup) {
                    timeData[day].ranges.push({ start, end, payment });
                }
            });

            const selectedCount = selectedDays.size;

            // UX 유지: 완료 후 선택 해제/초기화
            selectedDays.clear();
            dayTabs.forEach(t => t.classList.remove("active"));
            currentDay = null;
            renderTimeRanges(null);

            updateMultiSelectUI();
            updateReservationTime();
            updateActiveDaysSummary();

            alert(`${selectedCount}개 요일에 시간 구간이 추가되었습니다.`);
        });
    }

    /* -------------------------------
     * 13. 예약 활성화 토글 (rsPosible)
     * ------------------------------- */
    function toggleTimeBox() {
        if (!timeBox) return;

        if (isReservationEnabled()) {
            timeBox.classList.remove("time-disabled");
        } else {
            timeBox.classList.add("time-disabled");
            if (reservationHidden) reservationHidden.value = "{}";
        }
        updateActiveDaysSummary();
    }

    if (rsEl) {
        rsEl.addEventListener("change", toggleTimeBox);
        rsEl.addEventListener("input", toggleTimeBox); // select 대응
    }

    /* -------------------------------
     * 14. 저장 버튼 → JSON 저장
     * ------------------------------- */
    const saveBtn = document.querySelector(".btn-save-all");
    if (saveBtn) {
        saveBtn.addEventListener("click", function () {
            updateReservationTime();
        });
    }

    /* -------------------------------
     * 15. 이미지 미리보기
     * ------------------------------- */
    const photoInput = document.getElementById("photoInput");
    const previewImage = document.getElementById("previewImage");
    const previewPlaceholder = document.getElementById("previewPlaceholder");

    if (photoInput) {
        photoInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;

            if (!file.type.startsWith("image/")) {
                alert("이미지 파일만 업로드 가능합니다.");
                return;
            }

            const reader = new FileReader();
            reader.onload = function (e) {
                if (previewPlaceholder) previewPlaceholder.style.display = "none";
                if (previewImage) {
                    previewImage.style.display = "block";
                    previewImage.src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        });
    }

    /* -------------------------------
     * 16. 폼 submit (첨부파일 포함)
     * ------------------------------- */
    const form = document.getElementById("modifyForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        updateReservationTime();

        const formData = new FormData(form);

        // fileupload.js에서 관리되는 selectedFiles 그대로 사용
        if (typeof selectedFiles !== "undefined") {
            selectedFiles.forEach(file => {
                formData.append("attachment_files", file);
            });
        }

        fetch(form.action, {
            method: "POST",
            body: formData
        }).then(res => {
            if (res.redirected) window.location.href = res.url;
        });
    });

    /* -------------------------------
     * 17. 초기 렌더링
     * ------------------------------- */
    renderTimeRanges(null);
    updateMultiSelectUI();
    toggleTimeBox();
    updateReservationTime();
    updateActiveDaysSummary();
});
