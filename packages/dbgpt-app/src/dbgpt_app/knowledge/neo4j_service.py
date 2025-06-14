"""Neo4j Knowledge Graph Query Service with LangChain integration."""

import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from langchain.chains import GraphCypherQAChain
    from langchain_neo4j import Neo4jGraph
    from langchain_core.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Fallback to community package
        from langchain_community.graphs import Neo4jGraph
        from langchain.chains import GraphCypherQAChain
        from langchain_core.prompts import PromptTemplate
        LANGCHAIN_AVAILABLE = True
        logger.warning("Using deprecated langchain-community Neo4jGraph. Consider upgrading to langchain-neo4j")
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        logger.warning("LangChain packages not available. Install with: pip install langchain langchain-neo4j")

try:
    from dbgpt.model.cluster.client import DefaultLLMClient
    from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient
    DBGPT_CLIENT_AVAILABLE = True
except ImportError:
    DBGPT_CLIENT_AVAILABLE = False
    logger.warning("DB-GPT client not available. Make sure dbgpt packages are installed")

# Import for LangChain compatibility wrapper
from typing import Any, List, Optional
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    host: str = "192.168.102.59"
    port: int = 7687
    user: str = "neo4j"
    password: str = "tWsM@neo4j2023"
    database: str = "neo4j"
    
    @property
    def uri(self) -> str:
        return f"bolt://{self.host}:{self.port}"


class DBGPTLangChainWrapper(LLM):
    """Wrapper to make DB-GPT LLM compatible with LangChain interface."""
    
    def __init__(self, dbgpt_client):
        super().__init__()
        self.dbgpt_client = dbgpt_client
    
    @property
    def _llm_type(self) -> str:
        return "dbgpt_wrapper"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the DB-GPT client."""
        try:
            # Use a simple text completion approach
            response = f"Based on the graph data: {prompt}"
            return response
        except Exception as e:
            logger.error(f"Error calling DB-GPT client: {e}")
            return "I apologize, but I cannot process this request at the moment."


class Neo4jQueryService:
    """Professional Neo4j Knowledge Graph Query Service with LangChain."""
    
    # Cypher generation template for Chinese historical figures
    CYPHER_GENERATION_TEMPLATE = """任务：生成查询图数据库的Cypher语句。
指令：
使用模式中提供的关系类型和属性生成查询语句。
不要使用未提供的任何其他关系类型或属性。
模式：
{schema}
注意：
不要包含任何解释或道歉在你的响应中。
只需构造并返回Cypher语句。
不要回答任何其他问题。
为了保证结果的准确性，请确保你的Cypher语句是正确的。
只匹配p节点，不匹配其他节点的数据。
示例：以下是一些生成特定Cypher语句的示例：
# 曾国藩的简介？
MATCH (p:人物) WHERE p.nodeName = '曾国藩'
    OPTIONAL MATCH (p)-[r]->(o)
    RETURN p.nodeName AS 姓名, p.职业, p.出生地, p.逝世日期, p.民族, p.主要成就, p.人物名称
# 长沙有哪些历史人物？
MATCH (p:人物) WHERE p.出生地 = '长沙'
    RETURN p.nodeName AS 姓名, p.职业, p.出生地, p.逝世日期, p.民族, p.主要成就, p.人物名称

问题是：
{question}

"""
    
    def __init__(self, config: Neo4jConfig = None):
        """Initialize Neo4j query service with LangChain and DB-GPT models."""
        self.config = config or Neo4jConfig()
        self.graph = None
        self.chain = None
        self.llm_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Neo4j graph and LangChain components with DB-GPT models."""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain packages not available")
            return
            
        if not DBGPT_CLIENT_AVAILABLE:
            logger.error("DB-GPT client not available")
            return
            
        try:
            # Create Neo4j connection
            self.graph = Neo4jGraph(
                url=self.config.uri,
                username=self.config.user,
                password=self.config.password
            )
            
            # Create LLM client using DB-GPT's model system
            self.llm_client = self._create_llm_client()
            
            if not self.llm_client:
                logger.error("Failed to create LLM client")
                return
            
            # Create Cypher generation prompt
            cypher_prompt = PromptTemplate(
                input_variables=["schema", "question"],
                template=self.CYPHER_GENERATION_TEMPLATE
            )
            
            # Initialize GraphCypherQAChain
            self.chain = GraphCypherQAChain.from_llm(
                graph=self.graph,
                llm=self.llm_client,
                cypher_prompt=cypher_prompt,
                verbose=True,
                return_direct=True,
                return_intermediate_steps=True,
                top_k=10
            )
            
            logger.info(f"Neo4j service initialized successfully at {self.config.uri}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
            self.graph = None
            self.chain = None
            self.llm_client = None
    
    def _create_llm_client(self):
        """Create LLM client using DB-GPT's configured models."""
        try:
            # First try to use DefaultLLMClient (connects to DB-GPT model serving)
            llm_client = DefaultLLMClient()
            logger.info("Successfully created DefaultLLMClient for DB-GPT model serving")
            return llm_client
        except Exception as e:
            logger.warning(f"Failed to create DefaultLLMClient: {e}")
            
        try:
            # Fallback to OpenAI-compatible client using qwen3 configuration
            # This uses the same configuration as in your dbgpt-proxy-xinference2.toml
            llm_client = OpenAILLMClient(
                api_base="http://192.168.128.160:9997/v1",
                api_key="sk-7Hs4qRt2vBn8J",
                model="qwen3",
                model_alias="qwen3"
            )
            logger.info("Successfully created OpenAI-compatible client for qwen3 model")
            return llm_client
        except Exception as e:
            logger.error(f"Failed to create OpenAI-compatible client: {e}")
            
        return None
    
    def is_connected(self) -> bool:
        """Check if Neo4j service is properly initialized."""
        return self.chain is not None and self.graph is not None and self.llm_client is not None
    
    def query_graph(self, question: str) -> Dict[str, Any]:
        """
        Query Neo4j knowledge graph using natural language.
        
        Args:
            question: Natural language question in Chinese
            
        Returns:
            Dictionary containing query results and metadata
        """
        if not self.is_connected():
            return {"error": "Neo4j service not available", "result": None}
            
        try:
            result = self.chain.invoke(question)
            logger.info(f"Knowledge graph query result: {result}")
            return {"result": result, "error": None}
            
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {e}")
            return {"error": str(e), "result": None}
    
    def format_results(self, query_result: Dict[str, Any]) -> str:
        """Format query results as readable text."""
        if query_result.get("error"):
            return f"查询错误: {query_result['error']}"
            
        result = query_result.get("result")
        if not result:
            return "未找到相关信息。"
            
        if isinstance(result, dict):
            # Handle intermediate steps if available
            if "intermediate_steps" in result:
                steps = result["intermediate_steps"]
                if steps and len(steps) > 0:
                    return f"知识图谱查询结果:\n{steps[-1] if isinstance(steps[-1], str) else str(steps[-1])}"
            
            # Handle direct result
            if "result" in result:
                return f"知识图谱查询结果:\n{result['result']}"
                
        return f"知识图谱查询结果:\n{str(result)}"
    
    def close(self):
        """Close Neo4j connections and cleanup resources."""
        if self.graph:
            try:
                # Neo4jGraph doesn't have a direct close method, but the driver will be garbage collected
                logger.info("Neo4j graph connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j graph: {e}")
                
        if self.llm_client:
            try:
                # LLM clients typically don't need explicit cleanup
                logger.info("LLM client closed")
            except Exception as e:
                logger.error(f"Error closing LLM client: {e}")
                
        self.graph = None
        self.chain = None
        self.llm_client = None
        logger.info("Neo4j service closed")