# gmail_worker
Chat application to serve as an assistant with access to your Gmail inbox

## Setup Instructions

### 1. Create the Environment

To set up the Python environment, use the provided `.environment.yml` file:

```bash
conda env create -f .environment.yml
conda activate gmail_worker
```

### 2. Google Cloud Credentials

This application requires a Google Cloud `client_id` and `client_secret` for authenticating with your Gmail account.  
Create a `.env` file in the project root with the following content:

```
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
```

You can obtain these credentials from your Google Cloud project.

### 3. Ollama and Llama 3.2

The app uses [Ollama](https://ollama.com/) for local LLM inference.  
Install Ollama and pull the Llama 3.2 model specifically:

```bash
# Install Ollama (see https://ollama.com/download)
ollama pull llama3.2
```

### 4. Chat UI

The chat interface is built with [Gradio](https://www.gradio.app/).  
When you run the app, a web UI will launch and provide a shareable link for others to access the chat.
