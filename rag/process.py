import json
from json import JSONDecodeError
from typing import Tuple

from llama_index.core import StorageContext, VectorStoreIndex, ChatPromptTemplate, SimpleDirectoryReader
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore

from log_structure import LogCluster
from config import log_metadata, TRA_TYPE_domain_knowledge, TRA_TYPE_most_frequent_tokens



# FIXME: can't contain '{}' directly in template, or it will be treated as format kwargs.
#  to fix it, pass '{}' as arguments
system_template_str = '''
Term(s) you need to know in advance:
Log cluster: Each log cluster comprises log messages sharing the same template. For example, there are two log messages: 
  1.CE sym 2, at 0x0b85eee0, mask 0x05
  2.CE sym 27, at 0x11b3f3c0, mask 0x10
They share the same template (similar to regex pattern): CE sym <*> at <*> mask <*>. The template is also called as "template of log cluster".

Requirements:
- Always answer the question. If the context isn't helpful, answer the question on your own.
- Judge whether a log cluster indicates system anomaly.
- The answer must be pure JSON string, with three fields:
    1.result, yes or no to indicate whether the log indicates a system anomaly; 
    2.score: confidence of the result, range from 0 to 1; 
    3.reason: explain reason of the judgement.
  example of required json output: {output_sample}
'''

question_template_str = '''
We have provided context information below. If the context isn't helpful, answer the question on your own.
---------------------
{context_str}
---------------------
Some metadata of this log cluster: {log_metadata}.
Answer question:
Query: {query_str}
Template: {log_cluster}
Example log messages that match the template:
\t{samples}
Answer:
'''

node_content_tmpl_str = '''
Is this an anomaly log cluster? {is_anomaly}
confidence score: {score}
reason: {reason}
----------------------------------
log cluster's template: {template}
examples:
\t{samples}
\t...
'''

chat_text_qa_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=system_template_str,
    ),
    ChatMessage(
        role=MessageRole.USER,
        content=question_template_str,
    ),
]
chat_text_qa_tmpl = ChatPromptTemplate(chat_text_qa_msgs)

# Attu client addr: http://10.58.137.244:8888/
vector_store = MilvusVectorStore(uri='http://10.58.137.244:19530', dim=1536, collection_name='scale_ad_collection')
storage_context = StorageContext.from_defaults(vector_store=vector_store)

embed_model = OpenAIEmbedding()

# connect directly to vector database
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=100, chunk_overlap=0),
        TitleExtractor(),
        OpenAIEmbedding(),
    ]
)

# nodes = pipeline.run(documents=SimpleDirectoryReader(input_files=['rag/data/log-info.log']).load_data())

# Create your index
index = VectorStoreIndex.from_vector_store(vector_store)

# index.insert_nodes(nodes)

query_engine = index.as_query_engine()


def rag_feedback(log_cluster: LogCluster) -> Tuple[int, int, str]:
    template = chat_text_qa_tmpl.partial_format(log_metadata=f'Environment: {log_metadata}; Level: {log_cluster.metadata[TRA_TYPE_domain_knowledge]}; Most Frequent Tokens: {log_cluster.metadata[TRA_TYPE_most_frequent_tokens]}',
                                                log_cluster=log_cluster.template,
                                                samples='\n\t'.join(log_cluster.get_log_messages()[0:10]),
                                                output_sample='{result:yes, score: 0.7, reason:the reason is ...')
    query_engine.update_prompts({"response_synthesizer:text_qa_template": template})
    response = query_engine.query('Does this type of log message indicate an anomaly?')
    # FIXME: llm sometimes is stupid, the response is not in pure json:
    #  ```json{...}```
    decision, score, reason = -1, -1, 'no feedback yet'
    try:
        data = json.loads(str(response)).values()
        result, score, reason = tuple(data)
        decision = 1 if result == 'yes' else 0
    except JSONDecodeError as e:
        print(e)
    return decision, score, reason


def rag_insert(log_cluster: LogCluster):
    metadata = {
        "log cluster's template": log_cluster.template,
        'log level': log_cluster.metadata[TRA_TYPE_domain_knowledge],
        "log cluster's most frequent tokens": log_cluster.metadata[TRA_TYPE_most_frequent_tokens]
    }
    samples = '\n\t'.join(log_cluster.get_log_messages()[0:10])

    node_content = node_content_tmpl_str.format(is_anomaly='true' if log_cluster.feedback.decision else 'false',
                                                score=log_cluster.feedback.ep,
                                                reason=log_cluster.feedback.reason,
                                                template=log_cluster.template,
                                                samples=samples)
    node = TextNode(id_=hash(log_cluster.template),
                    text=node_content,
                    metadata=metadata,
                    embedding=embed_model.get_text_embedding(node_content))
    index.insert_nodes([node])
