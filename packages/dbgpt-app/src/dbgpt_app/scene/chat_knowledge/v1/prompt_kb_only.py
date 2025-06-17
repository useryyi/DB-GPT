from dbgpt._private.config import Config
from dbgpt.core import (
    ChatPromptTemplate,
    HumanPromptTemplate,
    MessagesPlaceholder,
    SystemPromptTemplate,
)
from dbgpt_app.scene import AppScenePromptTemplateAdapter, ChatScene
from dbgpt_app.scene.chat_normal.out_parser import NormalChatOutputParser

CFG = Config()

PROMPT_SCENE_DEFINE = """A chat between a curious user and an artificial intelligence \
assistant, who very familiar with database related knowledge. 
The assistant gives helpful, detailed, professional and polite answers to the user's \
questions. """


_KNOWLEDGE_BASE_ONLY_TEMPLATE_ZH = """ 你是一个专业的问答助手，专门基于知识库内容回答用户问题。

回答要求:
1. 严格基于提供的知识库内容回答问题，不能引用外部资料
2. 回答要准确、详细，保持专业性和客观性
3. 如果知识库内容能部分回答问题，请基于现有内容尽量详细回答
4. 保持回答的自然性，避免机械化的表述
5. 严格禁止编造任何不在知识库中的内容

无内容处理:
     如果知识库中没有相关信息，请回答: "抱歉，知识库中暂时没有相关信息来回答您的问题。"

格式要求:
     1. 如果知识库信息包含图片、链接、表格、代码块等特殊markdown格式，确保在答案中保持原有格式
     2. 适当使用markdown格式组织答案，提高可读性
     3. 禁止编造内容或引用不存在的资料来源

            知识库内容: 
            {context}
            
            用户问题:
            {question}
"""

_KNOWLEDGE_BASE_ONLY_TEMPLATE_EN = """ You are a professional Q&A assistant that specializes in answering user questions based on knowledge base content.

Answer Requirements:
1. Strictly answer questions based on the provided knowledge base content, do not cite external materials
2. Answers should be accurate, detailed, maintaining professionalism and objectivity
3. If knowledge base content can partially answer the question, provide as detailed an answer as possible based on existing content
4. Maintain natural answers, avoid mechanical expressions
5. Strictly prohibited from fabricating any content not in the knowledge base

No Content Handling:
     If there is no relevant information in the knowledge base, please answer: "Sorry, there is currently no relevant information in the knowledge base to answer your question."

Format Requirements:
    1. If knowledge base information contains special markdown formats such as images, links, tables, or code blocks, ensure to maintain the original format in the answer
    2. Appropriately use markdown format to organize answers for better readability
    3. Prohibited from fabricating content or citing non-existent data sources
    
            Knowledge Base Content: 
            {context}
            
            User Question:
            {question}
"""

_KNOWLEDGE_BASE_ONLY_TEMPLATE = (
    _KNOWLEDGE_BASE_ONLY_TEMPLATE_EN if CFG.LANGUAGE == "en" else _KNOWLEDGE_BASE_ONLY_TEMPLATE_ZH
)

PROMPT_NEED_STREAM_OUT = True
prompt_kb_only = ChatPromptTemplate(
    messages=[
        SystemPromptTemplate.from_template(_KNOWLEDGE_BASE_ONLY_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanPromptTemplate.from_template("{question}"),
    ]
)

prompt_adapter_kb_only = AppScenePromptTemplateAdapter(
    prompt=prompt_kb_only,
    template_scene=ChatScene.ChatKnowledge.value() + "_kb_only",
    stream_out=PROMPT_NEED_STREAM_OUT,
    output_parser=NormalChatOutputParser(),
)

# 注册知识库专用模板
CFG.prompt_template_registry.register(
    prompt_adapter_kb_only, language=CFG.LANGUAGE, is_default=False
)
