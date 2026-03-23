// 로그인 오버레이 DOM 요소 반환
const loginOverlay = () => document.getElementById("login-overlay");

// 로그인 에러 메시지 DOM 요소 반환
const loginErrorEl = () => document.getElementById("login-error");

// 로그인 완료 여부
let isAuthenticated = false;

// 대시보드 각 영역별 자동 갱신 주기 (초 단위)
const REFRESH_INTERVALS = {
    summary: 20,
    processes: 60,
    services: 30,
    logs: 15,
};


// setInterval 핸들 저장 (갱신 제어용)
let refreshTimers = {
    summary: null,
    processes: null,
    services: null,
    logs: null,
};


// 로그인 오버레이를 화면에 표시
const showLoginOverlay = () => {
    const el = loginOverlay();
    if (el) el.style.display = "flex";
};


// 로그인 오버레이를 숨김
const hideLoginOverlay = () => {
    const el = loginOverlay();
    if (el) el.style.display = "none";
};


// 로그인 에러 메시지를 화면에 출력
const setLoginError = (message = "") => {
    const el = loginErrorEl();
    if (el) el.textContent = message;
};


// 사용자 입력값으로 로그인 API 호출 후 세션 생성 시도
// 성공 시 true, 실패 시 false 반환
const tryLogin = async () => {
    const usernameEl = document.getElementById("login-username");
    const passwordEl = document.getElementById("login-password");

    const username = usernameEl?.value?.trim() ?? "";
    const password = passwordEl?.value ?? "";

    // 입력값 검증
    if (!username || !password) {
        setLoginError("아이디와 비밀번호를 입력하세요.");
        return false;
    }

    // 로그인 요청
    const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username,
            password,
        }),
    });

    // 로그인 실패 처리
    if (!response.ok) {
        isAuthenticated = false;
        setLoginError("로그인 실패");
        if (passwordEl) passwordEl.value = "";
        return false;
    }

    // 로그인 성공 처리
    if (passwordEl) passwordEl.value = "";
    setLoginError("");
    isAuthenticated = true;
    hideLoginOverlay();
    return true;
};

// 로그인 전에는 보호 API 호출을 막는다.
const ensureAuthenticated = () => {
    if (!isAuthenticated) {
        throw new Error("auth not ready");
    }
};

// 에러 메시지에 401이 포함되어 있는지 확인한다
const isUnauthorizedError = (error) =>
    String(error?.message ?? "").includes("401");

// 로그인 버튼 클릭 및 Enter 키 입력 이벤트 바인딩
// 로그인 성공 시 대시보드 로딩 및 자동 갱신 시작
const bindLoginEvents = () => {
    const loginBtn = document.getElementById("login-btn");
    const passwordEl = document.getElementById("login-password");

    // 로그인 버튼 클릭
    if (loginBtn) {
        loginBtn.addEventListener("click", async () => {
            const ok = await tryLogin();
            if (ok) {
                await refreshDashboard();
                startAutoRefresh();
            }
        });
    }

    // 비밀번호 입력창에서 Enter 입력 시 로그인 시도
    if (passwordEl) {
        passwordEl.addEventListener("keydown", async (event) => {
            if (event.key === "Enter") {
                const ok = await tryLogin();
                if (ok) {
                    await refreshDashboard();
                    startAutoRefresh();
                }
            }
        });
    }
};

// HTML 특수문자를 이스케이프해서 XSS를 방지한다.
const escapeHtml = (value) =>
    String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

// 사용률 숫자에 따라 상태 클래스명을 반환한다.
const getUsageClass = (value) => {
    const num = Number(value);

    if (Number.isNaN(num)) return "";
    if (num >= 90) return "bad";
    if (num >= 70) return "warn";
    return "good";
};

// 서비스 상태 문자열을 점(dot) 클래스명으로 변환한다.
const getServiceDotClass = (status) => {
    const lower = String(status ?? "").toLowerCase();

    if (lower.includes("zombie") || lower.includes("idle")) return "warn";
    if (lower.startsWith("active")) return "on";
    return "off";
};

// 프로세스 상태 코드를 점(dot) 클래스명으로 변환한다.
const getProcessDotClass = (statusCode) => {
    if (statusCode === "OK") return "on";
    if (statusCode === "WARN") return "warn";
    if (statusCode === "DANGER") return "off";
    return "";
};

// 현재 시각을 YYYY-MM-DD HH:mm:ss 형식 문자열로 반환한다.
const formatNow = () => {
    const now = new Date();

    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
};

// 자동 새로고침 상태 문구를 화면에 반영한다.
const setRefreshStatus = (text) => {
    const el = document.getElementById("refresh-status");
    if (!el) return;

    el.textContent = text;
};

// 마지막 갱신 시각 텍스트를 화면에 반영한다.
const updateSectionUpdatedAt = (id, text = null) => {
    const el = document.getElementById(id);
    if (!el) return;

    const value = text ?? formatNow();
    el.textContent = `[updated at] ${value}`;
};

// summary API를 호출해서 시스템 요약 영역을 갱신한다.
const refreshSummary = async () => {
    ensureAuthenticated();

    const response = await fetch("/api/dashboard/summary", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`summary fetch failed: ${response.status}`);
    }

    const data = await response.json();
    renderSystem(data);
    updateSectionUpdatedAt("summary-updated-at", data.updated_at);
};

// processes API를 호출해서 프로세스 목록 영역을 갱신한다.
const refreshProcesses = async () => {
    ensureAuthenticated();

    const response = await fetch("/api/dashboard/processes", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`processes fetch failed: ${response.status}`);
    }

    const data = await response.json();
    renderProcesses(data.processes);
    updateSectionUpdatedAt("processes-updated-at", data.updated_at);
};

// services API를 호출해서 서비스 상태 영역을 갱신한다.
const refreshServices = async () => {
    ensureAuthenticated();

    const response = await fetch("/api/dashboard/services", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`services fetch failed: ${response.status}`);
    }

    const data = await response.json();
    renderServices(data.services);
    updateSectionUpdatedAt("services-updated-at", data.updated_at);
};

// logs API를 호출해서 로그 영역을 갱신한다.
const refreshLogs = async () => {
    ensureAuthenticated();

    const response = await fetch("/api/dashboard/logs", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`logs fetch failed: ${response.status}`);
    }

    const data = await response.json();
    renderLogs(data.log_source, data.logs);
    updateSectionUpdatedAt("logs-updated-at", data.updated_at);
};

// 로그 콘솔을 항상 최하단으로 스크롤한다.
const scrollLogToBottom = () => {
    const logConsole = document.getElementById("log-console");
    if (!logConsole) return;

    logConsole.scrollTop = logConsole.scrollHeight;
};

// CPU, 메모리, 디스크, 업타임 영역을 렌더링한다.
const renderSystem = (data) => {
    const cpuEl = document.getElementById("cpu");
    const memoryEl = document.getElementById("memory");
    const diskEl = document.getElementById("disk");
    const uptimeEl = document.getElementById("uptime");

    if (cpuEl) {
        cpuEl.textContent = `${data.cpu}%`;
        cpuEl.className = getUsageClass(data.cpu);
    }

    if (memoryEl) {
        memoryEl.textContent = `${data.memory}%`;
        memoryEl.className = getUsageClass(data.memory);
    }

    if (diskEl) {
        diskEl.textContent = `${data.disk}%`;
        diskEl.className = getUsageClass(data.disk);
    }

    if (uptimeEl) {
        uptimeEl.textContent = data.uptime ?? "-";
    }
};

// 서비스 목록 영역을 렌더링한다.
const renderServices = (services) => {
    const container = document.getElementById("service-list");
    if (!container) return;

    const entries = Object.entries(services ?? {});
    container.innerHTML = entries
        .map(
            ([name, status]) => `
                <div class="service-item">
                    <div class="service-name-group">
                        <span class="dot ${getServiceDotClass(status)}"></span>
                        <span class="service-name">${escapeHtml(name)}</span>
                    </div>
                    <span class="service-status">[ ${escapeHtml(String(status).toUpperCase())} ]</span>
                </div>
            `
        )
        .join("");
};

// 로그 소스와 로그 콘솔 내용을 렌더링한다.
const renderLogs = (logSource, logs) => {
    const sourceEl = document.getElementById("log-source");
    const consoleEl = document.getElementById("log-console");

    if (sourceEl) {
        sourceEl.textContent = `SOURCE : ${logSource ?? "-"}`;
    }

    if (consoleEl) {
        consoleEl.innerHTML = (logs ?? [])
            .map(
                (line) => `
                    <div class="log-line">${escapeHtml(line)}</div>
                `
            )
            .join("");

        scrollLogToBottom();
    }
};

// 프로세스 목록 영역을 렌더링한다.
const renderProcesses = (processes) => {
    const container = document.getElementById("process-list");
    if (!container) return;

    container.innerHTML = (processes ?? [])
        .map((p) => {
            const dotClass = getProcessDotClass(p.status_code);

            const warningsHtml = Array.isArray(p.warnings) && p.warnings.length > 0
                ? `
                    <p class="bad warning-text">
                        ${p.warnings.map((warning) => `⚠ ${escapeHtml(warning)}`).join("<br>")}
                    </p>
                `
                : "";

            const portsHtml = p.display_ports
                ? `
                    <p class="process-p">
                        PORT : ${escapeHtml(p.display_ports)}
                    </p>
                `
                : "";

            const actionHtml = !p.is_system
                ? `
                    <button class="kill-btn"
                            data-pid="${escapeHtml(p.pid)}"
                            data-name="${escapeHtml(p.name)}"
                            onclick="terminateProcess(this)">
                        TERMINATE
                    </button>
                `
                : `
                    <span style="font-size:10px; color:#666;">
                        SYSTEM PROTECTED
                    </span>
                `;

            return `
                <div class="process-item">
                    <p class="process-status">
                        <span class="dot ${dotClass}"></span>
                        ${escapeHtml(p.name)} (PID ${escapeHtml(p.pid)})
                    </p>

                    <p class="process-explain">
                        ${escapeHtml(p.explain)}
                        ${actionHtml}
                    </p>

                    <p class="process-p">
                        CPU : ${escapeHtml(p.cpu)}% |
                        MEM : ${escapeHtml(p.memory)}% |
                        USER : ${escapeHtml(p.user)}
                    </p>

                    ${portsHtml}

                    <span style="font-size: 10px; margin-left: 5px;">
                        ${escapeHtml(p.status_summary)}
                    </span>

                    ${warningsHtml}

                    <hr style="border:1px dashed #00ff9c; margin:10px 0;">
                </div>
            `;
        })
        .join("");
};

// 대시보드 전체 각 영역을 개별 API 기준으로 초기 갱신한다.
const refreshDashboard = async () => {
    try {
        setRefreshStatus("RELOADING...");

        await Promise.all([
            refreshSummary(),
            refreshProcesses(),
            refreshServices(),
            refreshLogs(),
        ]);

        setRefreshStatus(
            `summary:${REFRESH_INTERVALS.summary}s | processes:${REFRESH_INTERVALS.processes}s | services:${REFRESH_INTERVALS.services}s | logs:${REFRESH_INTERVALS.logs}s`
        );
    } catch (error) {
        console.error(error);
        if (String(error?.message ?? "") === "auth not ready") {
            setRefreshStatus("AUTH REQUIRED");
            return;
        }
        setRefreshStatus("AUTH REQUIRED");

        if (isUnauthorizedError(error)) {
            isAuthenticated = false;
            showLoginOverlay();
            Object.values(refreshTimers).forEach((timer) => {
                if (timer) clearInterval(timer);
            });
        }
    }
};

// 자동 갱신 타이머를 영역별로 설정/재설정한다.
const startAutoRefresh = () => {
    if (!isAuthenticated) return;
    Object.values(refreshTimers).forEach((timer) => {
        if (timer) {
            clearInterval(timer);
        }
    });

    refreshTimers.summary = setInterval(async () => {
        try {
            await refreshSummary();
        } catch (error) {
            console.error(error);
        }
    }, REFRESH_INTERVALS.summary * 1000);

    refreshTimers.processes = setInterval(async () => {
        try {
            await refreshProcesses();
        } catch (error) {
            console.error(error);
        }
    }, REFRESH_INTERVALS.processes * 1000);

    refreshTimers.services = setInterval(async () => {
        try {
            await refreshServices();
        } catch (error) {
            console.error(error);
        }
    }, REFRESH_INTERVALS.services * 1000);

    refreshTimers.logs = setInterval(async () => {
        try {
            await refreshLogs();
        } catch (error) {
            console.error(error);
        }
    }, REFRESH_INTERVALS.logs * 1000);

    setRefreshStatus(
        `summary:${REFRESH_INTERVALS.summary}s | processes:${REFRESH_INTERVALS.processes}s | services:${REFRESH_INTERVALS.services}s | logs:${REFRESH_INTERVALS.logs}s`
    );
};

// 공용 커스텀 모달을 띄우고 사용자 선택 결과를 Promise로 반환한다.
const showModal = (title, message, showCancel = false, type = "error") =>
    new Promise((resolve) => {
        const modal = document.getElementById("custom-modal");
        const card = modal.querySelector(".modal-card");
        const titleEl = document.getElementById("modal-title");
        const messageEl = document.getElementById("modal-message");
        const okBtn = document.getElementById("modal-ok-btn");
        const cancelBtn = document.getElementById("modal-cancel-btn");

        const colors = {
            error: "#ff5555",
            success: "#00ff9c",
            info: "#ffd866",
        };

        const themeColor = colors[type] ?? colors.error;

        card.style.borderColor = themeColor;
        titleEl.style.color = themeColor;
        okBtn.style.borderColor = themeColor;
        okBtn.style.color = themeColor;

        okBtn.onmouseover = () => {
            okBtn.style.backgroundColor = themeColor;
            okBtn.style.color = "#000";
        };

        okBtn.onmouseout = () => {
            okBtn.style.backgroundColor = "transparent";
            okBtn.style.color = themeColor;
        };

        titleEl.innerText = title;
        messageEl.innerHTML = message;
        modal.style.display = "flex";

        cancelBtn.style.display = showCancel ? "inline-block" : "none";

        okBtn.onclick = () => {
            modal.style.display = "none";
            resolve(true);
        };

        cancelBtn.onclick = () => {
            modal.style.display = "none";
            resolve(false);
        };
    });

// 선택한 프로세스 종료 API를 호출하고 성공 시 대시보드를 다시 갱신한다.
const terminateProcess = async (button) => {
    const { pid, name } = button.dataset;

    const confirmed = await showModal(
        "WARNING: TERMINATE",
        `[${escapeHtml(name)}] <br> 프로세스를 종료하시겠습니까?`,
        true,
        "error"
    );

    if (!confirmed) return;

    try {
        const response = await fetch("/api/process/terminate", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
             },
            body: JSON.stringify({ pid: Number(pid) }),
            credentials: "same-origin",
        });

        const data = await response.json();

        if (data.result === "terminated") {
            await showModal("SUCCESS", data.message, false, "success");
            await refreshDashboard();
        } else {
            await showModal("BLOCKED", data.message, false, "info");
        }
    } catch (error) {
        await showModal("CRITICAL ERROR", "통신 중 오류가 발생했습니다.", false, "error");
    }
};

// 인라인 onclick에서 호출할 수 있도록 terminateProcess를 전역에 노출한다.
window.terminateProcess = terminateProcess;

// 초기 1회 렌더
document.addEventListener("DOMContentLoaded", async () => {
    scrollLogToBottom();
    bindLoginEvents();
    showLoginOverlay();
});