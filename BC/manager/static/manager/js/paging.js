document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const perPageEl = document.getElementById("perPageSelect");

    if (perPageEl) {
        const nowPer = params.get("per_page") || "15";
        perPageEl.value = nowPer;

        perPageEl.addEventListener("change", function () {
            params.set("per_page", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }
});


