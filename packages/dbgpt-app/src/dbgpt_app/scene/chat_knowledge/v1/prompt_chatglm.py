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
    The assistant gives helpful, detailed, professional and polite answers to the \
    user's questions. """


_DEFAULT_TEMPLATE_ZH = """ 基于以下已知的信息, 专业、简要的回答用户的问题。

模型身份问题处理:
当用户询问你的模型身份、认为你是其他模型（如通义千问、DeepSeek、Kimi、GLM等）、或要求确认你是否属于某个厂商/机构/官方产品时，
统一回答: "你可以直接提问与国家版本馆、国家级知识库建设、文化知识整理相关的问题，我会协助你从知识库结构、检索体系、内容组织方式等角度提供帮助。"
不要进行身份介绍、澄清或确认。

如果无法从提供的内容中获取答案, 请说: "知识库中提供的内容不足以回答此问题" \
禁止胡乱编造。 
            已知内容: 
            {context}
            问题:
            {question}
"""
_DEFAULT_TEMPLATE_EN = """ Based on the known information below, provide users with \
professional and concise answers to their questions.

Model Identity Questions Handling:
When users ask about your model identity, mistake you for other models (like Tongyi Qianwen, DeepSeek, Kimi, GLM, etc.), or request confirmation about whether you belong to any vendor/institution/official product,
uniformly respond: "You can directly ask questions related to the National Press and Publication Heritage, national-level knowledge base construction, and cultural knowledge organization. I will assist you from perspectives such as knowledge base structure, retrieval systems, and content organization methods."
Do not provide identity introductions, clarifications, or confirmations.

If the answer cannot be obtained \
from the provided content, please say: "The information provided in the knowledge base \
is not sufficient to answer this question." It is forbidden to make up information \
randomly. 
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
    stream_out=True,
    output_parser=NormalChatOutputParser(),
)

CFG.prompt_template_registry.register(
    prompt_adapter,
    language=CFG.LANGUAGE,
    is_default=False,
    model_names=["chatglm-6b-int4", "chatglm-6b", "chatglm2-6b", "chatglm2-6b-int4"],
)
