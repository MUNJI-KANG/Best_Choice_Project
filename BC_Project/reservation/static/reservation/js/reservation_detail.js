document.addEventListener("DOMContentLoaded", function () {
    /* ---------------------------
        0) 예약 가능 여부 체크
    ---------------------------- */
    const rsPossibleEl = document.getElementById("rs-possible");
    const rsPossible = rsPossibleEl ? rsPossibleEl.value : "1";
    if (rsPossible !== "1") return;

    /* ---------------------------
        1) 데이터 로드
    ---------------------------- */
    const reservationJsonEl = document.getElementById("reservation-json");
    const reservedJsonEl = document.getElementById("reserved-json");

    const reservationTime = JSON.parse(reservationJsonEl?.textContent || "{}");
    const reservedData = JSON.parse(reservedJsonEl?.textContent || "[]");

    const facilityId = document.getElementById("facility-id")?.value;

    const slotGrid = document.getElementById("time-slot-grid");
    const selectedDateEl = document.getElementById("selected-date");
    const selectedTimeEl = document.getElementById("selected-time");

    let pricePerSlot = 0;
    let selectedSlots = []; // [{start, end}]

    if (!slotGrid || !selectedDateEl || !selectedTimeEl) {
        console.error("필수 DOM 누락: time-slot-grid / selected-date / selected-time");
        return;
    }

    /* ---------------------------
        2) 총 금액 및 선택 시간 표시
    ---------------------------- */
    function updateTotal() {
        const total = selectedSlots.length * pricePerSlot;
        const totalEl = document.getElementById("total-price");
        if (totalEl) totalEl.textContent = `${total.toLocaleString("ko-KR")}원`;

        selectedTimeEl.textContent = selectedSlots.length
            ? selectedSlots.map(s => `${s.start} ~ ${s.end}`).join(", ")
            : "-";
    }

    /* ---------------------------
        3) 시간 유틸
    ---------------------------- */
    function timeToMinutes(t) {
        const [h, m] = String(t).split(":").map(Number);
        return h * 60 + m;
    }

    function minutesToTime(min) {
        const h = String(Math.floor(min / 60)).padStart(2, "0");
        const m = String(min % 60).padStart(2, "0");
        return `${h}:${m}`;
    }

    /* ---------------------------
        4) range 기반 슬롯 생성 (핵심)
        - open~close 연속 생성 금지
    ---------------------------- */
    function buildSlotsFromRanges(ranges, interval) {
        const slots = [];
        const seen = new Set();

        const iv = Number(interval);
        if (!iv || iv <= 0) return slots;

        (ranges || []).forEach(r => {
            const start = r?.start;
            const end = r?.end;
            if (!start || !end) return;

            const startMin = timeToMinutes(start);
            const endMin = timeToMinutes(end);
            if (!(startMin < endMin)) return;

            for (let t = startMin; t + iv <= endMin; t += iv) {
                const s = minutesToTime(t);
                const e = minutesToTime(t + iv);
                const key = `${s}-${e}`;

                if (seen.has(key)) continue;
                seen.add(key);
                slots.push({ start: s, end: e });
            }
        });

        slots.sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));
        return slots;
    }

    /* ---------------------------
        5) dayInfo + dayRanges + interval 결정
        - 네 JSON 구조에 맞게 reservationTime.ranges[day]에서 꺼냄
    ---------------------------- */
    function getDayContext(dayOfWeek) {
        const dayInfo = reservationTime?.[dayOfWeek] || null;

        const rangesByDay = reservationTime?.ranges || {};
        const dayRanges = Array.isArray(rangesByDay?.[dayOfWeek]) ? rangesByDay[dayOfWeek] : [];

        const intervalByDay = reservationTime?.intervalByDay || {};
        const interval =
            Number(intervalByDay?.[dayOfWeek]) ||
            Number(dayInfo?.interval) ||
            60;

        return { dayInfo, dayRanges, interval };
    }

    /* ---------------------------
        6) 슬롯 렌더링
        - ranges 있으면 ranges 기준
        - 없으면 open/close fallback
        - 결과가 0이면 메시지 출력(빈 화면 방지)
    ---------------------------- */
    function renderSlotsForDay(dayOfWeek, selectedDateStr) {
        slotGrid.innerHTML = "";
        selectedSlots = [];
        updateTotal();

        const { dayInfo, dayRanges, interval } = getDayContext(dayOfWeek);

        if (!dayInfo || !dayInfo.active) {
            slotGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#777;">휴무일입니다</div>`;
            selectedTimeEl.textContent = "-";
            return;
        }

        // 가격은 기존대로 dayInfo.payment 사용
        pricePerSlot = Number(dayInfo.payment || 0);

        let slots = [];

        // ✅ 1순위: ranges
        if (dayRanges.length > 0) {
            slots = buildSlotsFromRanges(dayRanges, interval);
        } else if (dayInfo.open && dayInfo.close) {
            // ⛑ fallback: 레거시 open/close
            slots = buildSlotsFromRanges([{ start: dayInfo.open, end: dayInfo.close }], interval);
        }

        if (!slots.length) {
            slotGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#777;">예약 가능한 시간이 없습니다</div>`;
            selectedTimeEl.textContent = "-";
            return;
        }

        slots.forEach(slot => {
            const div = document.createElement("div");
            div.classList.add("slot");
            div.textContent = `${slot.start} ~ ${slot.end}`;

            const isReserved = reservedData.some(r =>
                r.date === selectedDateStr &&
                r.start === slot.start &&
                r.end === slot.end
            );

            if (isReserved) {
                div.classList.add("disabled");
                div.style.pointerEvents = "none";
            } else {
                div.addEventListener("click", function () {
                    const key = `${slot.start}-${slot.end}`;
                    const idx = selectedSlots.findIndex(s => `${s.start}-${s.end}` === key);

                    if (idx >= 0) {
                        selectedSlots.splice(idx, 1);
                        div.classList.remove("selected");
                    } else {
                        selectedSlots.push({ start: slot.start, end: slot.end });
                        div.classList.add("selected");
                    }
                    updateTotal();
                });
            }

            slotGrid.appendChild(div);
        });
    }

    /* ---------------------------
        7) 캘린더 설정
    ---------------------------- */
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) {
        console.error("calendar DOM 누락");
        return;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        locale: "ko",
        headerToolbar: { left: "prev", center: "title", right: "next" },

        dateClick: function (info) {
            try {
                const clicked = new Date(info.dateStr);
                clicked.setHours(0, 0, 0, 0);
                if (clicked < today) return;

                document.querySelectorAll(".fc-day-selected")
                    .forEach(cell => cell.classList.remove("fc-day-selected"));

                info.dayEl.classList.add("fc-day-selected");
                selectedDateEl.textContent = info.dateStr;

                const dayOfWeek = clicked.toLocaleString("en-US", { weekday: "long" }).toLowerCase();

                renderSlotsForDay(dayOfWeek, info.dateStr);
            } catch (e) {
                console.error("dateClick 처리 중 오류", e);
                slotGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#777;">시간 데이터를 불러오지 못했습니다</div>`;
            }
        },

        dayCellDidMount: function (arg) {
            try {
                const cellDate = new Date(arg.date);
                cellDate.setHours(0, 0, 0, 0);

                if (cellDate < today) {
                    arg.el.classList.add("fc-day-disabled");
                    return;
                }

                const dayOfWeek = cellDate.toLocaleString("en-US", { weekday: "long" }).toLowerCase();
                const dayInfo = reservationTime?.[dayOfWeek];

                if (!dayInfo || !dayInfo.active) arg.el.classList.add("fc-day-unavailable");
                else arg.el.classList.add("fc-day-available");
            } catch (e) {
                console.error("dayCellDidMount 오류", e);
            }
        }
    });

    calendar.render();

    /* ---------------------------
        8) 예약 버튼
    ---------------------------- */
    const reserveBtn = document.getElementById("reserve-button");
    if (reserveBtn) {
        reserveBtn.addEventListener("click", function () {
            const date = selectedDateEl.textContent;

            if (!date || date === "-" || selectedSlots.length === 0) {
                alert("날짜와 시간을 선택해주세요.");
                return;
            }

            fetch("/reservation/save/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({
                    date: date,
                    slots: selectedSlots,
                    facility_id: facilityId
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.result === "ok") {
                    alert("예약이 완료되었습니다!");
                    window.location.href = "/member/myreservation";
                } else {
                    alert(data.msg);
                }
            });
        });
    }

    /* ---------------------------
        9) CSRF
    ---------------------------- */
    function getCookie(name) {
        let cookieValue = null;
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
        return cookieValue;
    }

    /* ---------------------------
        10) 오늘 날짜 자동 선택 (기존 방식 유지)
    ---------------------------- */
    (function selectToday() {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const todayStr = `${yyyy}-${mm}-${dd}`;

        const todayCell = document.querySelector(`[data-date="${todayStr}"]`);
        if (todayCell) {
            // FullCalendar 내부 이벤트 시뮬레이션
            // (기존 코드 방식 유지)
            try {
                calendar.trigger("dateClick", {
                    date: d,
                    dateStr: todayStr,
                    dayEl: todayCell
                });
            } catch (e) {
                // trigger가 없는 버전도 있어 직접 호출 fallback
                selectedDateEl.textContent = todayStr;
                const dayOfWeek = d.toLocaleString("en-US", { weekday: "long" }).toLowerCase();
                renderSlotsForDay(dayOfWeek, todayStr);
            }
        }
    })();
});
