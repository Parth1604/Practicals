"""LangGraph RAG pipeline with document grading and one query-rewrite retry.

    retrieve -> grade_documents -> generate                  (relevant docs found)
                                -> rewrite_query -> retrieve (none relevant, retries left)
                                -> fallback                  (none relevant, out of retries)
"""
from typing import Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from config import CHAT_MODEL, MAX_REWRITES, TOP_K
from store import get_vector_store

FALLBACK_ANSWER = "I don't know based on the Nimbus documents."

llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
retriever = get_vector_store().as_retriever(search_kwargs={"k": TOP_K})


class RagState(TypedDict, total=False):
    question: str               # original user question
    query: str                  # query actually sent to the retriever (may be rewritten)
    documents: list[Document]   # relevant documents after grading
    rewrites: int
    answer: str


# --- grading -----------------------------------------------------------------

class Grade(BaseModel):
    relevant: bool = Field(description="True if the document helps answer the question")


grade_prompt = ChatPromptTemplate.from_messages([
    ("system", "You judge whether a document from Nimbus Coffee Co.'s knowledge base contains "
               "information that helps answer the user's question. Be lenient: a document is relevant "
               "if it holds any fact needed for the answer, even if it is not enough on its own "
               "(e.g. one product's price when the question compares prices)."),
    ("human", "Document:\n{document}\n\nQuestion: {question}"),
])
grader = grade_prompt | llm.with_structured_output(Grade)

# --- generation --------------------------------------------------------------

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the customer assistant for Nimbus Coffee Co.\n"
               "Answer the question using ONLY the context below. Be concise and specific.\n"
               f'If the context does not contain the answer, say "{FALLBACK_ANSWER}"\n\n'
               "Context:\n{context}"),
    ("human", "{question}"),
])
answer_chain = answer_prompt | llm | StrOutputParser()

rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's question into a short search query for a coffee company's "
               "knowledge base (menu, hours, loyalty program, shipping, coffees, brewing, sourcing). "
               "Return only the query."),
    ("human", "{question}"),
])
rewrite_chain = rewrite_prompt | llm | StrOutputParser()


# --- nodes -------------------------------------------------------------------

def retrieve(state: RagState) -> RagState:
    query = state.get("query") or state["question"]
    return {"query": query, "documents": retriever.invoke(query)}


def grade_documents(state: RagState) -> RagState:
    docs = state["documents"]
    grades = grader.batch([{"document": d.page_content, "question": state["question"]} for d in docs])
    return {"documents": [d for d, g in zip(docs, grades) if g.relevant]}


def rewrite_query(state: RagState) -> RagState:
    return {
        "query": rewrite_chain.invoke({"question": state["question"]}),
        "rewrites": state.get("rewrites", 0) + 1,
    }


def generate(state: RagState) -> RagState:
    context = "\n\n---\n\n".join(d.page_content for d in state["documents"])
    return {"answer": answer_chain.invoke({"context": context, "question": state["question"]})}


def fallback(state: RagState) -> RagState:
    return {"answer": FALLBACK_ANSWER}


def route_after_grading(state: RagState) -> Literal["generate", "rewrite_query", "fallback"]:
    if state["documents"]:
        return "generate"
    if state.get("rewrites", 0) < MAX_REWRITES:
        return "rewrite_query"
    return "fallback"


def build_graph():
    g = StateGraph(RagState)
    g.add_node("retrieve", retrieve)
    g.add_node("grade_documents", grade_documents)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("generate", generate)
    g.add_node("fallback", fallback)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade_documents")
    g.add_conditional_edges("grade_documents", route_after_grading)
    g.add_edge("rewrite_query", "retrieve")
    g.add_edge("generate", END)
    g.add_edge("fallback", END)
    return g.compile()


rag_graph = build_graph()


def ask(question: str) -> RagState:
    return rag_graph.invoke({"question": question, "rewrites": 0})
