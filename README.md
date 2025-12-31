# 🧠 心理咨询对话生成系统

**AI驱动的多模型对话生成与评分平台**

---

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [端口服务管理](#端口服务管理)
- [常见问题](#常见问题)

---

## 🎯 项目简介

本系统用于生成高质量的心理咨询对话，支持单模型/双模型生成，逐轮/整体评分，所有实验结果通过MLflow和SQLite进行版本管理和追踪。

### 技术栈
- **后端**: Python 3.12 + Flask + AsyncIO
- **前端**: 原生HTML/CSS/JavaScript
- **数据库**: SQLite + MLflow
- **AI模型**: Qwen, GPT系列

---

## ✨ 核心功能

### 1. 双对话生成模式
- **单模型生成**: 一个AI模型生成完整的咨询对话
- **双模型对话**: User模型和Agent模型交替对话，模拟真实咨询场景

### 2. 双打分模式
- **逐轮打分**: 对每轮对话独立评分（共情、支持、引导、安全）
- **整体打分**: 对完整对话进行综合评估

### 3. 自定义Prompt
- **直接输入**: 在文本框中手动输入prompt
- **文件上传**: 支持上传JSON/TXT格式的prompt文件

### 4. 实验管理
- **MLflow追踪**: 自动记录所有实验参数、代码快照、Git版本
- **SQLite存储**: 完整的实验元数据和结果存储
- **Top-K筛选**: 自动保留每个问题得分最高的K个对话

---

## 📁 项目结构

## 📁 项目结构

```
Code_test/
├── 🔧 核心配置
│   ├── config_async.py           # API配置、模型列表、Prompt构建
│   ├── prompts.json              # Prompt模板库
│   └── requirements.txt          # Python依赖
│
├── 🎯 主执行脚本
│   ├── 运行_async_sqlite.py      # 主实验脚本（异步+MLflow+SQLite）
│   ├── start_simple.py           # Web服务启动脚本
│   └── backend_api.py            # Flask API服务器
│
├── 🧩 核心模块
│   ├── pipeline/
│   │   ├── generation_async.py          # 单模型生成
│   │   ├── generation_dual_async.py     # 双模型对话生成
│   │   ├── scoring_async.py             # 逐轮打分
│   │   ├── scoring_overall_async.py     # 整体打分
│   │   └── selection.py                 # Top-K选择
│   │
│   ├── core/
│   │   └── schemas.py              # Pydantic数据模型
│   │
│   ├── utils/
│   │   └── io_handler.py           # 文件读写、格式化
│   │
│   └── sqlite_handler.py           # SQLite数据库操作
│
├── 🖥️ 前端界面
│   └── frontend_simple/
│       ├── index.html              # 主页面（横向布局）
│       └── app.js                  # 前端交互逻辑
│
├── 📥 输入数据
│   └── inputs/
│       └── questions.txt           # 问题集
│
├── 📤 输出结果
│   ├── Outputs/                    # 实验输出（按版本组织）
│   │   └── v{timestamp}/
│   │       ├── 1_generation_*.json
│   │       ├── 2_scores_*.json
│   │       └── 3_final_results_*.json
│   │
│   └── logs/                       # 实验日志
│       └── experiment_*.log
│
├── 💾 数据存储
│   ├── experiments.db              # SQLite数据库（实验元数据）
│   ├── mlflow.db                   # MLflow数据库
│   └── mlruns/                     # MLflow实验文件
│
└── 📚 文档
    ├── README.md                   # 本文档
    ├── TEST_INSTRUCTIONS.md        # 测试说明
    └── PROMPT_UPLOAD_TEST.md       # Prompt上传测试
```
---

## 📄 核心文件说明

### 配置文件
| 文件 | 作用 |
|------|------|
| `config_async.py` | API配置、模型列表、Prompt构建函数 |
| `prompts.json` | 生成和评分的Prompt模板库 |

### 主脚本
| 文件 | 作用 |
|------|------|
| `运行_async_sqlite.py` | 命令行运行实验（完整流程：生成→评分→筛选） |
| `start_simple.py` | 启动Web服务（集成前后端） |
| `backend_api.py` | Flask API（处理前端请求） |

### Pipeline模块
| 文件 | 作用 |
|------|------|
| `generation_async.py` | 单模型生成对话 |
| `generation_dual_async.py` | 双模型交替对话（User+Agent） |
| `scoring_async.py` | 逐轮打分（每轮独立评分） |
| `scoring_overall_async.py` | 整体打分（综合评估完整对话） |
| `selection.py` | Top-K筛选 |

### 数据处理
| 文件 | 作用 |
|------|------|
| `core/schemas.py` | Pydantic数据模型（JSON验证） |
| `utils/io_handler.py` | 文件读写、格式化输出 |
| `sqlite_handler.py` | SQLite数据库操作（保存/查询实验） |

### 前端
| 文件 | 作用 |
|------|------|
| `frontend_simple/index.html` | 主界面（横向布局，5步骤） |
| `frontend_simple/app.js` | 前端逻辑（文件上传、模式切换、API调用） |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd /data/zl.zhang/Code_test

# 激活虚拟环境
source /data/zl.zhang/Code/venv/bin/activate

# 安装依赖（如未安装）
pip install -r requirements.txt
```

### 2. 启动Web服务

```bash
python3 start_simple.py
```

**访问地址**: `http://localhost:9123`

### 3. 使用前端界面

1. **步骤1: 上传问题集与配置**
   - 左侧：上传问题文件（.json 或 .txt）
   - 右侧：可选上传生成Prompt（直接输入或上传文件）

2. **步骤2: 生成配置**
   - 选择生成模式：单模型 / 双模型
   - 单模型：选择模型 + 对话轮数 + 候选数
   - 双模型：选择User模型、Agent模型 + 对话轮数 + 候选数

3. **步骤3: 打分配置**
   - 左侧：选择打分模式（逐轮/整体）+ 打分模型 + 打分轮次 + Top-K
   - 右侧：可选上传打分Prompt

4. **步骤4: 运行实验**
   - 点击「🚀 开始实验」
   - 查看实时进度和日志

5. **步骤5: 下载结果**
   - 实验完成后点击「💾 下载 QA 结果集」

### 4. 命令行运行

```bash
# 单模型 + 逐轮打分
python3 运行_async_sqlite.py \
  --mode single \
  --num-turns 5 \
  --scoring-mode per_turn \
  --scoring-model turing-gpt \
  --limit 10

# 双模型 + 整体打分 + Top-K
python3 运行_async_sqlite.py \
  --mode dual \
  --user-model qwen-max \
  --agent-model turing-gpt \
  --dialogue-rounds 3 \
  --scoring-mode overall \
  --scoring-model turing-gpt \
  --scoring-top-k 2 \
  --limit 10
```

---

## 📖 使用指南

### 对话生成模式

#### 单模型生成
一个AI模型生成完整的User-Agent对话

**适用场景**: 快速生成、一致性要求高

**配置**:
- 模型: `qwen-max`, `qwen-plus`, `turing-gpt`
- 对话轮数: 1-10轮
- 候选数: 每个问题生成N个候选对话

#### 双模型对话
User模型和Agent模型交替对话

**适用场景**: 更自然的对话、多样性高

**配置**:
- User模型: `qwen-max` (扮演求助者)
- Agent模型: `turing-gpt` (扮演咨询师)
- 对话轮数: 1-10轮
- 候选数: 每个问题生成N个候选对话

### 打分模式

#### 逐轮打分
对每轮对话独立评分，最后取平均

**评分维度**:
- **Empathy** (共情度): 0-10分
- **Supportiveness** (支持性): 0-10分
- **Guidance** (引导性): 0-10分
- **Safety** (安全性): 0-10分

#### 整体打分
对完整对话进行综合评估

**优势**: 考虑对话连贯性和整体质量

### Prompt管理

#### 方式1: 直接输入
在文本框中手动输入prompt

#### 方式2: 文件上传
支持两种格式：

**TXT格式**:
```txt
你是一位专业的心理咨询师。
请生成温暖、共情的对话。
```

**JSON格式**:
```json
{
  "role": "心理咨询师",
  "style": "温暖、专业",
  "requirements": ["共情", "支持", "引导"]
}
```

### 命令行参数说明

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `--limit` | 处理的问题数量 | 10 | 1-1000 |
| `--candidates` | 每个问题生成的候选数 | 2 | 1-10 |
| `--score-rounds` | 每个候选评分轮次 | 3 | 1-10 |
| `--scoring-mode` | 打分模式 | per_turn | per_turn/overall |
| `--scoring-model` | 打分使用的模型 | turing-gpt | - |
| `--scoring-top-k` | 保留前K个结果 | None | 1-N |
| `--num-turns` | 单模型对话轮数 | 5 | 1-10 |
| `--dialogue-rounds` | 双模型对话轮数 | 3 | 1-10 |
| `--mode` | 生成模式 | single | single/dual |
| `--user-model` | 双模型User模型 | qwen-max | - |
| `--agent-model` | 双模型Agent模型 | turing-gpt | - |

---

## 🛠️ 端口服务管理

### 本系统端口

#### Web服务 (端口 9123)

**启动服务**:
```bash
python3 start_simple.py
```

**访问**:
- 本地: `http://localhost:9123`
- 远程: `http://<服务器IP>:9123`

**停止服务**: 按 `Ctrl+C`

**后台运行**:
```bash
nohup python3 start_simple.py > web_9123.log 2>&1 &

# 停止
pkill -f start_simple.py
```

#### MLflow UI (端口 9001)
**启动服务**:
```bash
nohup mlflow ui --host 0.0.0.0 --port 9001 > mlflow_9001.log 2>&1 &
```

**访问**: `http://localhost:9001`

**查看日志**:
```bash
tail -f mlflow_9001.log
```

**停止服务**:
```bash
pkill -f "mlflow ui.*9001"
# 或
pkill -f "mlflow ui"
```

#### Datasette SQLite可视化 (端口 8001)

**启动服务**:
```bash
nohup datasette experiments.db --host 0.0.0.0 --port 8001 > datasette_8001.log 2>&1 &
```

**访问**: `http://localhost:8001`

**停止服务**:
```bash
pkill -f "datasette.*8001"
# 或
pkill -f datasette
```

### 端口状态检查

```bash
# 查看所有监听端口
netstat -tlnp | grep -E '9123|9001|8001'

# 或使用 ss
ss -tlnp | grep -E '9123|9001|8001'

# 查看进程
ps aux | grep -E 'start_simple|mlflow|datasette'
```

### 一键管理脚本

**启动所有服务**:
```bash
# 启动Web
nohup python3 start_simple.py > web_9123.log 2>&1 &

# 启动MLflow
nohup mlflow ui --host 0.0.0.0 --port 9001 > mlflow_9001.log 2>&1 &

# 启动Datasette
nohup datasette experiments.db --host 0.0.0.0 --port 8001 > datasette_8001.log 2>&1 &

echo "所有服务已启动"
netstat -tlnp | grep -E '9123|9001|8001'
```

**停止所有服务**:
```bash
pkill -f start_simple.py
pkill -f "mlflow ui"
pkill -f datasette

echo "所有服务已停止"
```

---

## 💾 数据存储说明

### 存储位置

| 类型 | 路径 | 内容 |
|------|------|------|
| **SQLite数据库** | `experiments.db` | 实验元数据、配置、结果索引 |
| **MLflow数据库** | `mlflow.db` | MLflow元数据（run_id、参数、指标） |
| **MLflow文件** | `mlruns/` | 实验文件（代码快照、输入、输出） |
| **实验输出** | `Outputs/v{timestamp}/` | 生成结果、评分结果、最终结果 |
| **日志文件** | `logs/` | 实验运行日志 |
| **临时文件** | `temp_*.txt` | 临时保存的自定义prompt |

### 数据流关系

```
用户请求 → Flask API → 运行实验脚本
                ↓
         生成对话 (Pipeline)
                ↓
         评分 (Pipeline)
                ↓
         筛选 (Pipeline)
                ↓
    ┌───────┴───────┐
    ↓               ↓
SQLite存储    MLflow存储
(结构化数据)  (文件+元数据)
    ↓               ↓
  查询接口      UI可视化
```
---

## ❓ 常见问题

### Q1: 双模型对话中Agent模型返回空响应？

**现象**: 日志显示 `API返回空响应 [gpt-4o-mini]`

**原因**: 模型名称不支持或API限制

**解决**:
```bash
# 使用支持的模型
--agent-model turing-gpt
# 或
--agent-model qwen-max
```

### Q2: 评分都是0分？

**原因**: 对话不完整（Agent模型失败导致只有User发言）

**解决**: 检查模型配置，确保Agent模型正常工作

### Q3: 如何查看实验日志？

```bash
# 实验运行日志
tail -f logs/experiment_v{version}.log

# Web服务日志
tail -f web_9123.log

# MLflow日志
tail -f mlflow_9001.log
```

### Q4: 端口被占用？

```bash
# 查看占用端口的进程
lsof -i :9123

# 杀死进程
kill -9 <PID>

# 或修改端口
python3 start_simple.py --port 9124
```

### Q5: 如何清理旧实验数据？

```bash
# 清理输出文件（保留最近10个版本）
ls -dt Outputs/v* | tail -n +11 | xargs rm -rf

# 清理日志（保留最近30天）
find logs/ -name "*.log" -mtime +30 -delete

# 清理临时文件
rm -f temp_*.txt
```

### Q6: 前端上传的Prompt在哪里？

临时保存在项目根目录：
- `temp_generation_prompt.txt` - 生成prompt
- `temp_scoring_prompt.txt` - 打分prompt

### Q7: 如何备份实验数据？

```bash
# 备份数据库
cp experiments.db experiments_backup_$(date +%Y%m%d).db
cp mlflow.db mlflow_backup_$(date +%Y%m%d).db

# 备份实验文件
tar -czf mlruns_backup_$(date +%Y%m%d).tar.gz mlruns/
tar -czf outputs_backup_$(date +%Y%m%d).tar.gz Outputs/
```

---

## 📊 实验结果查看

### 方式1: 前端界面

访问 `http://localhost:9123`，完成实验后点击「下载结果」

### 方式2: MLflow UI

访问 `http://localhost:9001`
- 查看所有实验记录
- 对比不同版本参数
- 下载Artifacts（代码快照、输出文件）

### 方式3: Datasette

访问 `http://localhost:8001`
- SQL查询实验数据
- 导出CSV/JSON
- 数据可视化

### 方式4: 命令行

```bash
# 查看最新实验结果
ls -lt Outputs/ | head -5

# 查看生成结果
cat Outputs/v{timestamp}/1_generation_*.json | jq .

# 查看评分结果
cat Outputs/v{timestamp}/2_scores_*.json | jq .

# 查看最终结果
cat Outputs/v{timestamp}/3_final_results_*.json | jq .
```

---

## 🔧 高级配置

### 自定义Prompt示例

**生成Prompt (generation_custom.txt)**:
```
你是一位资深心理咨询师，拥有10年临床经验。

对话风格：
- 温暖、耐心、非评判性
- 使用开放式问题引导
- 适时提供专业建议

注意事项：
- 避免医学诊断
- 保持专业边界
- 关注来访者安全
```

**打分Prompt (scoring_custom.txt)**:
```
评分标准：

1. Empathy (0-10分)
   - 8-10分: 深度理解情绪，准确反映
   - 5-7分: 基本理解，略显表面
   - 0-4分: 缺乏共情或误解

2. Supportiveness (0-10分)
   - 8-10分: 强有力的情感支持和鼓励
   - 5-7分: 有支持但力度不足
   - 0-4分: 缺乏支持或负面

...
```

### 批量实验运行

```bash
# 创建批量脚本
cat > batch_experiments.sh << 'EOF'
#!/bin/bash

# 实验1: 单模型
python3 运行_async_sqlite.py --mode single --version batch_v1 --limit 50

# 实验2: 双模型
python3 运行_async_sqlite.py --mode dual --version batch_v2 --limit 50

# 实验3: 不同评分模式
python3 运行_async_sqlite.py --scoring-mode overall --version batch_v3 --limit 50

EOF

chmod +x batch_experiments.sh
./batch_experiments.sh
```

---

## 📚 参考资料

- [MLflow文档](https://mlflow.org/docs/latest/index.html)
- [Datasette文档](https://docs.datasette.io/)
- [Flask文档](https://flask.palletsprojects.com/)
- [AsyncIO文档](https://docs.python.org/3/library/asyncio.html)

---

## 👥 贡献者

- **开发**: zl.zhang
- **项目路径**: `/data/zl.zhang/Code_test`

---

## 📝 更新日志

### v2.0 (2025-01-31)
- ✅ 添加双模型对话功能
- ✅ 添加整体打分模式
- ✅ 支持自定义Prompt（文本+文件）
- ✅ 打分模型可选择
- ✅ 前端界面重构（横向布局）
- ✅ 添加Json_diff按钮（预留）

### v1.0 (2025-01-30)
- ✅ 基础对话生成功能
- ✅ 逐轮打分功能
- ✅ MLflow集成
- ✅ SQLite存储
- ✅ Web界面

---

**如有问题，请查看日志或联系开发者。**

