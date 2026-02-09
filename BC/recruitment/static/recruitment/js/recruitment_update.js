// recruitment_update.js

// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_submit   = document.querySelector(".btn-update");
    const btn_list     = document.querySelector(".btn-list");
    const recruit_form = document.querySelector("#recruit_form");  // 폼이 있으면 여기로

    // 1) 작성(수정 완료) 버튼
    if (btn_submit) {
        btn_submit.addEventListener("click", function (e) {
            // 기본 동작 그대로 쓰려면 막을 필요 없음
            // e.preventDefault();
            recruit_form.submit();   // -> Django update view 로 POST
        });
    }

    // 2) 목록 버튼
    if (btn_list) {
        btn_list.addEventListener("click", function (e) {
            e.preventDefault();
            handle_list();
        });
    }


    //  3) 파일 2MB 이상 + 누적 선택
    const updateFileInput = document.getElementById('updateFileInput');
    const updateFileList  = document.getElementById('updateFileList');
    let updatedFiles = [];

    if (updateFileInput && updateFileList) {
        updateFileInput.addEventListener('change', function (e) {
            const maxSize  = 2 * 1024 * 1024;
            const newFiles = Array.from(e.target.files);

            let merged = [...updatedFiles];

            for (const f of newFiles) {
                if (f.size > maxSize) {
                    alert(`"${f.name}" 은(는) 2MB를 초과하여 업로드할 수 없습니다.`);
                    updateFileInput.value = "";
                    return;
                }
                merged.push(f);
            }

            const dt = new DataTransfer();
            merged.forEach(f => dt.items.add(f));
            updateFileInput.files = dt.files;
            updatedFiles          = Array.from(dt.files);

            renderUpdateFileList();
        });

        function renderUpdateFileList() {
            updateFileList.innerHTML = '';

            updatedFiles.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.innerHTML = `
                    <span class="file-item-name">${file.name}</span>
                    <button type="button" class="file-item-remove" data-index="${index}">✕</button>
                `;
                updateFileList.appendChild(item);

                item.querySelector('.file-item-remove')
                    .addEventListener('click', () => {
                        const dt = new DataTransfer();
                        const remain = Array
                            .from(updateFileInput.files)
                            .filter((_, i) => i !== index);

                        remain.forEach(f => dt.items.add(f));
                        updateFileInput.files = dt.files;
                        updatedFiles          = Array.from(dt.files);
                        renderUpdateFileList();
                    });
            });
        }
    }


    
});

// 목록 이동
function handle_list() {
    // 실제 리스트 URL에 맞게 수정해서 쓰시면 됩니다.
    window.location.href = "/recruitment";
}

// Editor 내용을 form submit 시 hidden input에 저장
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('recruit_form');
    const contentInput = document.getElementById('contentInput');

    if (form && contentInput) {
        form.addEventListener('submit', function (e) {
            if (window.editorInstance) {
                contentInput.value = window.editorInstance.getHTML();
            }
        });
    }
});