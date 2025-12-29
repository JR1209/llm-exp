"""
文档索引脚本
将 documents/ 下的文档向量化并存储到 Chroma
"""

import os
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config_async import API_KEY, API_BASE_URL


def load_documents(directory: str = "documents") -> List:
    """加载文档目录下的所有文本文件"""
    docs_path = PROJECT_ROOT / directory
    
    if not docs_path.exists():
        raise FileNotFoundError(f"文档目录不存在: {docs_path}")
    
    files = list(docs_path.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"文档目录为空: {docs_path}")
    
    print(f"📂 找到 {len(files)} 个文档文件")
    
    loader = DirectoryLoader(
        str(docs_path),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    print(f"✅ 成功加载 {len(documents)} 个文档")
    return documents


def split_documents(documents: List, chunk_size: int = 500, chunk_overlap: int = 50) -> List:
    """切分文档为小块"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"📝 文档已切分为 {len(chunks)} 个块")
    return chunks


def create_vectorstore(chunks: List, persist_directory: str = "vectorstore"):
    """创建向量数据库"""
    persist_path = PROJECT_ROOT / persist_directory
    
    embeddings = OpenAIEmbeddings(
        openai_api_key=API_KEY,
        openai_api_base=API_BASE_URL,
        model="text-embedding-ada-002"
    )
    
    print(f"🔄 正在向量化文档...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_path)
    )
    
    print(f"✅ 向量库已保存到: {persist_path}")
    return vectorstore


def main():
    """主函数"""
    print("=" * 80)
    print("📚 心理咨询案例向量化索引")
    print("=" * 80)
    
    try:
        print("\n[步骤 1/3] 加载文档...")
        documents = load_documents()
        
        print("\n[步骤 2/3] 切分文档...")
        chunks = split_documents(documents, chunk_size=500, chunk_overlap=50)
        
        print("\n[步骤 3/3] 创建向量库...")
        vectorstore = create_vectorstore(chunks)
        
        print("\n" + "=" * 80)
        print("🎉 索引完成！")
        print("=" * 80)
        print(f"📊 统计信息:")
        print(f"  - 文档数量: {len(documents)}")
        print(f"  - 文档块数: {len(chunks)}")
        print(f"  - 向量库路径: {PROJECT_ROOT / 'vectorstore'}")
        print("\n现在可以运行实验并使用 --use-rag 参数启用 RAG 功能")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()