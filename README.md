# gurbani-insight
A chatbot trained on the english transliteration of The Guru Granth Sahib Ji: Query the divine knowledge
# Gurbani Insight

![Gurbani Insight Logo](https://via.placeholder.com/150x150.png?text=GI)

A semantic search application for discovering wisdom from the Guru Granth Sahib using natural language queries.

## Overview

Gurbani Insight allows users to ask questions in natural language and receive relevant insights from the Guru Granth Sahib. The application uses:

- **Vector Embeddings** to understand the semantic meaning of both queries and scripture texts
- **ChromaDB** as a lightweight vector database for efficient similarity search
- **Ollama** for local embeddings and optional LLM-enhanced responses
- **FastAPI** for a responsive web API

## Features

- 💬 **Natural Language Search**: Ask questions in everyday language
- 🔍 **Semantic Understanding**: Search by meaning, not just keywords
- 📊 **Relevant Results**: Get the most relevant passages based on your query
- 🧠 **Enhanced Responses**: Generate coherent answers that directly address your questions (when LLM is available)
- 🌐 **Web Interface**: Clean, responsive interface for easy interaction

## Screenshots

![Search Interface](https://via.placeholder.com/800x400.png?text=Search+Interface)
![Results Example](https://via.placeholder.com/800x400.png?text=Results+Example)

## Getting Started

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) for embeddings and LLM capabilities

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gurbani-insight.git
cd gurbani-insight
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

3. Download the data:
   - Follow the instructions in the [data/README.md](data/README.md) file to obtain the Guru Granth Sahib PDF

4. Process the data:
```bash
python -m app.process_data
```

5. Start the application:
```bash
python -m app.main
```

6. Open your browser and navigate to:
```
http://localhost:8001
```

### Using Docker

You can also run the application using Docker:

```bash
docker-compose up -d
```

This will start both the application and Ollama in containers.

## API Endpoints

The service provides several API endpoints:

- `GET /`: Web interface for searching the Guru Granth Sahib
- `POST /v1/chat/completions`: OpenAI-compatible chat completion API
- `POST /api/search`: Direct search endpoint for custom integrations
- `GET /health`: Health check endpoint

### Chat Completions API

The primary endpoint follows the OpenAI Chat Completions API format:

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What does Guru Granth Sahib teach about meditation?"}
    ],
    "model": "gurbani-search",
    "top_k": 10
  }'
```

## Deployment

### Deploying to Render

1. Fork this repository to your GitHub account
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variables: 
     - `OLLAMA_API_URL`: URL to your Ollama instance
     - `EMBEDDING_MODEL`: Name of your embedding model (default: `nomic-embed-text`)

### Deploying to Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add the Ollama plugin to your project
4. Configure environment variables in Railway dashboard
5. Deploy your application

### Deploying to Fly.io

1. Install the flyctl CLI
2. Run `fly launch` in your project directory
3. Configure your fly.toml file
4. Deploy with `fly deploy`

## How It Works

Gurbani Insight works by:

1. **Data Processing**: The Guru Granth Sahib text is processed into semantic chunks
2. **Vector Embedding**: Each chunk is converted to a vector embedding that captures its meaning
3. **Vector Storage**: These embeddings are stored in ChromaDB for efficient retrieval
4. **Query Processing**: User queries are also converted to vector embeddings
5. **Semantic Search**: The system finds the most semantically similar passages to the query
6. **Response Generation**: When available, an LLM synthesizes a direct answer based on the retrieved passages

## Project Structure

```
gurbani-insight/
├── app/               # Application code
│   ├── __init__.py    # Package initialization
│   ├── main.py        # FastAPI application
│   ├── config.py      # Configuration settings
│   ├── models.py      # Data models
│   ├── process_data.py # Data processing script
│   └── utils/         # Utility functions
│       ├── embedding.py  # Embedding utilities
│       ├── search.py     # Search functions
│       └── response.py   # Response formatting
├── data/              # Data directory (PDF and processed CSV)
├── static/            # Static web files
│   └── index.html     # Web interface
├── .env.example       # Example environment variables
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container definition
└── docker-compose.yml # Container orchestration
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Guru Granth Sahib English translations
- The Ollama project for providing local LLM capabilities
- ChromaDB for the vector database
- FastAPI for the web framework

## Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - email@example.com

Project Link: [https://github.com/yourusername/gurbani-insight](https://github.com/yourusername/gurbani-insight)
>>>>>>> 0173953 (Initial commit - Gurbani Insight)
