"""
定义 LLM 输出的数据结构（用于 Structured Outputs）
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ================================
# 生成对话的输出格式
# ================================

class DialogueTurn(BaseModel):
    """单轮对话"""
    role: str = Field(description="角色，User 或 Assistant")
    content: Optional[str] = Field(None, description="对话内容")
    message: Optional[str] = Field(None, description="对话内容（兼容字段）")
    
    @field_validator('content', mode='before')
    @classmethod
    def set_content(cls, v, info):
        """如果 content 为空但 message 有值，使用 message"""
        if v is None and info.data.get('message'):
            return info.data['message']
        return v


class GenerationOutput(BaseModel):
    """生成对话的完整输出"""
    question: Optional[str] = Field(None, description="原始问题")
    cot: str = Field(description="思维链推理过程（Chain of Thought）")
    dialogue: List[DialogueTurn] = Field(description="多轮对话列表")


# ================================
# 评分的输出格式
# ================================

class EvaluationOutput(BaseModel):
    """评分输出"""
    Empathy: float = Field(description="共情分数", ge=0, le=10)
    Supportiveness: float = Field(description="支持性分数", ge=0, le=10)
    Guidance: float = Field(description="指导性分数", ge=0, le=10)
    Safety: float = Field(description="安全性分数", ge=0, le=10)
