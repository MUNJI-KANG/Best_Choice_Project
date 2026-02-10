document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const contextInput = document.querySelector("#contextInput");

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (window.editorInstance) {
            contextInput.value = window.editorInstance.getHTML();
        }

        const formData = new FormData(form);

        selectedFiles.forEach(file => {
            formData.append("file", file);
        });

        fetch(form.action, {
            method: "POST",
            body: formData
        })
            .then(res => {
                if (res.redirected) window.location.href = res.url;
            });
    });

})