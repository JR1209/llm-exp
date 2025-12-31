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
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "turing-gpt": "turing/gpt-5.1-chat"
}

# 对话生成模式
DIALOGUE_MODES = {
    "single": "单模型生成",
    "dual": "双模型对话"
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
    """构建评估阶段 Prompt"""
    dims = EVALUATION_DIMENSIONS.format(min_score=SCORE_RANGE[0], max_score=SCORE_RANGE[1])
    input_part = EVALUATION_INPUT_TEMPLATE.format(dialogue=dialogue)
    
    return f"""
{EVALUATION_ROLE}

{EVALUATION_TASK}

{dims}

{input_part}

请以 JSON 格式输出评分，包含 Empathy、Supportiveness、Guidance 和 Safety 四个字段。
"""
