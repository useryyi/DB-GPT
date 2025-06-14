import json
import logging
import os
from functools import reduce
from typing import Dict, List, Type

logger = logging.getLogger(__name__)

from dbgpt import SystemApp
from dbgpt.core import (
    ChatPromptTemplate,
    HumanPromptTemplate,
    MessagesPlaceholder,
    SystemPromptTemplate,
)
from dbgpt.core.interface.llm import ModelOutput
from dbgpt.rag.retriever.rerank import RerankEmbeddingsRanker
from dbgpt.rag.retriever.rewrite import QueryRewrite
from dbgpt.util.tracer import root_tracer, trace
from dbgpt_app.knowledge.request.request import KnowledgeSpaceRequest
from dbgpt_app.knowledge.service import KnowledgeService
from dbgpt_app.scene import BaseChat, ChatScene
from dbgpt_app.scene.base_chat import ChatParam
from dbgpt_app.scene.chat_knowledge.v1.config import ChatKnowledgeConfig
from dbgpt_serve.rag.models.chunk_db import DocumentChunkDao, DocumentChunkEntity
from dbgpt_serve.rag.models.document_db import (
    KnowledgeDocumentDao,
    KnowledgeDocumentEntity,
)
from dbgpt_serve.rag.retriever.knowledge_space import KnowledgeSpaceRetriever
from dbgpt_app.knowledge.neo4j_service import Neo4jQueryService


class ChatKnowledge(BaseChat):
    """KBQA Chat Module"""

    chat_scene: str = ChatScene.ChatKnowledge.value()

    @classmethod
    def param_class(cls) -> Type[ChatKnowledgeConfig]:
        return ChatKnowledgeConfig

    def __init__(self, chat_param: ChatParam, system_app: SystemApp):
        """Chat Knowledge Module Initialization
        Args:
           - chat_param: Dict
            - chat_session_id: (str) chat session_id
            - current_user_input: (str) current user input
            - model_name:(str) llm model name
            - select_param:(str) space name
        """
        from dbgpt.rag.embedding.embedding_factory import RerankEmbeddingFactory

        self.curr_config = chat_param.real_app_config(ChatKnowledgeConfig)
        self.knowledge_space = chat_param.select_param
        super().__init__(chat_param=chat_param, system_app=system_app)
        from dbgpt_serve.rag.models.models import (
            KnowledgeSpaceDao,
        )

        space_dao = KnowledgeSpaceDao()
        space = space_dao.get_one({"name": self.knowledge_space})
        if not space:
            space = space_dao.get_one({"id": self.knowledge_space})
        if not space:
            raise Exception(f"have not found knowledge space:{self.knowledge_space}")
        self.rag_config = self.app_config.rag
        self.space_context = self.get_space_context(space.name)

        self.top_k = self.get_knowledge_search_top_size(space.name)
        self.recall_score = self.get_similarity_score_threshold()

        query_rewrite = None
        if self.rag_config.query_rewrite:
            query_rewrite = QueryRewrite(
                llm_client=self.llm_client,
                model_name=self.llm_model,
                language=self.system_app.config.configs.get(
                    "dbgpt.app.global.language"
                ),
            )
        reranker = None
        retriever_top_k = self.top_k
        if self.model_config.default_reranker:
            rerank_embeddings = RerankEmbeddingFactory.get_instance(
                self.system_app
            ).create()
            rerank_top_k = self.curr_config.knowledge_retrieve_rerank_top_k
            if not rerank_top_k:
                rerank_top_k = self.rag_config.rerank_top_k
            reranker = RerankEmbeddingsRanker(rerank_embeddings, topk=rerank_top_k)
            if retriever_top_k < rerank_top_k or retriever_top_k < 20:
                # We use reranker, so if the top_k is less than 20,
                # we need to set it to 20
                retriever_top_k = max(rerank_top_k, 20)
        self._space_retriever = KnowledgeSpaceRetriever(
            space_id=space.id,
            embedding_model=self.model_config.default_embedding,
            top_k=retriever_top_k,
            query_rewrite=query_rewrite,
            rerank=reranker,
            llm_model=self.llm_model,
            system_app=self.system_app,
        )

        self.prompt_template.template_is_strict = False
        self.relations = None
        self.chunk_dao = DocumentChunkDao()
        document_dao = KnowledgeDocumentDao()
        documents = document_dao.get_documents(
            query=KnowledgeDocumentEntity(space=space.name)
        )
        if len(documents) > 0:
            self.document_ids = [document.id for document in documents]
        
        # Initialize Neo4j query service
        try:
            # Import the simplified Neo4j service that doesn't require LangChain chains
            import sys
            import os
            sys.path.insert(0, '/home/yannic/work/github/DB-GPT')
            from simple_neo4j_service import SimpleNeo4jQueryService
            
            self.neo4j_service = SimpleNeo4jQueryService()
            is_connected = self.neo4j_service.is_connected()
            logger.info(f"Simplified Neo4j service initialized, connected: {is_connected}")
            if not is_connected:
                logger.warning("Neo4j service is not connected. Check if Neo4j server is running at 192.168.102.59:7687")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
            self.neo4j_service = None

    async def _handle_final_output(
        self, final_output: ModelOutput, incremental: bool = False
    ):
        reference = f"\n\n{self.parse_source_view(self.chunks_with_score)}"
        view_message = final_output.text
        view_message = view_message + reference

        if final_output.has_thinking and not incremental:
            view_message = final_output.gen_text_with_thinking(new_text=view_message)
        return final_output.text, view_message

    def stream_call_reinforce_fn(self, text):
        """return reference"""
        return text + f"\n\n{self.parse_source_view(self.chunks_with_score)}"

    @trace()
    async def generate_input_values(self) -> Dict:
        if self.space_context and self.space_context.get("prompt"):
            # Not use template_define
            # Replace the template with the prompt template
            self.prompt_template.prompt = ChatPromptTemplate(
                messages=[
                    SystemPromptTemplate.from_template(
                        self.space_context["prompt"]["template"]
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    HumanPromptTemplate.from_template("{question}"),
                ]
            )
        from dbgpt.util.chat_util import run_async_tasks

        user_input = self.current_user_input.last_text

        tasks = [self.execute_similar_search(user_input)]
        candidates_with_scores = await run_async_tasks(tasks=tasks, concurrency_limit=1)
        candidates_with_scores = reduce(lambda x, y: x + y, candidates_with_scores)
        
        # Execute Neo4j query in parallel with knowledge base search
        neo4j_results = []
        neo4j_context = ""
        if self.neo4j_service and self.neo4j_service.is_connected():
            try:
                logger.info(f"Executing Neo4j query for: {user_input}")
                neo4j_results = self.neo4j_service.query_graph(user_input, limit=5)
                logger.info(f"Neo4j returned {len(neo4j_results)} results")
                if neo4j_results:
                    # Format Neo4j results - handle various node types, integrate naturally
                    neo4j_context = ""
                    for i, record in enumerate(neo4j_results, 1):
                        # Process each node in the record
                        for key, node in record.items():
                            if hasattr(node, '_properties') and hasattr(node, 'labels'):
                                props = node._properties
                                labels = list(node.labels)
                                
                                # Get node name - try multiple possible name fields
                                node_name = (props.get('nodeName') or 
                                           props.get('人物名称') or 
                                           props.get('名称') or 
                                           props.get('name') or 
                                           props.get('title') or 
                                           props.get('标题') or '未知')
                                
                                # Format as natural text without rigid structure
                                if '人物' in labels:
                                    # For person nodes, create natural description
                                    career = props.get('职业', '')
                                    achievements = props.get('主要成就', '')
                                    death_date = props.get('逝世日期', '')
                                    birthplace = props.get('出生地', '')
                                    
                                    person_info = f"{node_name}"
                                    if career:
                                        person_info += f"，{career}"
                                    if achievements:
                                        # Split achievements to avoid repetition and limit length
                                        achievement_parts = achievements.split('；')[:2]  # Take first 2 parts only
                                        if achievement_parts:
                                            person_info += f"，{achievement_parts[0]}"
                                    if death_date:
                                        person_info += f"，逝世于{death_date}"
                                    if birthplace and birthplace != '未知':
                                        person_info += f"，出生地为{birthplace}"
                                    
                                    neo4j_context += person_info + "。\n"
                                else:
                                    # For other node types, create natural description
                                    label_text = labels[0] if labels else '项目'
                                    node_info = f"{node_name}（{label_text}）"
                                    
                                    # Add key properties naturally, limit to avoid repetition
                                    properties = []
                                    for prop_key, prop_value in props.items():
                                        if (prop_key not in ['nodeName', '人物名称', '名称', 'name', 'title', '标题', 'resourceId'] 
                                            and prop_value and str(prop_value).strip() and len(properties) < 3):
                                            # Limit property value length to avoid repetition
                                            prop_str = str(prop_value)[:100]
                                            properties.append(f"{prop_key}：{prop_str}")
                                    
                                    if properties:
                                        node_info += "，" + "，".join(properties)
                                    
                                    neo4j_context += node_info + "。\n"
                            else:
                                # Fallback for non-node objects
                                neo4j_context += f"{str(node)[:100]}。\n"
                            
                            # Only process the first node to avoid duplication
                            break
                    neo4j_context = neo4j_context.strip()
                    logger.info(f"Neo4j context generated: {neo4j_context[:200]}...")
            except Exception as e:
                logger.error(f"Error querying Neo4j: {e}")
        else:
            logger.warning("Neo4j service is not available or not connected, skipping Neo4j query")
        
        self.chunks_with_score = []
        knowledge_base_context = ""
        if not candidates_with_scores or len(candidates_with_scores) == 0:
            print("no relevant docs to retrieve")
            knowledge_base_context = ""
        else:
            self.chunks_with_score = []
            for chunk in candidates_with_scores:
                chucks = self.chunk_dao.get_document_chunks(
                    query=DocumentChunkEntity(content=chunk.content),
                    document_ids=self.document_ids,
                )
                if len(chucks) > 0:
                    self.chunks_with_score.append((chucks[0], chunk.score))

            knowledge_base_context = "\n".join([doc.content for doc in candidates_with_scores])
        
        # Combine contexts based on priority rules
        final_context = ""
        if neo4j_context and knowledge_base_context:
            # Both have content - combine them with clear separation
            final_context = f"{knowledge_base_context}\n\n{neo4j_context}"
            logger.info("Combined knowledge base and Neo4j results")
        elif neo4j_context:
            # Only Neo4j has content
            final_context = neo4j_context
            logger.info("Using only Neo4j results as knowledge base has no content")
        elif knowledge_base_context:
            # Only knowledge base has content
            final_context = knowledge_base_context
            logger.info("Using only knowledge base results as Neo4j has no content")
        else:
            # Neither has content
            final_context = ""
            logger.info("Neither Neo4j nor knowledge base returned content")
        
        self.relations = list(
            set(
                [
                    os.path.basename(str(d.metadata.get("source", "")))
                    for d in candidates_with_scores
                ]
            )
        )
        input_values = {
            "context": final_context,
            "question": user_input,
            "relations": self.relations,
            "neo4j_context": neo4j_context,
            "knowledge_base_context": knowledge_base_context,
        }
        return input_values

    def parse_source_view(self, chunks_with_score: List):
        """
        format knowledge reference view message to web
        <references title="'References'" references="'[{name:aa.pdf,chunks:[{10:text},{11:text}]},{name:bb.pdf,chunks:[{12,text}]}]'"> </references>
        """  # noqa
        import xml.etree.ElementTree as ET

        references_ele = ET.Element("references")
        title = "References"
        references_ele.set("title", title)
        references_dict = {}
        for chunk, score in chunks_with_score:
            doc_name = chunk.doc_name
            if doc_name not in references_dict:
                references_dict[doc_name] = {
                    "name": doc_name,
                    "chunks": [
                        {
                            "id": chunk.id,
                            "content": chunk.content,
                            "meta_info": chunk.meta_info,
                            "recall_score": score,
                        }
                    ],
                }
            else:
                references_dict[doc_name]["chunks"].append(
                    {
                        "id": chunk.id,
                        "content": chunk.content,
                        "meta_info": chunk.meta_info,
                        "recall_score": score,
                    }
                )
        references_list = list(references_dict.values())
        references_ele.set(
            "references", json.dumps(references_list, ensure_ascii=False)
        )
        html = ET.tostring(references_ele, encoding="utf-8")
        reference = html.decode("utf-8")
        return reference.replace("\\n", "")

    def get_space_context_by_id(self, space_id):
        service = KnowledgeService()
        return service.get_space_context_by_space_id(space_id)

    def get_space_context(self, space_name):
        service = KnowledgeService()
        return service.get_space_context(space_name)

    def get_knowledge_search_top_size(self, space_name) -> int:
        if self.space_context:
            return int(self.space_context["embedding"]["topk"])

        service = KnowledgeService()
        request = KnowledgeSpaceRequest(name=space_name)
        spaces = service.get_knowledge_space(request)
        if len(spaces) == 1:
            from dbgpt_ext.storage import __knowledge_graph__ as graph_storages

            if spaces[0].vector_type in graph_storages:
                return self.rag_config.kg_chunk_search_top_k
        if self.curr_config.knowledge_retrieve_top_k:
            return self.curr_config.knowledge_retrieve_top_k

        return self.rag_config.similarity_top_k

    def get_similarity_score_threshold(self):
        if self.space_context:
            return float(self.space_context["embedding"]["recall_score"])
        if self.curr_config.similarity_score_threshold >= 0:
            return self.curr_config.similarity_score_threshold
        return self.rag_config.similarity_score_threshold

    async def execute_similar_search(self, query):
        """execute similarity search"""
        with root_tracer.start_span(
            "execute_similar_search", metadata={"query": query}
        ):
            return await self._space_retriever.aretrieve_with_scores(
                query, self.recall_score
            )
    
    def __del__(self):
        """Cleanup Neo4j connection when object is destroyed."""
        if hasattr(self, 'neo4j_service') and self.neo4j_service:
            try:
                self.neo4j_service.close()
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
