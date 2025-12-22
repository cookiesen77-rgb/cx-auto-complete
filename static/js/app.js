/**
 * 超星学习通 Web 界面 - 前端交互逻辑
 */

// ============ 全局状态 ============
const AppState = {
    socket: null,
    isConnected: false,
    isLoggedIn: false,
    courses: [],
    selectedCourses: new Set(),
    isTaskRunning: false,
    settings: {
        speed: 1.5,
        autoSubmit: false
    }
};

// ============ DOM 元素引用 ============
const DOM = {
    // 连接状态
    connectionStatus: document.getElementById('connectionStatus'),
    
    // 登录相关
    loginSection: document.getElementById('loginSection'),
    loginForm: document.getElementById('loginForm'),
    loginBtn: document.getElementById('loginBtn'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    
    // 用户信息
    userSection: document.getElementById('userSection'),
    userName: document.getElementById('userName'),
    refreshCoursesBtn: document.getElementById('refreshCoursesBtn'),
    
    // 设置
    settingsSection: document.getElementById('settingsSection'),
    autoSubmit: document.getElementById('autoSubmit'),
    
    // 任务控制
    actionSection: document.getElementById('actionSection'),
    startTaskBtn: document.getElementById('startTaskBtn'),
    stopTaskBtn: document.getElementById('stopTaskBtn'),
    
    // 课程列表
    coursesContainer: document.getElementById('coursesContainer'),
    emptyState: document.getElementById('emptyState'),
    loadingState: document.getElementById('loadingState'),
    coursesList: document.getElementById('coursesList'),
    selectAllBtn: document.getElementById('selectAllBtn'),
    deselectAllBtn: document.getElementById('deselectAllBtn'),
    selectedCount: document.getElementById('selectedCount'),
    
    // 进度
    progressSection: document.getElementById('progressSection'),
    progressBar: document.getElementById('progressBar'),
    progressPercent: document.getElementById('progressPercent'),
    currentCourse: document.getElementById('currentCourse'),
    courseCount: document.getElementById('courseCount'),
    
    // 日志
    logContainer: document.getElementById('logContainer'),
    clearLogBtn: document.getElementById('clearLogBtn'),
    
    // Toast
    toastContainer: document.getElementById('toastContainer')
};

// ============ 工具函数 ============

/**
 * 显示 Toast 通知
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        warning: '⚠️',
        error: '❌',
        info: '💡'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
    `;
    
    DOM.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 添加日志
 */
function addLog(level, message, time = null) {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;
    
    const timeStr = time || new Date().toLocaleTimeString('zh-CN', { hour12: false });
    
    entry.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-message">${message}</span>
    `;
    
    DOM.logContainer.appendChild(entry);
    DOM.logContainer.scrollTop = DOM.logContainer.scrollHeight;
}

/**
 * 更新连接状态
 */
function updateConnectionStatus(connected, text = null) {
    const dot = DOM.connectionStatus.querySelector('.status-dot');
    const textEl = DOM.connectionStatus.querySelector('.status-text');
    
    dot.classList.remove('connected', 'error');
    
    if (connected) {
        dot.classList.add('connected');
        textEl.textContent = text || '已连接';
    } else if (connected === false) {
        dot.classList.add('error');
        textEl.textContent = text || '连接断开';
    } else {
        textEl.textContent = text || '连接中...';
    }
}

/**
 * 更新选中计数
 */
function updateSelectedCount() {
    DOM.selectedCount.textContent = `已选: ${AppState.selectedCourses.size}`;
    DOM.startTaskBtn.disabled = AppState.selectedCourses.size === 0;
}

/**
 * 切换按钮加载状态
 */
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ============ WebSocket 连接 ============

function initSocket() {
    const socket = io({
        transports: ['websocket', 'polling'],
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });
    
    socket.on('connect', () => {
        AppState.isConnected = true;
        updateConnectionStatus(true);
        addLog('success', 'WebSocket 连接成功');
    });
    
    socket.on('disconnect', () => {
        AppState.isConnected = false;
        updateConnectionStatus(false);
        addLog('warning', 'WebSocket 连接断开，正在尝试重连...');
    });
    
    socket.on('connect_error', (error) => {
        updateConnectionStatus(false, '连接错误');
        addLog('error', `连接错误: ${error.message}`);
    });
    
    // 接收日志
    socket.on('log', (data) => {
        addLog(data.level, data.message, data.time);
    });
    
    // 接收进度
    socket.on('progress', (data) => {
        updateProgress(data);
    });
    
    // 接收状态更新
    socket.on('status', (data) => {
        handleStatusUpdate(data);
    });
    
    AppState.socket = socket;
}

// ============ 状态处理 ============

function handleStatusUpdate(data) {
    switch (data.status) {
        case 'logged_in':
            AppState.isLoggedIn = true;
            showLoggedInUI(data.data.username);
            break;
            
        case 'task_started':
            AppState.isTaskRunning = true;
            showTaskRunningUI(data.data.total);
            break;
            
        case 'task_completed':
            AppState.isTaskRunning = false;
            showTaskCompletedUI();
            break;
            
        case 'task_error':
            AppState.isTaskRunning = false;
            showTaskErrorUI(data.data.error);
            break;
    }
}

function showLoggedInUI(username) {
    // 隐藏登录，显示用户信息
    DOM.loginSection.classList.add('hidden');
    DOM.userSection.classList.remove('hidden');
    DOM.settingsSection.classList.remove('hidden');
    DOM.actionSection.classList.remove('hidden');
    
    // 显示用户名 (隐藏部分)
    const maskedUsername = username.substring(0, 3) + '****' + username.substring(7);
    DOM.userName.textContent = maskedUsername;
    
    // 自动获取课程
    fetchCourses();
}

function showTaskRunningUI(total) {
    DOM.startTaskBtn.classList.add('hidden');
    DOM.stopTaskBtn.classList.remove('hidden');
    DOM.progressSection.classList.remove('hidden');
    
    // 禁用课程选择
    document.querySelectorAll('.course-item').forEach(item => {
        item.style.pointerEvents = 'none';
        item.style.opacity = '0.6';
    });
    
    DOM.selectAllBtn.disabled = true;
    DOM.deselectAllBtn.disabled = true;
    
    showToast('任务已开始', 'success');
}

function showTaskCompletedUI() {
    DOM.startTaskBtn.classList.remove('hidden');
    DOM.stopTaskBtn.classList.add('hidden');
    
    // 恢复课程选择
    document.querySelectorAll('.course-item').forEach(item => {
        item.style.pointerEvents = '';
        item.style.opacity = '';
    });
    
    DOM.selectAllBtn.disabled = false;
    DOM.deselectAllBtn.disabled = false;
    
    showToast('🎉 所有任务已完成！', 'success');
}

function showTaskErrorUI(error) {
    DOM.startTaskBtn.classList.remove('hidden');
    DOM.stopTaskBtn.classList.add('hidden');
    
    // 恢复课程选择
    document.querySelectorAll('.course-item').forEach(item => {
        item.style.pointerEvents = '';
        item.style.opacity = '';
    });
    
    DOM.selectAllBtn.disabled = false;
    DOM.deselectAllBtn.disabled = false;
    
    showToast(`任务出错: ${error}`, 'error');
}

function updateProgress(data) {
    const percent = data.percent || 0;
    
    DOM.progressBar.style.width = `${percent}%`;
    DOM.progressPercent.textContent = `${percent}%`;
    DOM.currentCourse.textContent = data.course || '处理中...';
    DOM.courseCount.textContent = `${data.current || 0}/${data.total || 0}`;
}

// ============ API 调用 ============

async function login(username, password) {
    try {
        setButtonLoading(DOM.loginBtn, true);
        
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('登录成功！', 'success');
        } else {
            showToast(result.message || '登录失败', 'error');
        }
        
        return result;
        
    } catch (error) {
        showToast('网络错误，请重试', 'error');
        return { success: false, message: error.message };
    } finally {
        setButtonLoading(DOM.loginBtn, false);
    }
}

async function fetchCourses() {
    try {
        // 显示加载状态
        DOM.emptyState.classList.add('hidden');
        DOM.coursesList.classList.add('hidden');
        DOM.loadingState.classList.remove('hidden');
        
        const response = await fetch('/api/courses');
        const result = await response.json();
        
        if (result.success) {
            AppState.courses = result.courses;
            renderCourses(result.courses);
            showToast(`已加载 ${result.courses.length} 门课程`, 'success');
        } else {
            showToast(result.message || '获取课程失败', 'error');
            DOM.loadingState.classList.add('hidden');
            DOM.emptyState.classList.remove('hidden');
        }
        
    } catch (error) {
        showToast('网络错误，请重试', 'error');
        DOM.loadingState.classList.add('hidden');
        DOM.emptyState.classList.remove('hidden');
    }
}

async function startTask() {
    const courseIds = Array.from(AppState.selectedCourses);
    
    if (courseIds.length === 0) {
        showToast('请至少选择一门课程', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/task/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_ids: courseIds,
                auto_submit: AppState.settings.autoSubmit,
                speed: AppState.settings.speed
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showToast(result.message || '启动任务失败', 'error');
        }
        
    } catch (error) {
        showToast('网络错误，请重试', 'error');
    }
}

async function stopTask() {
    try {
        const response = await fetch('/api/task/stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('正在停止任务...', 'warning');
        } else {
            showToast(result.message || '停止任务失败', 'error');
        }
        
    } catch (error) {
        showToast('网络错误，请重试', 'error');
    }
}

// ============ UI 渲染 ============

function renderCourses(courses) {
    DOM.loadingState.classList.add('hidden');
    DOM.coursesList.classList.remove('hidden');
    DOM.selectAllBtn.disabled = false;
    DOM.deselectAllBtn.disabled = false;
    
    DOM.coursesList.innerHTML = courses.map(course => `
        <div class="course-item" data-id="${course.courseId}">
            <div class="course-checkbox"></div>
            <div class="course-info">
                <div class="course-title">${course.title}</div>
                <div class="course-meta">
                    <span>👨‍🏫 ${course.teacher}</span>
                    <span class="course-id">ID: ${course.courseId}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    // 绑定点击事件
    document.querySelectorAll('.course-item').forEach(item => {
        item.addEventListener('click', () => toggleCourse(item));
    });
}

function toggleCourse(item) {
    const courseId = item.dataset.id;
    
    if (AppState.selectedCourses.has(courseId)) {
        AppState.selectedCourses.delete(courseId);
        item.classList.remove('selected');
    } else {
        AppState.selectedCourses.add(courseId);
        item.classList.add('selected');
    }
    
    updateSelectedCount();
}

function selectAllCourses() {
    document.querySelectorAll('.course-item').forEach(item => {
        AppState.selectedCourses.add(item.dataset.id);
        item.classList.add('selected');
    });
    updateSelectedCount();
}

function deselectAllCourses() {
    document.querySelectorAll('.course-item').forEach(item => {
        item.classList.remove('selected');
    });
    AppState.selectedCourses.clear();
    updateSelectedCount();
}

// ============ 事件绑定 ============

function initEventListeners() {
    // 登录表单
    DOM.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = DOM.username.value.trim();
        const password = DOM.password.value.trim();
        
        if (!username || !password) {
            showToast('请输入账号和密码', 'warning');
            return;
        }
        
        if (!/^\d{11}$/.test(username)) {
            showToast('请输入正确的11位手机号', 'warning');
            return;
        }
        
        await login(username, password);
    });
    
    // 刷新课程
    DOM.refreshCoursesBtn.addEventListener('click', fetchCourses);
    
    // 速度选择
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            AppState.settings.speed = parseFloat(btn.dataset.speed);
        });
    });
    
    // 自动提交开关
    DOM.autoSubmit.addEventListener('change', (e) => {
        AppState.settings.autoSubmit = e.target.checked;
    });
    
    // 全选/取消全选
    DOM.selectAllBtn.addEventListener('click', selectAllCourses);
    DOM.deselectAllBtn.addEventListener('click', deselectAllCourses);
    
    // 开始/停止任务
    DOM.startTaskBtn.addEventListener('click', startTask);
    DOM.stopTaskBtn.addEventListener('click', stopTask);
    
    // 清空日志
    DOM.clearLogBtn.addEventListener('click', () => {
        DOM.logContainer.innerHTML = '';
        addLog('info', '日志已清空');
    });
}

// ============ AI 配置功能 ============

const AiConfigDOM = {
    modal: document.getElementById('aiConfigModal'),
    openBtn: document.getElementById('openAiConfigBtn'),
    closeBtn: document.getElementById('closeAiConfigBtn'),
    cancelBtn: document.getElementById('cancelAiConfigBtn'),
    saveBtn: document.getElementById('saveAiConfigBtn'),
    testBtn: document.getElementById('testAiConfigBtn'),
    form: document.getElementById('aiConfigForm'),
    provider: document.getElementById('aiProvider'),
    endpoint: document.getElementById('aiEndpoint'),
    key: document.getElementById('aiKey'),
    model: document.getElementById('aiModel'),
    interval: document.getElementById('aiInterval'),
    coverRate: document.getElementById('aiCoverRate'),
    submit: document.getElementById('aiSubmit')
};

/**
 * 打开 AI 配置弹窗
 */
async function openAiConfigModal() {
    AiConfigDOM.modal.classList.remove('hidden');
    await loadAiConfig();
}

/**
 * 关闭 AI 配置弹窗
 */
function closeAiConfigModal() {
    AiConfigDOM.modal.classList.add('hidden');
}

/**
 * 加载 AI 配置
 */
async function loadAiConfig() {
    try {
        const response = await fetch('/api/config/ai');
        const result = await response.json();
        
        if (result.success) {
            const config = result.config;
            AiConfigDOM.provider.value = config.provider || 'AI';
            AiConfigDOM.endpoint.value = config.endpoint || '';
            AiConfigDOM.key.value = config.key || '';
            AiConfigDOM.model.value = config.model || '';
            AiConfigDOM.interval.value = config.min_interval_seconds || '3';
            AiConfigDOM.coverRate.value = config.cover_rate || '0.9';
            AiConfigDOM.submit.checked = config.submit === 'true';
        } else {
            showToast('加载配置失败: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('加载配置失败', 'error');
    }
}

/**
 * 测试 AI API 连接
 */
async function testAiConfig() {
    const config = {
        endpoint: AiConfigDOM.endpoint.value.trim(),
        key: AiConfigDOM.key.value.trim(),
        model: AiConfigDOM.model.value.trim()
    };
    
    if (!config.endpoint || !config.key || !config.model) {
        showToast('请填写 Endpoint、Key 和模型名称', 'warning');
        return;
    }
    
    try {
        setButtonLoading(AiConfigDOM.testBtn, true);
        addLog('info', '正在测试 API 连接...');
        
        const response = await fetch('/api/config/ai/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
            addLog('success', result.message);
        } else {
            showToast(result.message, 'error');
            addLog('error', result.message);
        }
    } catch (error) {
        showToast('测试请求失败', 'error');
        addLog('error', '测试请求失败: ' + error.message);
    } finally {
        setButtonLoading(AiConfigDOM.testBtn, false);
    }
}

/**
 * 保存 AI 配置
 */
async function saveAiConfig() {
    const config = {
        provider: AiConfigDOM.provider.value,
        endpoint: AiConfigDOM.endpoint.value.trim(),
        key: AiConfigDOM.key.value.trim(),
        model: AiConfigDOM.model.value.trim(),
        min_interval_seconds: AiConfigDOM.interval.value,
        cover_rate: AiConfigDOM.coverRate.value,
        submit: AiConfigDOM.submit.checked
    };
    
    try {
        setButtonLoading(AiConfigDOM.saveBtn, true);
        
        const response = await fetch('/api/config/ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('配置已保存', 'success');
            closeAiConfigModal();
            addLog('success', 'AI 配置已更新');
        } else {
            showToast('保存失败: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('保存配置失败', 'error');
    } finally {
        setButtonLoading(AiConfigDOM.saveBtn, false);
    }
}

/**
 * Provider 默认配置
 */
const ProviderDefaults = {
    'AI': {
        endpoint: '',
        model: '',
        hint: '填写任意 OpenAI 兼容的 API'
    },
    'SiliconFlow': {
        endpoint: 'https://api.siliconflow.cn/v1/chat/completions',
        model: 'deepseek-ai/DeepSeek-V3',
        hint: '硅基流动 API，获取 Key: https://cloud.siliconflow.cn'
    },
    'TikuYanxi': {
        endpoint: '',
        model: '',
        hint: '言溪题库，需要配置 tokens'
    },
    'TikuLike': {
        endpoint: '',
        model: '',
        hint: 'LIKE 知识库'
    },
    'TikuAdapter': {
        endpoint: '',
        model: '',
        hint: 'TikuAdapter 开源项目'
    }
};

/**
 * 切换 Provider 时更新默认值
 */
function onProviderChange() {
    const provider = AiConfigDOM.provider.value;
    const defaults = ProviderDefaults[provider] || ProviderDefaults['AI'];
    
    // 如果当前值为空或是其他 provider 的默认值，则更新
    const currentEndpoint = AiConfigDOM.endpoint.value.trim();
    const isDefaultEndpoint = Object.values(ProviderDefaults).some(p => p.endpoint === currentEndpoint);
    
    if (!currentEndpoint || isDefaultEndpoint) {
        AiConfigDOM.endpoint.value = defaults.endpoint;
    }
    
    const currentModel = AiConfigDOM.model.value.trim();
    const isDefaultModel = Object.values(ProviderDefaults).some(p => p.model === currentModel);
    
    if (!currentModel || isDefaultModel) {
        AiConfigDOM.model.value = defaults.model;
    }
}

/**
 * 初始化 AI 配置事件
 */
function initAiConfigEvents() {
    AiConfigDOM.openBtn.addEventListener('click', openAiConfigModal);
    AiConfigDOM.closeBtn.addEventListener('click', closeAiConfigModal);
    AiConfigDOM.cancelBtn.addEventListener('click', closeAiConfigModal);
    AiConfigDOM.saveBtn.addEventListener('click', saveAiConfig);
    AiConfigDOM.testBtn.addEventListener('click', testAiConfig);
    AiConfigDOM.provider.addEventListener('change', onProviderChange);
    
    // 点击遮罩关闭
    AiConfigDOM.modal.addEventListener('click', (e) => {
        if (e.target === AiConfigDOM.modal) {
            closeAiConfigModal();
        }
    });
    
    // ESC 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !AiConfigDOM.modal.classList.contains('hidden')) {
            closeAiConfigModal();
        }
    });
}

// ============ 初始化 ============

document.addEventListener('DOMContentLoaded', () => {
    addLog('info', '界面加载完成，正在连接服务器...');
    initSocket();
    initEventListeners();
    initAiConfigEvents();
});
