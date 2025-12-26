"""
定义 LLM 输出的数据结构（用于 Structured Outputs）
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


# ================================
# 生成对话的输出格式
# ================================

class DialogueTurn(BaseModel):
    """单轮对话"""
    role: str = Field(description="角色，必须是 'User' 或 'Assistant'")
    content: str = Field(description="对话内容，不能为空")
    
    @model_validator(mode='before')
    @classmethod
    def handle_message_field(cls, data: Any) -> Any:
        """兼容 message 字段（某些模型可能返回 message 而非 content）"""
        if isinstance(data, dict):
            # 如果没有 content 但有 message，则使用 message
            if 'content' not in data and 'message' in data:
                data['content'] = data['message']
        return data
    
    class Config:
        # 允许额外字段（兼容 message 字段）
        extra = 'allow'


class GenerationOutput(BaseModel):
    """生成对话的完整输出"""
    question: str = Field(description="原样返回的原始问题")
    cot: str = Field(description="思维链推理过程，包括情绪识别、问题分析、对话策略")
    dialogue: List[DialogueTurn] = Field(description="多轮对话列表，User 和 Assistant 交替")
    
    class Config:
        # 允许额外字段以提高兼容性
        extra = 'allow'


# ================================
# 评分的输出格式
# ================================

class EvaluationOutput(BaseModel):
    """评分输出"""
    Empathy: float = Field(description="共情分数：咨询师理解并回应求助者情绪的程度", ge=0, le=10)
    Supportiveness: float = Field(description="支持性分数：咨询师给予情感支持的程度", ge=0, le=10)
    Guidance: float = Field(description="指导性分数：咨询师提供有效建议和引导的程度", ge=0, le=10)
    Safety: float = Field(description="安全性分数：咨询师回复的专业性和安全性", ge=0, le=10)
    
    class Config:
        # 允许额外字段以提高兼容性
        extra = 'allow'
