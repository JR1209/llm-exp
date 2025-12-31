// 全局变量
let uploadedFile = null;
let uploadedQuestions = [];
let experimentVersion = null;
let resultData = null;

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const jsonPreview = document.getElementById('jsonPreview');
const runBtn = document.getElementById('runBtn');
const downloadBtn = document.getElementById('downloadBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const statusMessage = document.getElementById('statusMessage');
const resultContainer = document.getElementById('resultContainer');
const alert = document.getElementById('alert');
const logViewer = document.getElementById('logViewer');
const logContent = document.getElementById('logContent');
const refreshLogBtn = document.getElementById('refreshLogBtn');

// 新增：模式和模型选择元素
const modeRadios = document.querySelectorAll('input[name="mode"]');
const singleModelSelection = document.getElementById('singleModelSelection');
const dualModelSelection = document.getElementById('dualModelSelection');
const singleModel = document.getElementById('singleModel');
const singleDialogueRounds = document.getElementById('singleDialogueRounds');
const singleCandidates = document.getElementById('singleCandidates');
const userModel = document.getElementById('userModel');
const agentModel = document.getElementById('agentModel');
const dialogueRounds = document.getElementById('dialogueRounds');
const dualCandidates = document.getElementById('dualCandidates');

// 新增：打分模式元素
const scoringModeRadios = document.querySelectorAll('input[name="scoringMode"]');
const scoringModel = document.getElementById('scoringModel');
const scoreRounds = document.getElementById('scoreRounds');
const topK = document.getElementById('topK');

// 新增：Prompt相关元素
const generationPromptText = document.getElementById('generationPromptText');
const uploadGenPromptBtn = document.getElementById('uploadGenPromptBtn');
const clearGenPromptBtn = document.getElementById('clearGenPromptBtn');
const scoringPromptText = document.getElementById('scoringPromptText');
const uploadScorePromptBtn = document.getElementById('uploadScorePromptBtn');
const clearScorePromptBtn = document.getElementById('clearScorePromptBtn');

// 新增：侧边栏按钮
const jsonDiffBtn = document.getElementById('jsonDiffBtn');

// 可用模型列表
let availableModels = {};

// Prompt输入模式和文件内容
let genPromptMode = 'text'; // 'text' 或 'file'
let scorePromptMode = 'text';
let genPromptFileContent = null;
let scorePromptFileContent = null;

// 日志更新定时器
let logUpdateInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAvailableModels();
    initPromptTabs();
    initGenPromptFileUpload();
    initScorePromptFileUpload();
});

// 设置事件监听
function setupEventListeners() {
    // 上传区域点击
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);
    
    // 拖拽事件
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // 运行按钮
    runBtn.addEventListener('click', runExperiment);
    
    // 下载按钮
    downloadBtn.addEventListener('click', downloadResults);
    
    // 刷新日志按钮
    refreshLogBtn.addEventListener('click', () => fetchLog(experimentVersion));
    
    // 新增：模式切换
    modeRadios.forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });
    
    // 新增：模式选项点击
    document.querySelectorAll('.mode-option').forEach(option => {
        option.addEventListener('click', function() {
            const mode = this.dataset.mode;
            if (mode) {
                const radio = document.querySelector(`input[name="mode"][value="${mode}"]`);
                if (radio) {
                    radio.checked = true;
                    handleModeChange();
                }
            }
            
            const scoringMode = this.dataset.scoringMode;
            if (scoringMode) {
                const radio = document.querySelector(`input[name="scoringMode"][value="${scoringMode}"]`);
                if (radio) {
                    radio.checked = true;
                    handleScoringModeChange();
                }
            }
        });
    });
    
    // 新增：打分模式切换
    scoringModeRadios.forEach(radio => {
        radio.addEventListener('change', handleScoringModeChange);
    });
    
    // 新增：Prompt上传按钮
    uploadGenPromptBtn.addEventListener('click', uploadGenerationPrompt);
    clearGenPromptBtn.addEventListener('click', () => {
        generationPromptText.value = '';
        genPromptFileContent = null;
        const fileInfo = document.getElementById('genPromptFileInfo');
        if (fileInfo) fileInfo.style.display = 'none';
        document.getElementById('genPromptFileInput').value = '';
        showAlert('生成Prompt已清除', 'success');
    });
    
    uploadScorePromptBtn.addEventListener('click', uploadScoringPrompt);
    clearScorePromptBtn.addEventListener('click', () => {
        scoringPromptText.value = '';
        scorePromptFileContent = null;
        const fileInfo = document.getElementById('scorePromptFileInfo');
        if (fileInfo) fileInfo.style.display = 'none';
        document.getElementById('scorePromptFileInput').value = '';
        showAlert('打分Prompt已清除', 'success');
    });
    
    // 新增：Json Diff按钮（预留）
    jsonDiffBtn.addEventListener('click', () => {
        showAlert('Json Diff功能开发中...', 'error');
    });
}

// 加载可用模型列表
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                availableModels = data.models;
                populateModelSelects();
                
                // 同时加载已保存的prompts
                await loadCurrentPrompts();
            }
        }
    } catch (error) {
        console.error('加载模型列表失败:', error);
        showAlert('加载模型列表失败', 'error');
    }
}

// 加载当前已保存的prompts
async function loadCurrentPrompts() {
    try {
        // 加载生成prompt
        const genResponse = await fetch('/api/prompts/generation');
        if (genResponse.ok) {
            const genData = await genResponse.json();
            if (genData.success && genData.custom) {
                generationPromptText.value = genData.prompt;
            }
        }
        
        // 加载打分prompt
        const scoreResponse = await fetch('/api/prompts/scoring');
        if (scoreResponse.ok) {
            const scoreData = await scoreResponse.json();
            if (scoreData.success && scoreData.custom) {
                scoringPromptText.value = scoreData.prompt;
            }
        }
    } catch (error) {
        console.error('加载prompts失败:', error);
    }
}

// 初始化Prompt选项卡切换
function initPromptTabs() {
    document.querySelectorAll('.prompt-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            const promptType = this.dataset.prompt; // 'gen' 或 'score'
            
            // 找到所属的容器
            const container = this.closest('.prompt-upload-area');
            
            // 切换active状态
            container.querySelectorAll('.prompt-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 切换面板显示
            container.querySelectorAll('.prompt-panel').forEach(panel => {
                if (panel.dataset.prompt === promptType) {
                    panel.style.display = panel.dataset.panel === tabName ? 'block' : 'none';
                }
            });
            
            // 更新模式
            if (promptType === 'gen') {
                genPromptMode = tabName;
            } else if (promptType === 'score') {
                scorePromptMode = tabName;
            }
        });
    });
}

// 初始化生成Prompt文件上传
function initGenPromptFileUpload() {
    const dropZone = document.getElementById('genPromptDropZone');
    const fileInput = document.getElementById('genPromptFileInput');
    const fileInfo = document.getElementById('genPromptFileInfo');
    const fileName = document.getElementById('genPromptFileName');
    
    if (!dropZone || !fileInput) return;
    
    // 点击区域触发文件选择
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
            fileInput.click();
        }
    });
    
    dropZone.querySelector('.btn-small').addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    
    // 拖拽事件
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleGenPromptFile(e.dataTransfer.files[0]);
        }
    });
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleGenPromptFile(e.target.files[0]);
        }
    });
    
    function handleGenPromptFile(file) {
        if (!file) return;
        
        const isJson = file.name.endsWith('.json');
        const isTxt = file.name.endsWith('.txt');
        
        if (!isJson && !isTxt) {
            showAlert('请上传JSON或TXT格式文件', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            genPromptFileContent = e.target.result;
            fileName.textContent = file.name;
            fileInfo.style.display = 'block';
            showAlert('文件已加载：' + file.name, 'success');
        };
        reader.readAsText(file);
    }
}

// 初始化打分Prompt文件上传
function initScorePromptFileUpload() {
    const dropZone = document.getElementById('scorePromptDropZone');
    const fileInput = document.getElementById('scorePromptFileInput');
    const fileInfo = document.getElementById('scorePromptFileInfo');
    const fileName = document.getElementById('scorePromptFileName');
    
    if (!dropZone || !fileInput) return;
    
    // 点击区域触发文件选择
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
            fileInput.click();
        }
    });
    
    dropZone.querySelector('.btn-small').addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    
    // 拖拽事件
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleScorePromptFile(e.dataTransfer.files[0]);
        }
    });
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleScorePromptFile(e.target.files[0]);
        }
    });
    
    function handleScorePromptFile(file) {
        if (!file) return;
        
        const isJson = file.name.endsWith('.json');
        const isTxt = file.name.endsWith('.txt');
        
        if (!isJson && !isTxt) {
            showAlert('请上传JSON或TXT格式文件', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            scorePromptFileContent = e.target.result;
            fileName.textContent = file.name;
            fileInfo.style.display = 'block';
            showAlert('文件已加载：' + file.name, 'success');
        };
        reader.readAsText(file);
    }
}

// 上传生成prompt（支持文本和文件两种方式）
async function uploadGenerationPrompt() {
    let promptContent = '';
    
    if (genPromptMode === 'text') {
        promptContent = generationPromptText.value.trim();
    } else if (genPromptMode === 'file') {
        promptContent = genPromptFileContent;
    }
    
    if (!promptContent) {
        showAlert('请输入或上传prompt内容', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/prompts/generation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptContent })
        });
        
        if (response.ok) {
            showAlert('生成Prompt已保存', 'success');
        } else {
            showAlert('保存失败', 'error');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'error');
    }
}

// 上传打分prompt（支持文本和文件两种方式）
async function uploadScoringPrompt() {
    let promptContent = '';
    
    if (scorePromptMode === 'text') {
        promptContent = scoringPromptText.value.trim();
    } else if (scorePromptMode === 'file') {
        promptContent = scorePromptFileContent;
    }
    
    if (!promptContent) {
        showAlert('请输入或上传prompt内容', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/prompts/scoring', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptContent })
        });
        
        if (response.ok) {
            showAlert('打分Prompt已保存', 'success');
        } else {
            showAlert('保存失败', 'error');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'error');
    }
}

// 填充模型选择下拉框
function populateModelSelects() {
    const modelOptions = Object.entries(availableModels)
        .map(([key, value]) => `<option value="${key}">${key} (${value})</option>`)
        .join('');
    
    singleModel.innerHTML = modelOptions;
    userModel.innerHTML = modelOptions;
    agentModel.innerHTML = modelOptions;
    scoringModel.innerHTML = modelOptions;
    
    // 设置默认值
    singleModel.value = 'qwen-max';
    userModel.value = 'qwen-max';
    agentModel.value = 'turing-gpt';
    scoringModel.value = 'turing-gpt';
}

// 处理生成模式切换
function handleModeChange() {
    const selectedMode = document.querySelector('input[name="mode"]:checked').value;
    
    // 更新UI显示
    document.querySelectorAll('.mode-option[data-mode]').forEach(option => {
        option.style.background = 'rgba(255, 255, 255, 0.03)';
        option.style.borderColor = 'var(--border)';
        option.style.boxShadow = 'none';
    });
    
    const selectedOption = document.querySelector(`.mode-option[data-mode="${selectedMode}"]`);
    if (selectedOption) {
        selectedOption.style.background = 'rgba(255, 107, 157, 0.15)';
        selectedOption.style.borderColor = 'var(--primary)';
        selectedOption.style.boxShadow = '0 4px 16px rgba(255, 107, 157, 0.3)';
    }
    
    if (selectedMode === 'single') {
        singleModelSelection.style.display = 'block';
        dualModelSelection.style.display = 'none';
    } else {
        singleModelSelection.style.display = 'none';
        dualModelSelection.style.display = 'block';
    }
}

// 处理打分模式切换
function handleScoringModeChange() {
    const selectedMode = document.querySelector('input[name="scoringMode"]:checked').value;
    
    // 更新UI显示
    document.querySelectorAll('.mode-option[data-scoring-mode]').forEach(option => {
        option.style.background = 'rgba(255, 255, 255, 0.03)';
        option.style.borderColor = 'var(--border)';
        option.style.boxShadow = 'none';
    });
    
    const selectedOption = document.querySelector(`.mode-option[data-scoring-mode="${selectedMode}"]`);
    if (selectedOption) {
        selectedOption.style.background = 'rgba(255, 107, 157, 0.15)';
        selectedOption.style.borderColor = 'var(--primary)';
        selectedOption.style.boxShadow = '0 4px 16px rgba(255, 107, 157, 0.3)';
    }
}

// 获取实验日志
async function fetchLog(version) {
    if (!version) return;
    
    try {
        const response = await fetch(`/api/experiments/${version}/log`);
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                logContent.textContent = data.log || '暂无日志';
                // 自动滚动到底部
                logContent.scrollTop = logContent.scrollHeight;
            }
        } else {
            logContent.textContent = '日志加载失败或文件不存在';
        }
    } catch (error) {
        console.error('获取日志失败:', error);
    }
}

// 开始定时更新日志
function startLogUpdates(version) {
    // 清除旧的定时器
    if (logUpdateInterval) {
        clearInterval(logUpdateInterval);
    }
    
    // 显示日志查看器
    logViewer.classList.add('show');
    refreshLogBtn.style.display = 'inline-block';
    
    // 立即获取一次
    fetchLog(version);
    
    // 每3秒更新一次
    logUpdateInterval = setInterval(() => {
        fetchLog(version);
    }, 3000);
}

// 停止日志更新
function stopLogUpdates() {
    if (logUpdateInterval) {
        clearInterval(logUpdateInterval);
        logUpdateInterval = null;
    }
}

// 处理文件选择
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    const isJson = file.name.endsWith('.json');
    const isTxt = file.name.endsWith('.txt');
    
    if (!isJson && !isTxt) {
        showAlert('请上传 JSON 或 TXT 格式的文件', 'error');
        return;
    }
    
    uploadedFile = file;
    fileName.textContent = file.name;
    
    // 读取文件
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const content = e.target.result;
            
            if (isJson) {
                // JSON 格式处理
                const jsonData = JSON.parse(content);
                
                // 支持多种 JSON 格式
                if (Array.isArray(jsonData)) {
                    // 格式1: ["问题1", "问题2", ...]
                    if (typeof jsonData[0] === 'string') {
                        uploadedQuestions = jsonData;
                    }
                    // 格式2: [{"question": "..."}, {"question": "..."}, ...]
                    else if (typeof jsonData[0] === 'object') {
                        uploadedQuestions = jsonData.map(item => 
                            item.question || item.text || item.content || JSON.stringify(item)
                        );
                    }
                } else if (jsonData.questions) {
                    // 格式3: {"questions": [...]}
                    uploadedQuestions = Array.isArray(jsonData.questions) 
                        ? jsonData.questions.map(q => typeof q === 'string' ? q : q.question || q.text)
                        : [];
                } else {
                    uploadedQuestions = [JSON.stringify(jsonData)];
                }
                
                // 显示 JSON 预览
                jsonPreview.textContent = JSON.stringify(jsonData, null, 2).substring(0, 500) + '...';
                
            } else {
                // TXT 格式处理 - 每行一个问题
                uploadedQuestions = content
                    .split('\n')
                    .map(line => line.trim())
                    .filter(line => line.length > 0);
                
                // 显示 TXT 预览
                jsonPreview.textContent = content.substring(0, 500) + (content.length > 500 ? '...' : '');
            }
            
            fileInfo.classList.add('show');
            runBtn.disabled = false;
            
            showAlert(`成功加载 ${uploadedQuestions.length} 个问题 (${isJson ? 'JSON' : 'TXT'} 格式)`, 'success');
            
        } catch (error) {
            showAlert('文件解析错误：' + error.message, 'error');
            runBtn.disabled = true;
        }
    };
    reader.readAsText(file);
}

// 运行实验
async function runExperiment() {
    if (uploadedQuestions.length === 0) {
        showAlert('请先上传问题集', 'error');
        return;
    }
    
    // 禁用按钮
    runBtn.disabled = true;
    downloadBtn.disabled = true;
    
    // 显示进度
    progressContainer.classList.add('show');
    resultContainer.classList.remove('show');
    
    try {
        // 第一步：上传问题到服务器
        updateProgress(10, '正在上传问题集...');
        await uploadQuestions();
        
        // 第二步：启动实验
        updateProgress(20, '正在启动实验...');
        experimentVersion = 'v' + Date.now();
        
        // 获取选择的模式和模型
        const selectedMode = document.querySelector('input[name="mode"]:checked').value;
        const selectedScoringMode = document.querySelector('input[name="scoringMode"]:checked').value;
        
        // 获取候选数
        const candidatesCount = selectedMode === 'dual' 
            ? parseInt(dualCandidates.value) 
            : parseInt(singleCandidates.value);
        
        // 获取Top-K（空值表示不限制）
        const topKValue = topK.value.trim() ? parseInt(topK.value) : null;
        
        const requestBody = {
            version: experimentVersion,
            limit: uploadedQuestions.length,
            candidates: candidatesCount,
            score_rounds: parseInt(scoreRounds.value),
            top_k: uploadedQuestions.length,
            mode: selectedMode,
            scoring_mode: selectedScoringMode,
            scoring_model: scoringModel.value,
            scoring_top_k: topKValue
        };
        
        // 根据生成模式添加参数
        if (selectedMode === 'dual') {
            // 双模型模式
            requestBody.user_model = userModel.value;
            requestBody.agent_model = agentModel.value;
            requestBody.dialogue_rounds = parseInt(dialogueRounds.value);
        } else {
            // 单模型模式：添加生成轮数
            requestBody.num_turns = parseInt(singleDialogueRounds.value);
        }
        
        const expResult = await fetch('/api/experiments/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!expResult.ok) throw new Error('启动实验失败');
        
        // 启动日志监控
        console.log('实验版本:', experimentVersion);
        await sleep(2000); // 等待日志文件创建
        startLogUpdates(experimentVersion);
        
        // 第三步：等待实验完成（轮询结果）
        const modeText = selectedMode === 'dual' ? '双模型对话' : '单模型生成';
        const scoringText = selectedScoringMode === 'overall' ? '整体评分' : '逐轮评分';
        
        updateProgress(30, `正在${modeText}候选对话...`);
        await sleep(3000);
        
        updateProgress(50, `正在进行${scoringText}...`);
        await sleep(5000);
        
        updateProgress(70, '正在筛选最佳对话...');
        
        // 第四步：轮询检查实验状态（最多等待 10 分钟）
        updateProgress(80, '正在等待实验完成...');
        const maxAttempts = 120; // 120次 * 5秒 = 10分钟
        let attempts = 0;
        let resultFound = false;
        
        while (attempts < maxAttempts) {
            try {
                // 先检查实验状态
                const statusResponse = await fetch(`/api/experiments/${experimentVersion}/status`);
                if (statusResponse.ok) {
                    const statusData = await statusResponse.json();
                    console.log('状态检查:', statusData);
                    
                    if (statusData.success) {
                        const status = statusData.status;
                        const details = statusData.details || {};
                        
                        // 更新进度信息
                        if (status === 'completed') {
                            // 实验完成，获取结果
                            const success = await fetchResults();
                            if (success) {
                                resultFound = true;
                                break;
                            }
                        } else if (status === 'scoring') {
                            updateProgress(85, '正在进行评分... 已等待 ' + (attempts * 5) + ' 秒');
                        } else if (status === 'generating') {
                            updateProgress(83, '正在生成对话... 已等待 ' + (attempts * 5) + ' 秒');
                        } else {
                            // 显示日志尾部（如果有）
                            let msg = '实验运行中... 已等待 ' + (attempts * 5) + ' 秒';
                            if (details.log_tail) {
                                const lastLine = details.log_tail.split('\n').filter(l => l.trim()).slice(-1)[0];
                                if (lastLine) {
                                    msg += ' | ' + lastLine.substring(0, 50);
                                }
                            }
                            updateProgress(81, msg);
                        }
                    }
                }
            } catch (error) {
                console.error('检查状态时出错:', error);
            }
            
            attempts++;
            await sleep(5000); // 每5秒检查一次
        }
        
        if (!resultFound) {
            throw new Error('实验超时未完成。请检查后端日志：Outputs/' + experimentVersion + '/experiment.log');
        }
        
        updateProgress(95, '正在处理结果...');
        await sleep(500);
        
        updateProgress(100, '✅ 完成！');
        
        // 停止日志更新
        stopLogUpdates();
        
        // 最后获取一次完整日志
        await fetchLog(experimentVersion);
        
        // 显示结果
        showResults();
        showAlert('实验完成！可以下载结果了', 'success');
        downloadBtn.disabled = false;
        
    } catch (error) {
        // 停止日志更新
        stopLogUpdates();
        
        // 显示错误和日志
        showAlert('实验失败：' + error.message, 'error');
        if (experimentVersion) {
            await fetchLog(experimentVersion);
        }
        runBtn.disabled = false;
    }
}

// 上传问题到服务器
async function uploadQuestions() {
    // 清空并重写 questions.txt
    const response = await fetch('/api/questions/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions: uploadedQuestions })
    });
    
    if (!response.ok) throw new Error('上传问题失败');
}

// 获取结果
async function fetchResults() {
    // 改为获取评分结果文件
    const response = await fetch(`/api/results/${experimentVersion}/scores`);
    if (!response.ok) {
        if (response.status === 404) {
            throw new Error('WAITING'); // 特殊标记：结果还未准备好
        }
        throw new Error('获取结果失败');
    }
    
    const data = await response.json();
    if (data.success && data.data && data.data.length > 0) {
        resultData = data.data;
        return true;
    }
    throw new Error('WAITING');
}

// 显示结果统计
function showResults() {
    if (!resultData || resultData.length === 0) return;
    
    const totalQuestions = resultData.length;
    const totalDialogues = resultData.length;
    
    // 新格式: 3_final_results 没有分数字段，只显示问题数
    document.getElementById('totalQuestions').textContent = totalQuestions;
    document.getElementById('totalDialogues').textContent = totalDialogues;
    document.getElementById('avgScore').textContent = '已选最优';
    
    resultContainer.classList.add('show');
}

// 下载结果
function downloadResults() {
    if (!resultData || resultData.length === 0) {
        showAlert('没有可下载的结果', 'error');
        return;
    }
    
    console.log('最终结果数据示例:', resultData[0]); // 调试用
    
    // resultData 已经是格式化后的最终结果
    // 格式: {question_id, question, cot, answer}
    // 每个问题只有一条最高分的记录
    
    const formattedResults = resultData.map((item, index) => ({
        id: index + 1,
        question_id: item.question_id,
        question: item.question || '',
        cot: item.cot || '',
        answer: item.answer || '',
        version: experimentVersion
    }));
    
    // 创建下载链接
    const dataStr = JSON.stringify(formattedResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `final_results_${experimentVersion}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    showAlert(`最终结果已下载 (${formattedResults.length} 个问题，每题最高分)`, 'success');
}

// 更新进度
function updateProgress(percent, message) {
    progressFill.style.width = percent + '%';
    progressFill.textContent = percent + '%';
    statusMessage.textContent = message;
}

// 显示提示
function showAlert(message, type) {
    alert.textContent = message;
    alert.className = 'alert show alert-' + type;
    
    setTimeout(() => {
        alert.classList.remove('show');
    }, 3000);
}

// 辅助函数：延迟
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}