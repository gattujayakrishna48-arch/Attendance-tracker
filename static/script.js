// ============================================================
// Attendance Tracker – Client-side JavaScript
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss flash alerts after 5 seconds
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity .4s ease";
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Radio button visual feedback (fallback for browsers without full :has())
    document.querySelectorAll(".radio-btn input").forEach((radio) => {
        radio.addEventListener("change", () => {
            const name = radio.getAttribute("name");
            document.querySelectorAll(`input[name="${name}"]`).forEach((r) => {
                r.closest(".radio-btn").classList.remove("selected");
            });
            if (radio.checked) {
                radio.closest(".radio-btn").classList.add("selected");
                const row = radio.closest(".period-row");
                if (row) {
                    row.classList.remove("marked-present", "marked-absent");
                    row.classList.add(radio.value === "present" ? "marked-present" : "marked-absent");
                }
            }
        });
        if (radio.checked) {
            radio.closest(".radio-btn").classList.add("selected");
        }
    });

    // Initialize Attendance Charts if data is present
    initAttendanceCharts();
});


// ============================================================
// Charts Initialization
// ============================================================

function initAttendanceCharts() {
    const dataEl = document.getElementById("chartDataJson");
    if (!dataEl || typeof Chart === "undefined") return;

    let chartData;
    try {
        chartData = JSON.parse(dataEl.textContent);
    } catch (e) {
        console.error("Failed to parse chart data:", e);
        return;
    }

    const { subjects, donut, trend } = chartData;

    // 1. Subject-wise Bar Chart
    const subCanvas = document.getElementById("subjectBarChart");
    if (subCanvas && subjects && subjects.length > 0) {
        const labels = subjects.map(s => s.short_name);
        const pcts = subjects.map(s => s.pct);
        const colors = subjects.map(s => s.color || "#4f46e5");

        new Chart(subCanvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Attendance %",
                        data: pcts,
                        backgroundColor: colors.map(c => c + "cc"),
                        borderColor: colors,
                        borderWidth: 2,
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            callback: val => val + "%",
                            stepSize: 25
                        },
                        grid: { color: "#f1f5f9" }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                const idx = items[0].dataIndex;
                                return `${subjects[idx].name} (${subjects[idx].short_name})`;
                            },
                            label: (item) => {
                                const idx = item.dataIndex;
                                const s = subjects[idx];
                                return [
                                    `Attendance: ${s.pct}%`,
                                    `Present: ${s.present} / Total: ${s.total}`,
                                    `Absent: ${s.absent}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Overall Donut Chart
    const donutCanvas = document.getElementById("overallDonutChart");
    if (donutCanvas && donut) {
        const hasData = donut.total > 0;
        const donutData = hasData ? [donut.present, donut.absent] : [1];
        const donutColors = hasData ? ["#16a34a", "#dc2626"] : ["#cbd5e1"];
        const donutLabels = hasData ? ["Present", "Absent"] : ["No Records Yet"];

        new Chart(donutCanvas, {
            type: "doughnut",
            data: {
                labels: donutLabels,
                datasets: [{
                    data: donutData,
                    backgroundColor: donutColors,
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 14, font: { weight: "600" } }
                    },
                    tooltip: {
                        enabled: hasData,
                        callbacks: {
                            label: (item) => ` ${item.label}: ${item.parsed} periods`
                        }
                    }
                }
            }
        });
    }

    // 3. Daily 7-Day Trend Chart
    const trendCanvas = document.getElementById("dailyTrendChart");
    if (trendCanvas && trend && trend.labels.length > 0) {
        new Chart(trendCanvas, {
            type: "bar",
            data: {
                labels: trend.labels,
                datasets: [
                    {
                        label: "Present",
                        data: trend.present,
                        backgroundColor: "#16a34a",
                        borderRadius: 4,
                    },
                    {
                        label: "Absent",
                        data: trend.absent,
                        backgroundColor: "#dc2626",
                        borderRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: { stepSize: 1, precision: 0 },
                        grid: { color: "#f1f5f9" }
                    }
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { boxWidth: 14, font: { weight: "600" } }
                    }
                }
            }
        });
    }

    // Toggle button handler
    const buttons = document.querySelectorAll(".chart-toggle-btn");
    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const mode = btn.getAttribute("data-chart");
            const boxSubjects = document.getElementById("box-subjects");
            const boxRatio = document.getElementById("box-ratio");
            const boxTrend = document.getElementById("box-trend");

            if (mode === "all") {
                if (boxSubjects) boxSubjects.style.display = "block";
                if (boxRatio) boxRatio.style.display = "block";
                if (boxTrend) boxTrend.style.display = "block";
            } else if (mode === "subjects") {
                if (boxSubjects) boxSubjects.style.display = "block";
                if (boxRatio) boxRatio.style.display = "none";
                if (boxTrend) boxTrend.style.display = "none";
            } else if (mode === "ratio") {
                if (boxSubjects) boxSubjects.style.display = "none";
                if (boxRatio) boxRatio.style.display = "block";
                if (boxTrend) boxTrend.style.display = "none";
            } else if (mode === "trend") {
                if (boxSubjects) boxSubjects.style.display = "none";
                if (boxRatio) boxRatio.style.display = "none";
                if (boxTrend) boxTrend.style.display = "block";
            }
        });
    });
}


// ============================================================
// Timetable Page – Dynamic Period Add / Remove
// ============================================================

function addPeriod(dayNum) {
    const container = document.getElementById(`day${dayNum}_periods`);
    if (!container) return;

    // Remove empty placeholder message if present
    const noMsg = container.querySelector(".no-periods-msg");
    if (noMsg) noMsg.remove();

    const existing = container.querySelectorAll(".tt-period-row");
    const periodNum = existing.length + 1;

    // Default time based on period number if available
    const defaultTimes = {
        1: ["09:30", "10:20"],
        2: ["10:20", "11:10"],
        3: ["11:10", "12:00"],
        4: ["12:00", "12:50"],
        5: ["13:50", "14:40"],
        6: ["14:40", "15:30"],
        7: ["15:30", "16:20"],
    };
    const [defStart, defEnd] = defaultTimes[periodNum] || ["09:30", "10:20"];

    const optionsTemplate = document.getElementById("subjectOptions");
    const optionsHTML = optionsTemplate ? optionsTemplate.innerHTML : '<option value="">— Subject —</option>';

    const row = document.createElement("div");
    row.className = "tt-period-row";
    row.innerHTML = `
        <span class="tt-period-label">P${periodNum}</span>
        <select name="day${dayNum}_period${periodNum}_subject" required>
            ${optionsHTML}
        </select>
        <input type="time" name="day${dayNum}_period${periodNum}_start" value="${defStart}" required title="Start Time">
        <span style="font-size: .8rem; color: #94a3b8;">to</span>
        <input type="time" name="day${dayNum}_period${periodNum}_end" value="${defEnd}" required title="End Time">
        <button type="button" class="btn-icon btn-remove" onclick="removePeriod(this)" title="Remove Period">✕</button>
    `;
    container.appendChild(row);
}

function removePeriod(btn) {
    const row = btn.closest(".tt-period-row");
    const container = row.parentElement;
    row.remove();

    const rows = container.querySelectorAll(".tt-period-row");
    if (rows.length === 0) {
        container.innerHTML = '<p class="text-muted no-periods-msg" style="font-size: .85rem; padding: .5rem 0;">No periods scheduled.</p>';
        return;
    }

    // Re-number remaining periods sequentially
    rows.forEach((r, i) => {
        const num = i + 1;
        r.querySelector(".tt-period-label").textContent = `P${num}`;
        const dayMatch = r.querySelector("select").name.match(/day(\d+)/);
        if (dayMatch) {
            const dayNum = dayMatch[1];
            r.querySelector("select").name = `day${dayNum}_period${num}_subject`;
            const inputs = r.querySelectorAll("input[type='time']");
            if (inputs.length >= 2) {
                inputs[0].name = `day${dayNum}_period${num}_start`;
                inputs[1].name = `day${dayNum}_period${num}_end`;
            }
        }
    });
}
