# Bittensor API Service

A high-performance asynchronous API service for querying Tao dividends from the Bittensor blockchain and executing sentiment-based staking operations.

## 🌟 Features

- **FastAPI Endpoints**: Asynchronous API endpoints for Tao dividend queries
- **Caching Layer**: Redis-powered caching for optimized blockchain queries
- **Sentiment Analysis**: Integration with Datura.ai and Chutes.ai for Twitter data analysis
- **Automated Staking**: Background stake/unstake operations driven by sentiment analysis
- **Task Processing**: Celery workers for handling asynchronous operations
- **Data Storage**: MongoDB integration for historical data management
- **Containerization**: Docker support for seamless deployment

## 🛠️ Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher
- Redis
- MongoDB

## 🚀 Getting Started

### Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/marko1010/bittensor-api
   cd bittensor-api
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

3. Update the environment variables in `.env`:
   ```bash
   DATURA_API_KEY=           # Make sure to put the API key in single quotes since it contains a '$' character
   CHUTES_API_KEY=          
   ```

4. Update wallet path volume in docker-compose.yml:
   ```yaml
   volumes:
     - ~/.bittensor/wallets:/app/wallets
   ```
   If necessary, replace the default path `~/.bittensor/wallets` with the actual path to your Bittensor wallets directory on the host machine. This ensures the container can access your wallet files.

5. Launch the containers:
   ```bash
   docker compose up --build
   ```

The service will be accessible at `http://localhost:8000`

### Development Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## 📚 API Documentation

Access the API documentation through:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Authentication

The API requires API key authentication. Include your API key in the request header:
```
Authorization: Bearer your_api_key_here
```

## 🧪 Testing

Run the test suite:
```bash
docker compose --profile test up test
```