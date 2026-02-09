document.addEventListener('DOMContentLoaded', function() {
    // 1. 예약/모집글 일별 추이
    const dailyTrendCtx = document.getElementById('dailyTrendChart');
    if (dailyTrendCtx) {
        const recruitment = dailyRecruitment || {};
        const reservations = dailyReservations || {};
        
        // 날짜 정렬
        const allDates = [...new Set([...Object.keys(recruitment), ...Object.keys(reservations)])].sort();
        
        const recruitmentData = allDates.map(date => recruitment[date] || 0);
        const reservationData = allDates.map(date => reservations[date] || 0);
        
        new Chart(dailyTrendCtx, {
            type: 'line',
            data: {
                labels: allDates,
                datasets: [{
                    label: '모집글',
                    data: recruitmentData,
                    borderColor: 'rgb(52, 152, 219)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '예약',
                    data: reservationData,
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 2. 모집 완료 추이
    const completionCtx = document.getElementById('completionChart');
    if (completionCtx) {
        const trend = completionTrend || {};
        const labels = Object.keys(trend).sort();
        const totalData = labels.map(date => trend[date]?.total || 0);
        const completedData = labels.map(date => trend[date]?.completed || 0);
        
        new Chart(completionCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '전체',
                    data: totalData,
                    backgroundColor: 'rgba(149, 165, 166, 0.5)'
                }, {
                    label: '완료',
                    data: completedData,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 3. 회원 가입 추이
    const memberCtx = document.getElementById('memberChart');
    if (memberCtx) {
        const members = dailyMembers || {};
        const labels = Object.keys(members).sort();
        const memberData = labels.map(date => members[date] || 0);
        
        new Chart(memberCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '신규 회원',
                    data: memberData,
                    borderColor: 'rgb(155, 89, 182)',
                    backgroundColor: 'rgba(155, 89, 182, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 4. 성별 분포 비교 (전체/예약자/참여자)
    const genderCtx = document.getElementById('genderChart');
    if (genderCtx) {
        const gender = genderData || {};
        const reservationGender = reservationGenderData || {};
        const participationGender = participationGenderData || {};
        
        const labels = ['남성', '여성'];
        const allData = [gender['0'] || 0, gender['1'] || 0];
        const reservationData = [reservationGender['0'] || 0, reservationGender['1'] || 0];
        const participationData = [participationGender['0'] || 0, participationGender['1'] || 0];
        
        new Chart(genderCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '전체 회원',
                    data: allData,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)'
                }, {
                    label: '예약자',
                    data: reservationData,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }, {
                    label: '참여자',
                    data: participationData,
                    backgroundColor: 'rgba(155, 89, 182, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 5. 예약 취소율 추이
    const cancellationRateCtx = document.getElementById('cancellationRateChart');
    if (cancellationRateCtx) {
        const cancellationData = dailyCancellationRate || {};
        const labels = Object.keys(cancellationData).sort();
        const rateData = labels.map(date => cancellationData[date]?.rate || 0);
        const totalData = labels.map(date => cancellationData[date]?.total || 0);
        const cancelledData = labels.map(date => cancellationData[date]?.cancelled || 0);
        
        new Chart(cancellationRateCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '취소율 (%)',
                    data: rateData,
                    borderColor: 'rgb(231, 76, 60)',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                }, {
                    label: '전체 예약',
                    data: totalData,
                    borderColor: 'rgba(149, 165, 166, 0.5)',
                    backgroundColor: 'rgba(149, 165, 166, 0.1)',
                    type: 'bar',
                    yAxisID: 'y1'
                }, {
                    label: '취소',
                    data: cancelledData,
                    borderColor: 'rgba(231, 76, 60, 0.5)',
                    backgroundColor: 'rgba(231, 76, 60, 0.3)',
                    type: 'bar',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '취소율 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '예약 수'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    // 6. 참여율 추이
    const participationRateCtx = document.getElementById('participationRateChart');
    if (participationRateCtx) {
        const participationData = dailyParticipationRate || {};
        const labels = Object.keys(participationData).sort();
        const rateData = labels.map(date => participationData[date]?.rate || 0);
        const totalData = labels.map(date => participationData[date]?.total || 0);
        const completedData = labels.map(date => participationData[date]?.completed || 0);
        
        new Chart(participationRateCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '참여율 (%)',
                    data: rateData,
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                }, {
                    label: '전체 참가',
                    data: totalData,
                    borderColor: 'rgba(149, 165, 166, 0.5)',
                    backgroundColor: 'rgba(149, 165, 166, 0.1)',
                    type: 'bar',
                    yAxisID: 'y1'
                }, {
                    label: '완료',
                    data: completedData,
                    borderColor: 'rgba(46, 204, 113, 0.5)',
                    backgroundColor: 'rgba(46, 204, 113, 0.3)',
                    type: 'bar',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '참여율 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '참가 수'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    // 7. 게시판 통계
    const boardCtx = document.getElementById('boardChart');
    if (boardCtx && boardStats && boardStats.length > 0) {
        const boardLabels = boardStats.map(b => b.board_id__board_name || '기타');
        const boardData = boardStats.map(b => b.count);
        
        new Chart(boardCtx, {
            type: 'bar',
            data: {
                labels: boardLabels,
                datasets: [{
                    label: '게시글 수',
                    data: boardData,
                    backgroundColor: 'rgba(241, 196, 15, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else if (boardCtx) {
        // 데이터가 없을 때
        boardCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">게시판 데이터가 없습니다.</p>';
    }

});

