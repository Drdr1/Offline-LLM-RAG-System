import os
import httpx
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pypdf
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import uuid

app = FastAPI(title="Offline LLM RAG System")

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3:8b-instruct")
UPLOAD_DIR = Path("/app/uploads")
DATA_DIR = Path("/app/data")
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Initialize embedding model (will download on first run, then cached)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
collection = chroma_client.get_or_create_collection(
    name="pdf_documents",
    metadata={"hnsw:space": "cosine"}
)

class QuestionRequest(BaseModel):
    question: str
    top_k: int = 3

class AnswerResponse(BaseModel):
    answer: str
    citations: List[dict]

def extract_text_from_pdf(pdf_path: Path) -> List[dict]:
    """Extract text from PDF, returning list of page chunks"""
    chunks = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    chunks.append({
                        "text": text,
                        "page": page_num + 1,
                        "source": pdf_path.name
                    })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    return chunks

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the web UI"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline LLM RAG System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 0.95em;
        }
        .section {
            margin-bottom: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        h2 {
            color: #444;
            margin-bottom: 15px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
        }
        h2::before {
            content: "📄";
            margin-right: 10px;
        }
        .section:nth-child(3) h2::before { content: "❓"; }
        input[type="file"] {
            display: block;
            width: 100%;
            padding: 12px;
            border: 2px dashed #667eea;
            border-radius: 6px;
            margin-bottom: 15px;
            background: white;
            cursor: pointer;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
            margin-bottom: 15px;
        }
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-size: 15px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            display: none;
        }
        .result.show { display: block; }
        .answer {
            color: #333;
            line-height: 1.6;
            margin-bottom: 15px;
            white-space: pre-wrap;
        }
        .citations {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }
        .citations h3 {
            color: #555;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .citation {
            background: white;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #666;
            border-left: 3px solid #667eea;
        }
        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            margin-top: 15px;
            font-weight: 600;
        }
        .loading.show { display: block; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status {
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
            display: none;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            display: block;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Offline LLM RAG System</h1>
        <p class="subtitle">Upload PDFs, ask questions, get answers with citations - all running locally!</p>
        
        <div class="section">
            <h2>Upload PDF Documents</h2>
            <input type="file" id="pdfFile" accept=".pdf" multiple>
            <button onclick="uploadPDF()">📤 Upload & Index</button>
            <div id="uploadStatus" class="status"></div>
        </div>

        <div class="section">
            <h2>Ask Questions</h2>
            <textarea id="question" placeholder="Enter your question about the uploaded documents..."></textarea>
            <button onclick="askQuestion()">🔍 Get Answer</button>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                Thinking...
            </div>
            <div class="result" id="result">
                <div class="answer" id="answer"></div>
                <div class="citations" id="citations"></div>
            </div>
        </div>
    </div>

    <script>
        async function uploadPDF() {
            const fileInput = document.getElementById('pdfFile');
            const files = fileInput.files;
            const statusDiv = document.getElementById('uploadStatus');
            
            if (files.length === 0) {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Please select at least one PDF file';
                return;
            }

            for (let file of files) {
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        statusDiv.className = 'status success';
                        statusDiv.textContent = `✓ Successfully indexed: ${file.name} (${data.chunks_added} chunks)`;
                    } else {
                        const error = await response.json();
                        statusDiv.className = 'status error';
                        statusDiv.textContent = `✗ Error: ${error.detail}`;
                    }
                } catch (error) {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = `✗ Upload failed: ${error.message}`;
                }
            }
        }

        async function askQuestion() {
            const question = document.getElementById('question').value.trim();
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const answerDiv = document.getElementById('answer');
            const citationsDiv = document.getElementById('citations');

            if (!question) {
                alert('Please enter a question');
                return;
            }

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });

                if (response.ok) {
                    const data = await response.json();
                    answerDiv.textContent = data.answer;
                    
                    citationsDiv.innerHTML = '<h3>📚 Sources</h3>';
                    data.citations.forEach((cite, idx) => {
                        const citationEl = document.createElement('div');
                        citationEl.className = 'citation';
                        citationEl.innerHTML = `
                            <strong>Source ${idx + 1}:</strong> ${cite.source} (Page ${cite.page})<br>
                            <em>"${cite.text.substring(0, 150)}..."</em>
                        `;
                        citationsDiv.appendChild(citationEl);
                    });

                    result.classList.add('show');
                } else {
                    const error = await response.json();
                    alert(`Error: ${error.detail}`);
                }
            } catch (error) {
                alert(`Request failed: ${error.message}`);
            } finally {
                loading.classList.remove('show');
            }
        }

        // Allow Enter to submit question
        document.getElementById('question').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and index a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # Extract text from PDF
    page_chunks = extract_text_from_pdf(file_path)
    
    # Create smaller chunks for better retrieval
    all_chunks = []
    for page_chunk in page_chunks:
        text_chunks = chunk_text(page_chunk["text"])
        for chunk in text_chunks:
            all_chunks.append({
                "text": chunk,
                "page": page_chunk["page"],
                "source": page_chunk["source"]
            })
    
    # Generate embeddings and store in ChromaDB
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedding_model.encode(texts).tolist()
    
    ids = [str(uuid.uuid4()) for _ in all_chunks]
    metadatas = [{"page": c["page"], "source": c["source"]} for c in all_chunks]
    
    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    return {"message": "PDF indexed successfully", "chunks_added": len(all_chunks)}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an answer with citations"""
    
    # Generate embedding for the question
    question_embedding = embedding_model.encode([request.question]).tolist()[0]
    
    # Retrieve relevant chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=request.top_k
    )
    
    if not results['documents'][0]:
        raise HTTPException(status_code=404, detail="No documents found. Please upload PDFs first.")
    
    # Build context from retrieved chunks
    context_parts = []
    citations = []
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        context_parts.append(f"[Source {i+1}] {doc}")
        citations.append({
            "text": doc,
            "page": metadata['page'],
            "source": metadata['source']
        })
    
    context = "\n\n".join(context_parts)
    
    # Create prompt for LLM
    prompt = f"""Based on the following context from documents, answer the question. If the answer is not in the context, say so.

Context:
{context}

Question: {request.question}

Answer (cite sources using [Source N] notation):"""
    
    # Call Ollama
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            answer = result.get("response", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Ollama: {str(e)}")
    
    return AnswerResponse(answer=answer, citations=citations)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    count = collection.count()
    return {
        "indexed_chunks": count,
        "model": MODEL_NAME,
        "embedding_model": "all-MiniLM-L6-v2"
    }
