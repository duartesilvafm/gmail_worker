# Gmail-Worker
Chat application to serve as an assistant with access to your Gmail inbox and able to create and send drafts.

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


### 3. Hugging Face Credentials

This application uses Hugging Face services, utilizing the latest open-source model `gpt-oss-120B`.
To use Hugging Face services, you need an access token.  
Create a `.env` file in the project root (or add to your existing `.env`) with the following line:

```
HF_TOKEN=your_huggingface_token
```

You can obtain your access token from your [Hugging Face account settings](https://huggingface.co/settings/tokens).

### 4. Chat UI

The chat interface is built with [Gradio](https://www.gradio.app/).  
When you run the app, a web UI will launch and provide a shareable link for others to access the chat.
