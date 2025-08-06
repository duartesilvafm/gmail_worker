# imports for langchain, plotly and Chroma
import os
import gradio as gr
from langchain import hub
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

# load emails into directory
folders = "emails/"

# loader
loader = DirectoryLoader(folders, glob="**/*.md", loader_cls=TextLoader)
folder_docs = loader.load()

# text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_documents(folder_docs)
print(f"Total number of chunks: {len(chunks)}")

# use hugging face embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_name = "vector_db"

# if the vector store already exists, delete it
if os.path.exists(db_name):
    Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

# Create vectorstore
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
print(f"Vectorstore created with {vectorstore._collection.count()} documents")

# create chat with Gradio
llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
    provider="auto",  # let Hugging Face choose the best provider for you
)

llm = ChatHuggingFace(llm=llm)

# the retriever is an abstraction over the VectorStore that will be used during RAG
retriever = vectorstore.as_retriever()

# pull qa system prompt
retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
print(retrieval_qa_chat_prompt)


# combine docs
combine_docs_chain = create_stuff_documents_chain(
    llm, retrieval_qa_chat_prompt
)

# create a retrieval chain with the LLM and the retriever
retrieval_chain = create_retrieval_chain(
    retriever=retriever,
    combine_docs_chain=combine_docs_chain
)

# wrapping that in a function
def chat(question, history):
    result = retrieval_chain.invoke(
        {
            "input": question,
            "chat_history": history
        }
    )
    return result["answer"]

# And in Gradio:
view = gr.ChatInterface(chat, type="messages").launch(inbrowser=True)