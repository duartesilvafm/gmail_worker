# imports for langchain, plotly and Chroma
import os
import gradio as gr
from dotenv import load_dotenv
from modules.tools_llm import tools, handle_tool_call
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma 
from openai import OpenAI

load_dotenv()

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

"""CREATE CHAT FUNCTION"""

# Define the model to use
MODEL = "openai/gpt-oss-120b:cerebras"

# Initialize the OpenAI client
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

# chat for open ai
def chat_openai(message, history, vectorstore=vectorstore):

    # create a retrieval chain
    documents = vectorstore.similarity_search(message, k=5)

    # transform the documents into a format that can be used by the model
    context = []
    for document in documents:
        context += document.page_content.replace("\n", " ")
        print(document.page_content)

    # join into a string
    context = "\n".join(context)

    # dictionary with messages
    messages = [
        {
            "role": "system",
            "content": 
                "You are a helpful assistant with access to the user's gmail inbox through a vectorstore."
                "You also have access to APIs through tools which can create and send emails on the user's behalf."
                "To reply to the user, you have access to the following context:\n\n" + context
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