# imports for langchain, plotly and Chroma
import os
import gradio as gr
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_core.prompts.chat import ChatPromptTemplate
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
)

# split documents into chunks
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

# Persist the vectorstore
collection = vectorstore._collection
count = collection.count()

# Print the number of vectors and their dimensions
sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
dimensions = len(sample_embedding)
print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")

# create chat with Gradio
llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    do_sample=False,
    repetition_penalty=1.03,
    provider="auto",  # let Hugging Face choose the best provider for you
)

model = ChatHuggingFace(llm=llm)

# set up the conversation memory for the chat
memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

# the retriever is an abstraction over the VectorStore that will be used during RAG
retriever = vectorstore.as_retriever()

# putting it together: set up the conversation chain with the GPT 3.5 LLM, the vector store and memory
template = (
    "Combine the chat history and follow up question into "
    "a standalone question. Chat History: {chat_history}"
    "Follow up question: {question}"
)

# providing context
# create a base prompt
system_prompt = """
You are a helpful assistant that answers questions based on the content of emails, which have been sent to the user.
The emails are stored in a vector database and you can retrieve relevant information from them.
The emails contain information about various topics, including personal and professional matters.
You should use the information from the emails to provide accurate and relevant answers.
You will be provided with a question and the chat history.
Use the information from the emails to provide accurate and relevant answers.
"""

base_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

# putting it together: set up the conversation chain with the GPT 3.5 LLM, the vector store and memory
chain = ConversationalRetrievalChain.from_llm(
    llm=model,
    retriever=retriever,
    memory=memory,
    condense_question_prompt=base_prompt,
  )

# wrapping that in a function
def chat(question, history):
    result = chain.invoke({"question": question})
    return result["answer"]

# And in Gradio:
view = gr.ChatInterface(chat, type="messages").launch(inbrowser=True)