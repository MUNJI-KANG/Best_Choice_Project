document.addEventListener('DOMContentLoaded', function() {
    // 1. 연도별 안전점검 추세
    const yearlyInspectionCtx = document.getElementById('yearlyInspectionChart');
    if (yearlyInspectionCtx) {
        const trend = yearlyInspectionTrend || {};
        const labels = Object.keys(trend).sort();
        const data = labels.map(year => trend[year] || 0);
        
        if (labels.length > 0) {
            new Chart(yearlyInspectionCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '점검 건수',
                        data: data,
                        borderColor: 'rgb(52, 152, 219)',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointHoverRadius: 7
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
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '점검 건수'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '연도'
                            }
                        }
                    }
                }
            });
        } else {
            yearlyInspectionCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">안전점검 데이터가 없습니다.</p>';
        }
    }

    // 2. 등급별 분포
    const gradeDistributionCtx = document.getElementById('gradeDistributionChart');
    if (gradeDistributionCtx) {
        const distribution = gradeDistribution || {};
        const labels = Object.keys(distribution);
        const data = labels.map(grade => distribution[grade] || 0);
        
        if (labels.length > 0) {
            // 등급별 색상 매핑
            const gradeColors = {
                '양호': 'rgba(46, 204, 113, 0.8)',
                '주의': 'rgba(241, 196, 15, 0.8)',
                '경고': 'rgba(231, 76, 60, 0.8)'
            };
            
            const colors = labels.map(grade => gradeColors[grade] || 'rgba(149, 165, 166, 0.8)');
            
            new Chart(gradeDistributionCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        }
                    }
                }
            });
        } else {
            gradeDistributionCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">등급 데이터가 없습니다.</p>';
        }
    }

    // 3. 지역별 안전점검 통계
    const regionInspectionCtx = document.getElementById('regionInspectionChart');
    if (regionInspectionCtx) {
        const stats = regionInspectionStats || {};
        const regions = Object.keys(stats);
        
        if (regions.length > 0) {
            // 등급별로 데이터 정리
            const allGrades = new Set();
            regions.forEach(region => {
                Object.keys(stats[region]).forEach(grade => allGrades.add(grade));
            });
            const gradeList = Array.from(allGrades);
            
            const datasets = gradeList.map((grade, index) => {
                const gradeColors = {
                    '양호': 'rgba(46, 204, 113, 0.7)',
                    '주의': 'rgba(241, 196, 15, 0.7)',
                    '경고': 'rgba(231, 76, 60, 0.7)'
                };
                
                return {
                    label: grade,
                    data: regions.map(region => stats[region][grade] || 0),
                    backgroundColor: gradeColors[grade] || `rgba(${100 + index * 50}, ${150 + index * 30}, ${200 + index * 20}, 0.7)`
                };
            });
            
            new Chart(regionInspectionCtx, {
                type: 'bar',
                data: {
                    labels: regions,
                    datasets: datasets
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
                        x: {
                            stacked: true,
                            title: {
                                display: true,
                                text: '지역'
                            }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '시설 수'
                            }
                        }
                    }
                }
            });
        } else {
            regionInspectionCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">지역별 안전점검 데이터가 없습니다.</p>';
        }
    }

    // 4. 종목별 안전점검 통계
    const sportInspectionCtx = document.getElementById('sportInspectionChart');
    if (sportInspectionCtx) {
        const stats = sportInspectionStats || {};
        const sports = Object.keys(stats);
        
        if (sports.length > 0) {
            // 등급별로 데이터 정리
            const allGrades = new Set();
            sports.forEach(sport => {
                Object.keys(stats[sport]).forEach(grade => allGrades.add(grade));
            });
            const gradeList = Array.from(allGrades);
            
            const datasets = gradeList.map((grade, index) => {
                const gradeColors = {
                    '양호': 'rgba(46, 204, 113, 0.7)',
                    '주의': 'rgba(241, 196, 15, 0.7)',
                    '경고': 'rgba(231, 76, 60, 0.7)'
                };
                
                return {
                    label: grade,
                    data: sports.map(sport => stats[sport][grade] || 0),
                    backgroundColor: gradeColors[grade] || `rgba(${100 + index * 50}, ${150 + index * 30}, ${200 + index * 20}, 0.7)`
                };
            });
            
            new Chart(sportInspectionCtx, {
                type: 'bar',
                data: {
                    labels: sports,
                    datasets: datasets
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
                        x: {
                            stacked: true,
                            title: {
                                display: true,
                                text: '종목'
                            }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '시설 수'
                            }
                        }
                    }
                }
            });
        } else {
            sportInspectionCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">종목별 안전점검 데이터가 없습니다.</p>';
        }
    }
});

