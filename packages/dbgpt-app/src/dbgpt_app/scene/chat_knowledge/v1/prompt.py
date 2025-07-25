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


<<<<<<< HEAD
_DEFAULT_TEMPLATE_ZH = """ 你是一个权威的问答专家，请基于提供的信息直接回答用户的问题。

回答要求:
1. 只能基于提供的已知内容回答，不能引用或编造其他资料来源
2. 回答要自然流畅，直接给出答案，不要提及信息来源
3. 如果提供的信息存在冲突，采用更准确的信息
4. 如果信息互补，自然地整合所有相关内容
5. 严格禁止编造内容，包括编造资料来源

无信息处理:
     如果提供的内容无法回答用户问题，请直接回答: "根据当前资料，无法提供这方面的具体信息。"

格式要求:
     1.如果已知信息包含图片、链接、表格、代码块等特殊markdown标签格式的信息，\
     确保在答案中包含原文这些标签，不要丢弃不要修改。
     2.回答时可以适当分点说明，使用markdown格式让内容更清晰。
     3.禁止编造任何内容，禁止引用"公开资料"、"历史文献"等不存在的来源。

=======
_DEFAULT_TEMPLATE_ZH = """ 基于以下给出的已知信息, 准守规范约束，专业、\
简要回答用户的问题.
规范约束:
     1.如果已知信息包含的图片、链接、表格、代码块等特殊markdown标签格式的信息，\
     确保在答案中包含原文这些图片、链接、表格和代码标签，不要丢弃不要修改，\
     如:图片格式：![image.png](xxx), 链接格式:[xxx](xxx), \
     表格格式:|xxx|xxx|xxx|, 代码格式:```xxx```.
     2.如果无法从提供的内容中获取答案, 请说: "知识库中提供的内容不足以回答此问题" \
     禁止胡乱编造.
     3.回答的时候最好按照1.2.3.点进行总结, 并以markdown格式显示.
>>>>>>> upstream/main
            已知内容: 
            {context}
            
            问题:
            {question}
"""
_DEFAULT_TEMPLATE_EN = """ You are an authoritative Q&A expert. Please answer user questions directly based on the provided information.

Answer Requirements:
1. Only answer based on the provided known content, do not cite or fabricate other sources
2. Answer naturally and fluently, give direct answers without mentioning information sources
3. If provided information conflicts, use more accurate information
4. If information is complementary, naturally integrate all relevant content
5. Strictly prohibited from fabricating content, including fabricating data sources

No Information Handling:
     If the provided content cannot answer the user's question, please directly answer: "Based on current materials, I cannot provide specific information on this topic."

Format Requirements:
    1.Ensure to include original markdown formatting elements such as images, links, \
    tables, or code blocks without alteration in the response if they are present in \
    the provided information.
<<<<<<< HEAD
    2.When responding, you may appropriately organize points and use markdown format to make content clearer.
    3.Prohibited from fabricating any content, prohibited from citing "public materials", "historical documents" or other non-existent sources.
    
=======
        For example, image format should be ![image.png](xxx), link format [xxx](xxx), \
        table format should be represented with |xxx|xxx|xxx|, and code format with xxx.
    2.If the information available in the knowledge base is insufficient to answer the \
    question, state clearly: "The content provided in the knowledge base is not enough \
    to answer this question," and avoid making up answers.
    3.When responding, it is best to summarize the points in the order of 1, 2, 3, And \
    displayed in markdown format.
>>>>>>> upstream/main
            known information: 
            {context}
            
            question:
            {question}
"""

_DEFAULT_TEMPLATE = (
    _DEFAULT_TEMPLATE_EN if CFG.LANGUAGE == "en" else _DEFAULT_TEMPLATE_ZH
)

PROMPT_NEED_STREAM_OUT = True
prompt = ChatPromptTemplate(
    messages=[
        SystemPromptTemplate.from_template(_DEFAULT_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanPromptTemplate.from_template("{question}"),
    ]
)

prompt_adapter = AppScenePromptTemplateAdapter(
    prompt=prompt,
    template_scene=ChatScene.ChatKnowledge.value(),
    stream_out=PROMPT_NEED_STREAM_OUT,
    output_parser=NormalChatOutputParser(),
)

CFG.prompt_template_registry.register(
    prompt_adapter, language=CFG.LANGUAGE, is_default=True
)
