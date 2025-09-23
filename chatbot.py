import os
import json
import getpass
from PIL import Image
import gradio as gr

# Run instructions:
# - Ensure you have an OpenAI API key in the OPENAI_API_KEY env var. If not set, the script
#   will prompt for it on startup.
# - This script expects a Chroma vector DB at ./chroma_db (created by the project's
#   notebooks). If the DB is missing, the bot will fall back to LLM-only answers.
# - Dependencies: langchain, chromadb, openai, gradio, pillow. Install with pip if needed.

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


# Ensure OPENAI_API_KEY is set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


# David Goggins style RAG prompt
RAG_TEMPLATE = """
You are channeling the mindset and voice of David Goggins
Answer the user's question using ONLY the provided context, even if it's vague — really try to find the answer in the context. 
If the context doesn't contain the answer, respond with: "I don't know based on the provided context."

Guidelines:
- Speak with curse words, intensity, discipline, and raw motivation.
- Keep it concise, direct, and no-nonsense.
- Push the reader to take ownership, embrace discomfort, and stay hard.
- Never invent facts — stay grounded in the context provided.

Chat history:
{chat_history}

Context:
{context}

Question:
{question}

Answer in the Goggins style:
"""



# Try to load the existing Chroma DB; if unavailable, fall back to LLM-only answers
def get_retriever(k: int = 4):
    try:
        embeddings = OpenAIEmbeddings()
        vectordb = Chroma(
            collection_name="podcast-transcripts",
            embedding_function=embeddings,
            persist_directory="./chroma_db",
        )
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        print("Warning: failed to load Chroma DB; continuing without retrieval.", e)
        return None


def analyze_image(image_path):
    """Very small image summary: returns basic metadata and OCR-like text if possible.
    This is optional and lightweight — if PIL can open the image we attach its size info.
    """
    if not image_path:
        return None
    try:
        with Image.open(image_path) as im:
            return {"width": im.width, "height": im.height, "mode": im.mode}
    except Exception as e:
        print("Failed to open image:", e)
        return None


def build_qa_chain():
    retriever = get_retriever()
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"   # ensures memory saves only the answer
    )

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,  # keep sources
        combine_docs_chain_kwargs={
            "prompt": PromptTemplate(
                input_variables=["context", "question", "chat_history"],
                template=RAG_TEMPLATE
            )
        }
    )
    return qa



qa_chain = build_qa_chain()


def respond(message, image, history):
    """Respond to user input. If a Chroma retriever is available, sources will be returned too.
    Yields incremental bot responses to stream into the Gradio chat UI.
    """
    if message is None:
        message = ""

    # attach a short image summary into the question if available
    img_meta = analyze_image(image)
    question = message
    if img_meta:
        question = f"[ImageMeta: {json.dumps(img_meta)}]\n" + question

    try:
        # use modern invoke API instead of calling the chain directly
        result = qa_chain.invoke({"question": question})
    except Exception as e:
        # surface the error and return a helpful message to the user
        print("QA chain failed:", e)
        err_msg = (
            "Sorry — an internal error occurred while generating the answer."
            f"\nError: {e}"
        )
        history = history + [(message if message else "[Image]", err_msg)]
        yield history
        return

    answer_text = result.get("answer") if isinstance(result, dict) else str(result)
    sources = result.get("source_documents") if isinstance(result, dict) else None

    display = answer_text
    if sources:
        display += "\n\nSources:\n"
        for doc in sources:
            meta = getattr(doc, "metadata", {})
            snippet = getattr(doc, "page_content", "")[:400]
            display += f"- {meta} -- {snippet}...\n"

    history = history + [(message if message else "[Image]", display)]
    yield history


# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## David Goggins RAG Bot (podcast transcripts)")
    chatbot = gr.Chatbot()
    with gr.Row():
        msg = gr.Textbox(placeholder="Ask me something...", lines=2)
        img = gr.Image(type="filepath", label="Optional image")
    submit = gr.Button("Send")
    clear = gr.Button("Clear Chat")

    # analyze image silently (we don't store JSON memory like original)
    img.upload(lambda p: None, [img], None)

    submit.click(respond, [msg, img, chatbot], [chatbot])
    msg.submit(respond, [msg, img, chatbot], [chatbot])
    clear.click(lambda: [], None, chatbot)


if __name__ == "__main__":
    demo.launch(inbrowser=True)