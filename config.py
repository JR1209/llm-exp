"""
实验配置文件
Prompt Pipeline v2.0 - 结构化改造版本
"""
import yaml
from pathlib import Path

# ================================
# API配置
# ================================
API_KEY = "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni"
API_BASE_URL = "https://live-turing.cn.llm.tcljd.com/api/v1"

# ================================
# 模型配置
# ================================
QWEN_MODEL = "qwen-max-latest"
GPT_MODEL = "turing/gpt-5.1-chat"

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
    """从prompts.yaml加载所有prompt配置"""
    prompts_file = Path(__file__).parent / "prompts.yaml"
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 加载prompts
_PROMPTS = load_prompts()

# 生成阶段 - 组件
GENERATION_ROLE = _PROMPTS['generation']['role']
GENERATION_TASK = _PROMPTS['generation']['task']
GENERATION_ROLES = _PROMPTS['generation']['roles']
GENERATION_CONSTRAINTS = _PROMPTS['generation']['constraints']
GENERATION_INPUT_TEMPLATE = _PROMPTS['generation']['input_template']
GENERATION_OUTPUT_FORMAT = _PROMPTS['generation']['output_format']

# 评估阶段 - 组件
EVALUATION_ROLE = _PROMPTS['evaluation']['role']
EVALUATION_TASK = _PROMPTS['evaluation']['task']
EVALUATION_DIMENSIONS_DESC = _PROMPTS['evaluation']['dimensions_desc']
EVALUATION_INPUT_TEMPLATE = _PROMPTS['evaluation']['input_template']
EVALUATION_OUTPUT_FORMAT = _PROMPTS['evaluation']['output_format']

# ================================
# 组装完整 Prompt - v2.0
# ================================
def build_generation_prompt(question: str, num_turns: int = GENERATION_NUM_TURNS) -> str:
    """构建生成阶段 Prompt"""
    return f"""
{GENERATION_ROLE}

{GENERATION_TASK.format(num_turns=num_turns, total_messages=num_turns * 2)}

{GENERATION_ROLES}

{GENERATION_CONSTRAINTS}

{GENERATION_INPUT_TEMPLATE.format(question=question)}

{GENERATION_OUTPUT_FORMAT.format(num_turns=num_turns, total_messages=num_turns * 2)}
"""

def build_evaluation_prompt(dialogue: str, dimensions: list = EVALUATION_DIMENSIONS) -> str:
    """构建评估阶段 Prompt"""
    return f"""
{EVALUATION_ROLE}

{EVALUATION_TASK}

{EVALUATION_DIMENSIONS_DESC.format(min_score=SCORE_RANGE[0], max_score=SCORE_RANGE[1])}

{EVALUATION_INPUT_TEMPLATE.format(dialogue=dialogue)}

{EVALUATION_OUTPUT_FORMAT}
"""

# ================================
# 向后兼容接口
# ================================
QWEN_GENERATION_PROMPT = build_generation_prompt("{question}")
GPT_SCORING_PROMPT = build_evaluation_prompt("{dialogue}")