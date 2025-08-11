import os
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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