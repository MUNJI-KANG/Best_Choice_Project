document.addEventListener('DOMContentLoaded', function () {

    window.selectedFiles = [];

    document.querySelectorAll(".delete-existing-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const fileId = this.dataset.fileId;

            this.parentElement.remove();

            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "delete_files";
            hidden.value = fileId;

            document.querySelector("form").appendChild(hidden);
        });
    });

    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            Array.from(fileInput.files).forEach(file => {
                window.selectedFiles.push(file);
            });
            fileInput.value = "";
            renderFileList();
        });
    }

    function renderFileList() {
        if (!fileList) return;

        fileList.innerHTML = "";

        window.selectedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.style = "display:flex; align-items:center; gap:8px; padding:4px 0;";

            item.innerHTML = `
                <span>${file.name}</span>
                <button type="button" class="delete-file-btn" data-index="${index}"
                    style="background:#ff4d4d; color:white; border:none; padding:2px 6px; cursor:pointer; border-radius:3px;">
                    X
                </button>
            `;
            fileList.appendChild(item);
        });

        document.querySelectorAll(".delete-file-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                const idx = this.dataset.index;
                window.selectedFiles.splice(idx, 1);
                renderFileList();
            });
        });
    }
});
