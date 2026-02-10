document.addEventListener('DOMContentLoaded', function () {

    const pinTopCheckbox = document.querySelector("input[name='pin_top']");
    const noticeSection = document.querySelector(".notice-section");
    const noticeTypeRadios = document.querySelectorAll("input[name='notice_type']");
    const dateSection = document.getElementById("date-section");
    const startDateInput = document.querySelector("input[name='start_date']");
    const endDateInput = document.querySelector("input[name='end_date']");

    if (pinTopCheckbox && noticeSection) {

        function toggleDateInputs() {
            const checked = document.querySelector("input[name='notice_type']:checked");
            if (!checked) return;

            if (checked.value === "always") {
                dateSection.classList.add("hidden");
                startDateInput.disabled = true;
                endDateInput.disabled = true;
            } else {
                dateSection.classList.remove("hidden");
                startDateInput.disabled = false;
                endDateInput.disabled = false;
            }
        }

        function toggleNoticeSection() {
            const isPinned = pinTopCheckbox.checked;

            if (!isPinned) {
                noticeSection.classList.add("hidden");
                dateSection.classList.add("hidden");

                noticeTypeRadios.forEach(r => r.disabled = true);
                startDateInput.disabled = true;
                endDateInput.disabled = true;
            } else {
                noticeSection.classList.remove("hidden");

                noticeTypeRadios.forEach(r => r.disabled = false);
                toggleDateInputs();
            }
        }

        pinTopCheckbox.addEventListener("change", toggleNoticeSection);
        noticeTypeRadios.forEach(radio => {
            radio.addEventListener("change", toggleDateInputs);
        });

        toggleNoticeSection();
    }


    const form = document.querySelector("form");
    const contextInput = document.querySelector("#contextInput");
    const fileInput = document.getElementById("fileInput");

    if (!form) return;

    form.addEventListener("submit", function () {


        const faqTextarea = document.querySelector("textarea[name='context']");
        if (faqTextarea) {
            // 아무것도 건드릴 필요 없음
            return;
        }


        if (window.editorInstance && contextInput) {
            contextInput.value = window.editorInstance.getHTML();
        }

        if (window.selectedFiles && fileInput) {
            const dt = new DataTransfer();
            window.selectedFiles.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
        }

        // 🔥 fetch 사용 금지! 기본 form submit 사용
    });

});
