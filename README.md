# 实验项目 - 版本管理指南

## 📁 项目结构

```
Code/
├── config.py              # API配置、模型配置
├── prompts.yaml           # Prompt模板
├── run_experiment.py      # 主执行脚本
├── dvc.yaml               # DVC pipeline定义
├── dvc.lock               # DVC依赖锁定文件
├── params.yaml            # 实验参数
├── requirements.txt       # Python依赖
├── inputs/
│   └── questions.txt      # 输入问题集（Git管理）
└── Outputs/               # 实验输出（DVC管理）
    └── v1/
        ├── qwen_candidates_v1.jsonl
        ├── gpt_scores_v1.jsonl
        ├── top_results_v1.jsonl
        └── experiment_v1.log
```

## 🎯 版本管理策略

### Git管理（代码和配置）
- ✅ `config.py` - API、模型配置
- ✅ `prompts.yaml` - Prompt模板
- ✅ `run_experiment.py` - 执行脚本
- ✅ `inputs/questions.txt` - 问题集（小文件）
- ✅ `dvc.yaml`, `dvc.lock` - DVC配置

### DVC管理（大数据和输出）
- ✅ `Outputs/` - 所有实验输出结果

---

## 🚀 快速开始

### 1. 环境设置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行实验

```bash
# 运行实验
dvc repro

# 查看结果
ls Outputs/v1/
cat Outputs/v1/top_results_v1.jsonl
```

---

## 📝 日常工作流程

### 场景1: 修改Prompt后运行新实验

```bash
# 1. 修改prompt
vim prompts.yaml

# 2. 提交修改
git add prompts.yaml
git commit -m "Update generation prompt for better empathy"

# 3. 运行实验
dvc repro

# 4. 提交结果
git add dvc.lock Outputs.dvc
git commit -m "exp: Results with improved prompt"

# 5. 打标签（可选）
git tag v2
git push origin master --tags
dvc push
```

### 场景2: 添加新问题后运行实验

```bash
# 1. 添加问题
echo "新的问题内容" >> inputs/questions.txt

# 2. 提交修改
git add inputs/questions.txt
git commit -m "Add question about depression"

# 3. 运行实验（会自动检测问题集变化）
dvc repro

# 4. 提交结果
git add dvc.lock Outputs.dvc
git commit -m "exp: Results with new question"
git tag v3
```

### 场景3: 修改API配置

```bash
# 1. 修改config.py
vim config.py

# 2. 提交
git add config.py
git commit -m "config: Update API timeout to 180s"

# 3. 运行实验
dvc repro

# 4. 提交结果
git add dvc.lock Outputs.dvc
git commit -m "exp: Results with longer timeout"
```

---

## 🔄 版本切换

### 查看所有版本

```bash
# 查看提交历史
git log --oneline

# 查看所有标签
git tag
```

### 切换到旧版本

```bash
# 方法1: 使用commit hash
git checkout 640ecdd
dvc checkout

# 方法2: 使用标签
git checkout v1
dvc checkout

# 查看旧版本的文件
cat prompts.yaml
cat inputs/questions.txt
ls Outputs/v1/
```

### 切换回最新版本

```bash
git checkout master
dvc checkout
```

### 比较不同版本

```bash
# 比较prompt差异
git diff v1 v2 -- prompts.yaml

# 比较问题集差异
git diff v1 v2 -- inputs/questions.txt

# 比较代码差异
git diff v1 v2 -- run_experiment.py
```

---

## ⚙️ DVC工作机制

### 什么时候会触发重新运行？

修改以下文件并提交后，`dvc repro`会自动检测变化：

- ✅ `config.py`
- ✅ `prompts.yaml`
- ✅ `run_experiment.py`
- ✅ `inputs/questions.txt`

**重要**: 必须先`git commit`，DVC才能检测到变化！

### 完整流程

```bash
# 1. 修改文件
vim prompts.yaml
git log --oneline
# 2. 提交（关键步骤！）
git add prompts.yaml
git commit -m "Update prompt"

# 3. 运行
dvc repro  # ✅ 会检测到变化并重新运行
```

### 如果DVC说"Stage didn't change"？

```bash
# 强制重新运行
dvc repro --force

# 或删除lock文件
rm dvc.lock
dvc repro
```

---

## 📊 实验参数管理

### 当前参数（params.yaml）

```yaml
prompt_version: v1
temperature: 0.7
model: gpt-4
```

### 修改参数

```bash
# 1. 编辑params.yaml
vim params.yaml

# 2. 提交
git add params.yaml
git commit -m "params: Change temperature to 0.9"

# 3. 运行
dvc repro
```

---

## 🐛 常见问题

### Q1: 修改了文件但DVC没检测到？

**原因**: 没有`git commit`

**解决**:
```bash
git add <修改的文件>
git commit -m "说明"
dvc repro
```

### Q2: 切换版本后Outputs是空的？

**原因**: 没有执行`dvc checkout`

**解决**:
```bash
git checkout v1
dvc checkout  # 加上这句
ls Outputs/
```

### Q3: dvc checkout报错说没有缓存？

**原因**: 那个版本的输出从未推送过

**解决**: 切回master重新运行
```bash
git checkout master
dvc repro
dvc push
```

### Q4: 有未提交的修改，无法切换版本？

```bash
# 方法1: 提交修改
git add .
git commit -m "Save changes"
git checkout v1

# 方法2: 暂存修改
git stash
git checkout v1
# 回来后恢复
git checkout master
git stash pop
```

---

## 📋 实验前检查清单

- [ ] 虚拟环境已激活 (`source venv/bin/activate`)
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] Git工作区干净 (`git status`)
- [ ] 修改已提交 (`git commit`)
- [ ] 参数配置正确 (`cat params.yaml`)

---

## 📈 版本命名规范

### Git Commit Message

```bash
exp(v2): 实验相关的修改
config: 配置文件修改
fix: Bug修复
data: 数据变更
docs: 文档更新
```

### Git Tag

```bash
v1 - 基线实验
v2 - 改进的prompt
v3 - 新增问题集
v4 - 参数调优
```

---

## 🎓 最佳实践

1. **每次实验后立即提交**
   ```bash
   git add dvc.lock Outputs.dvc
   git commit -m "exp: 描述实验内容"
   git tag vX
   ```

2. **定期推送到远程**
   ```bash
   git push origin master --tags
   dvc push
   ```

3. **重要版本打标签**
   ```bash
   git tag -a v1 -m "Baseline experiment"
   ```

4. **记录实验笔记**
   - 在commit message中详细描述
   - 或维护单独的EXPERIMENTS.md

---

## 🔗 相关资源

- [DVC官方文档](https://dvc.org/doc)
- [Git文档](https://git-scm.com/doc)
- 项目Wiki（如果有）

---

## 📞 联系方式

如有问题，请联系：zl.zhang@xxx.com