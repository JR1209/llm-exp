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

// 日志更新定时器
let logUpdateInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
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
        const expResult = await fetch('/api/experiments/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                version: experimentVersion,
                limit: uploadedQuestions.length,
                candidates: 2,
                score_rounds: 3,
                top_k: uploadedQuestions.length
            })
        });
        
        if (!expResult.ok) throw new Error('启动实验失败');
        
        // 启动日志监控
        console.log('实验版本:', experimentVersion);
        await sleep(2000); // 等待日志文件创建
        startLogUpdates(experimentVersion);
        
        // 第三步：等待实验完成（轮询结果）
        updateProgress(30, 'Qwen 正在生成候选对话...');
        await sleep(3000);
        
        updateProgress(50, 'GPT 正在进行多维度评分...');
        await sleep(5000);
        
        updateProgress(70, '正在选择最佳对话...');
        
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
    
    // 计算平均分（兼容两种数据结构）
    const avgScore = resultData.reduce((sum, item) => {
        const score = item.scores?.Total || item.avg_score || 0;
        return sum + score;
    }, 0) / totalQuestions;
    
    document.getElementById('totalQuestions').textContent = totalQuestions;
    document.getElementById('totalDialogues').textContent = totalDialogues;
    document.getElementById('avgScore').textContent = avgScore.toFixed(2);
    
    resultContainer.classList.add('show');
}

// 下载结果
function downloadResults() {
    if (!resultData || resultData.length === 0) {
        showAlert('没有可下载的结果', 'error');
        return;
    }
    
    console.log('原始评分数据示例:', resultData[0]); // 调试用
    
    // 直接下载评分结果（gpt_scores 格式）
    // 格式：包含所有候选对话和它们的评分
    const formattedResults = resultData.map((item, index) => {
        const scores = item.scores || {};
        const output = item.output || {};
        
        // 提取对话内容
        let dialogue = '';
        if (output.dialogue) {
            if (Array.isArray(output.dialogue)) {
                // JSON 格式：[{role: "User", content: "..."}, ...]
                dialogue = output.dialogue.map(msg => 
                    `${msg.role}: ${msg.content}`
                ).join('\n');
            } else if (typeof output.dialogue === 'string') {
                // 纯文本格式
                dialogue = output.dialogue;
            }
        }
        
        return {
            id: index + 1,
            question_id: item.question_id,
            candidate_id: item.candidate_id,
            question: item.question || output.question || '',
            answer: dialogue,
            scores: {
                empathy: scores.Empathy || 0,
                supportiveness: scores.Supportiveness || 0,
                guidance: scores.Guidance || 0,
                safety: scores.Safety || 0,
                total: scores.Total || 0
            },
            cot: output.cot || null,
            version: experimentVersion
        };
    });
    
    // 创建下载链接
    const dataStr = JSON.stringify(formattedResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `qa_scores_${experimentVersion}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    showAlert(`评分结果已下载 (${formattedResults.length} 条记录，包含完整对话)`, 'success');
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