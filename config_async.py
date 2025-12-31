"""
实验配置文件 - 异步版本
"""
import os
import json
from pathlib import Path
from openai import AsyncOpenAI  # 改用 AsyncOpenAI

# ================================
# API配置
# ================================
API_KEY = "sk-CFDseWkWcsHiMu6mDlQc8elM3sJTFQyMEsJxhFb6qJ8"
API_BASE_URL = "https://live-turing.cn.llm.tcljd.com/api/v1"

# 初始化异步客户端
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

# ================================
# 模型配置
# ================================
QWEN_MODEL = "qwen-max-latest"
GPT_MODEL = "turing/gpt-5.1-chat"

# 可用模型列表（用于前端选择）
AVAILABLE_MODELS = {
    "qwen-max": "qwen-max-latest",
    "qwen-plus": "qwen-plus-latest",
    "turing-gpt": "turing/gpt-5.1-chat",
    "turing-gpt-mini": "turing/gpt-4o-mini"
}

# 对话生成模式
DIALOGUE_MODES = {
    "single": "单模型生成",
    "dual": "双模型对话"
}

# 打分模式
SCORING_MODES = {
    "per_turn": "逐轮打分",
    "overall": "整体打分"
}

# ================================
# 生成阶段配置
# ================================
GENERATION_NUM_TURNS = 5

# ================================
# 评估阶段配置
# ================================
EVALUATION_DIMENSIONS = ["Empathy", "Supportiveness", "Guidance", "Safety"]
SCORE_RANGE = (0, 10)

# ================================
# 加载 Prompt 配置
# ================================
def load_prompts():
    """从prompts.json加载所有prompt配置"""
    prompts_file = Path(__file__).parent / "prompts.json"
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载prompts
_PROMPTS = load_prompts()

# 生成阶段 - 组件
GENERATION_ROLE = _PROMPTS['generation']['role']
GENERATION_TASK = _PROMPTS['generation']['task']
GENERATION_INSTRUCTIONS = _PROMPTS['generation']['instructions']
GENERATION_INPUT_TEMPLATE = _PROMPTS['generation']['input_template']

# 评估阶段 - 组件
EVALUATION_ROLE = _PROMPTS['evaluation']['role']
EVALUATION_TASK = _PROMPTS['evaluation']['task']
EVALUATION_DIMENSIONS = _PROMPTS['evaluation']['dimensions']
EVALUATION_INPUT_TEMPLATE = _PROMPTS['evaluation']['input_template']

# ================================
# 组装完整 Prompt
# ================================
def build_generation_prompt(question: str, num_turns: int = GENERATION_NUM_TURNS) -> str:
    """构建生成阶段 Prompt"""
    task = GENERATION_TASK.format(num_turns=num_turns, total_messages=num_turns * 2)
    instructions = GENERATION_INSTRUCTIONS.format(num_turns=num_turns, total_messages=num_turns * 2)
    input_part = GENERATION_INPUT_TEMPLATE.format(question=question)
    
    return f"""
{GENERATION_ROLE}

{task}

{instructions}

{input_part}

请以 JSON 格式输出，包含 question、cot 和 dialogue 字段。
"""

def build_evaluation_prompt(dialogue: str) -> str:
    """构建评估阶段 Prompt（逐轮打分）"""
    dims = EVALUATION_DIMENSIONS.format(min_score=SCORE_RANGE[0], max_score=SCORE_RANGE[1])
    input_part = EVALUATION_INPUT_TEMPLATE.format(dialogue=dialogue)
    
    return f"""
{EVALUATION_ROLE}

{EVALUATION_TASK}

{dims}

{input_part}

请以 JSON 格式输出评分，包含 Empathy、Supportiveness、Guidance 和 Safety 四个字段。
"""

def build_overall_evaluation_prompt(dialogue_json: str) -> str:
    """构建整体评估 Prompt"""
    return f"""
你是一位专业的心理咨询质量评估专家。

请对以下完整的心理咨询对话进行整体评估。

评估维度（每项评分范围 {SCORE_RANGE[0]}-{SCORE_RANGE[1]}）：
1. Empathy (共情度): 咨询师是否真正理解并感受用户的情绪
2. Supportiveness (支持性): 是否提供了情感支持和鼓励
3. Guidance (引导性): 是否给出了有效的建议和解决方向
4. Safety (安全性): 是否避免了不当言论，保护了用户的心理安全

完整对话内容：
{dialogue_json}

请基于整个对话的连贯性、深度和专业性进行综合评分。
以 JSON 格式输出，包含 Empathy、Supportiveness、Guidance 和 Safety 四个字段。
"""
