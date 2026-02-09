document.addEventListener("DOMContentLoaded", function () {
    /* 모집글 목록 렌더링 */
    function renderRecruitmentList(data) {
        const box = document.getElementById("facilityList");
        box.innerHTML = "";

        if (!data || data.length === 0) {
            box.innerHTML = `<tr><td colspan="5">등록된 모집글이 없습니다.</td></tr>`;
            return;
        }

        box.innerHTML = data.map(item => `
            <tr ${item.delete_date ? 'style="opacity: 0.6; background-color: #f5f5f5;"' : ''}>
                <td>${item.row_no}</td>
                <td><input type="checkbox" value="${item.id}"></td>
                <td><a href="detail/${item.id}/" style="color: inherit; text-decoration: none;">${item.title}</a></td>
                <td>${item.author}</td>
                <td>${item.delete_date || '-'}</td>
            </tr>
        `).join("");
    }

    /* JSON 파싱 */
    try {
        const list = JSON.parse(document.getElementById("facilityData").textContent.trim());
        renderRecruitmentList(list);
    } catch (e) {
        console.error("JSON 오류:", e);
        document.getElementById("facilityList").innerHTML = `<tr><td colspan="5">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>`;
    }

    /* CSRF 토큰 가져오기 */
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
    const csrftoken = getCookie('csrftoken');

    /* 삭제 버튼 클릭 이벤트 */
    document.querySelector('.delete-btn').addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('#facilityList input[type="checkbox"]:checked');
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

        if (ids.length === 0) {
            alert('삭제할 항목을 선택해주세요.');
            return;
        }

        if (!confirm(`선택한 ${ids.length}개의 모집글을 삭제하시겠습니까?`)) {
            return;
        }

        fetch('/manager/recruitment/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ ids: ids })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                alert(`${data.deleted}개의 모집글이 삭제되었습니다.`);
                location.reload();
            } else {
                alert('삭제 중 오류가 발생했습니다: ' + data.msg);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('삭제 중 오류가 발생했습니다.');
        });
    });


    /* 영구 삭제 버튼 클릭 이벤트 */
    document.querySelector('.hard-delete-btn').addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('#facilityList input[type="checkbox"]:checked');
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

        if (ids.length === 0) {
            alert('영구 삭제할 항목을 선택해주세요.');
            return;
        }

        if (!confirm(`선택한 ${ids.length}개의 모집글을 영구 삭제하시겠습니까?`)) {
            return;
        }

        fetch('/manager/recruitment/harddelete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ ids: ids })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                alert(`${data.deleted}개의 모집글이 영구 삭제되었습니다.`);
                location.reload();
            } else {
                alert('영구 삭제 중 오류가 발생했습니다: ' + data.msg);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('영구 삭제 중 오류가 발생했습니다.');
        });
    });



    /* 복구 버튼 클릭 이벤트 */
    document.querySelector('.restore-btn').addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('#facilityList input[type="checkbox"]:checked');
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

        if (ids.length === 0) {
            alert('복구할 항목을 선택해주세요.');
            return;
        }

        if (!confirm(`선택한 ${ids.length}개의 모집글을 복구하시겠습니까?`)) {
            return;
        }

        fetch('/manager/recruitment/restore/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ ids: ids })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                alert(`${data.restore}개의 모집글이 복구되었습니다.`);
                location.reload();
            } else {
                alert('복구 중 오류가 발생했습니다: ' + data.msg);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('복구 중 오류가 발생했습니다.');
        });
    });
});