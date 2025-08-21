# imports for langchain, plotly and Chroma
import os
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma 
from FlagEmbedding import FlagReranker
from modules.tools_llm import tools, handle_tool_call


load_dotenv()

# Define the model to use
MODEL = "gpt-4o-mini"

# Initialize the OpenAI client
client = OpenAI()

"""
CREATE RETRIEVAL CHAIN
"""

# use hugging face embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_name = "vector_db"

# load vectorstore
vectorstore = Chroma(
    persist_directory=db_name, 
    embedding_function=embeddings
)

# creating a retreiver with a rankllm rerank
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 20},
)

# initiate a reranker from hugging face
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation


"""CREATE CHAT FUNCTION"""

def rerank_documents(documents, query, n=3):
    """
    Rerank documents received from the retriever

    Returns:
        list: List of reranked documents

    Args:
        documents (list): List of documents to rerank.
        query (str): The query to use for reranking.
    """

    # iterate through documents and compute scores
    scores = {}

    for doc in documents:

        # merge the metadata and page content into a single string
        doc_string = ", ".join([f"{str(k)}: {str(v)}" for k, v in doc.metadata.items()]) + "\n" + str(doc.page_content)
        score = reranker.compute_score([query, doc_string])
        scores[doc.metadata['id']] = score

    # filter the dictionary for the top n documents
    top_n_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:n]

    # create a list of documents based on the top n ids
    top_n_docs = [doc for doc in documents if doc.metadata['id'] in [doc_id for doc_id, _ in top_n_docs]]
    
    return top_n_docs


# chat for open ai
def chat_openai(message, history):

    # retrieve most relevant documents from retriever
    documents = retriever.invoke(message)

    # rerank the documents using the reranker
    reranked_docs = rerank_documents(documents, message)

    # transform the documents into a format that can be used by the model
    context = []
    for document in reranked_docs:
        context += document.page_content.replace("\n", " ")
        print(document.page_content)

    # join into a string
    context = "\n".join(context)

    # dictionary with messages
    messages = [
        {
            "role": "system",
            "content": 
                "You are a helpful assistant with access to the user's gmail inbox and google calendar through a vectorstore."
                "Each document in the vectorstore contains metadata about the email or calendar event."
                "You also have access to APIs through tools which can create and send emails on the user's behalf."
                "To reply to the user, use the following documents, and inform the user you are using the following documents:\n\n" + context
        }
    ]
    messages += history
    messages.append({
        "role": "user",
        "content": message
    })

    # Initial API call with tools
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" # Let the model decide when to call functions
    )

    # Print the response
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tool calls: {response.choices[0].message.tool_calls}")

    # # Check if the response contains tool calls
    if response.choices[0].message.tool_calls:
        message = response.choices[0].message
        response = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        response = client.chat.completions.create(model=MODEL, messages=messages)

    print(f"Final Response: {type(response.choices[0].message.content)}")
    return response.choices[0].message.content


# bring up a gradio interface
gr.ChatInterface(fn=chat_openai, type="messages").launch(inbrowser=True, share=True)