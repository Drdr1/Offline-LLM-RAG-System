# Offline-LLM-RAG-System

A complete, portable, offline LLM system with RAG capabilities for PDF documents. Runs entirely on Ubuntu 24.04, ships via USB, and requires no internet connection after installation.

##  Features

- ** 100% Offline**: No internet required after setup
- ** PDF Processing**: Upload and index PDF documents
- ** Q&A with Citations**: Ask questions and get answers with source references
- ** Simple Web UI**: Clean, intuitive interface
- ** Docker-based**: Containerized and portable
- ** USB Shippable**: Complete system fits on 64GB USB drive
- ** Local Processing**: Everything runs on your hardware


##  Requirements

### Hardware
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 50GB free space
- **USB**: 64GB+ for shipping

### Software
- Ubuntu 24.04 LTS
- Docker & Docker Compose

##  Quick Start

### Option 1: Fresh Setup with Internet

```bash
# Clone or copy project files
cd offline-llm

# Run setup (downloads models, builds images)
./setup.sh

# Copy usb-package/ to USB drive
```

### Option 2: Install from USB (Offline)

```bash
# 1. Install Ubuntu 24.04
# 2. Insert USB with package
# 3. Run installation

sudo ./install.sh

# 4. Open browser
# http://localhost:8000
```

##  What's Included

```
 Total: ~8-10GB
├──  Docker Images (3.5GB)
│   ├── Ollama
│   └── RAG API
├──  LLaMA 3 Model (4.7GB)
├──  System Packages (100MB)
└──  Application Code (10MB)
```

##  System Architecture

```
Browser (localhost:8000)
    ↓
FastAPI + RAG Service
    ├── PDF Processing
    ├── Text Embeddings
    ├── Vector Database (ChromaDB)
    └── Question Answering
    ↓
Ollama (LLaMA 3 8B)
    └── Answer Generation
```


##  Basic Usage

### 1. Upload PDFs
```
1. Open http://localhost:8000
2. Click file input
3. Select PDF(s)
4. Click "Upload & Index"
```

### 2. Ask Questions
```
1. Type your question
2. Click "Get Answer"
3. View answer with citations
```

### 3. Manage System
```bash
# Start/stop
sudo systemctl start offline-llm
sudo systemctl stop offline-llm

# View logs
docker logs rag-api

# Check status
docker ps
```

##  Screenshots

### Web Interface
- Clean, modern design
- Upload multiple PDFs
- Real-time processing status
- Answer with citations
- Source page references

## Performance

| Task | Time |
|------|------|
| PDF Upload (10 pages) | 5-10 sec |
| PDF Upload (100 pages) | 30-60 sec |
| Question Answer | 10-30 sec |

*On 4-core CPU, 16GB RAM*

## Key Features

### RAG Pipeline
- Automatic text chunking
- Semantic search
- Context-aware generation
- Source citation

### Vector Database
- ChromaDB for embeddings
- Cosine similarity search
- Persistent storage
- Fast retrieval

### LLM Processing
- LLaMA 3 8B Instruct
- 4-bit quantization
- ~8K context window
- CPU-optimized

##  Troubleshooting

### Common Issues

**Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Service won't start:**
```bash
sudo systemctl start docker
sudo systemctl restart offline-llm
```


##  Project Structure

```
offline-llm/
├── docker-compose.yml          # Docker orchestration
├── setup.sh                    # Setup script (with internet)
├── install.sh                  # Install script (offline)
├── rag-service/
│   ├── Dockerfile              # RAG service container
│   ├── main.py                 # FastAPI application
│   └── requirements.txt        # Python dependencies
├── INSTALLATION.md             # Detailed installation guide
├── QUICKSTART.md              # Quick reference
└── ARCHITECTURE.md            # Technical documentation
```

##  Advanced Configuration

### Change LLM Model
Edit `docker-compose.yml`:
```yaml
environment:
  - MODEL_NAME=mistral:7b-instruct
```

### Change Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Change to 8080
```

### Adjust Chunking
Edit `rag-service/main.py`:
```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
```

##  System Management

### Systemd Commands
```bash
sudo systemctl start offline-llm    # Start
sudo systemctl stop offline-llm     # Stop
sudo systemctl restart offline-llm  # Restart
sudo systemctl status offline-llm   # Status
```

### Docker Commands
```bash
docker ps                           # Running containers
docker logs rag-api                 # View logs
docker-compose down                 # Stop all
docker-compose up -d                # Start all
```

### Data Management
```bash
# Clear indexed data
sudo systemctl stop offline-llm
sudo rm -rf /opt/offline-llm/data/*
sudo systemctl start offline-llm

# Backup data
tar -czf backup.tar.gz /opt/offline-llm/data/
```


##  Contributing

This is a self-contained offline system. To modify:

1. Edit source files in `rag-service/`
2. Rebuild: `docker-compose build`
3. Restart: `sudo systemctl restart offline-llm`

