### 🐘 PostgreSQL Query Client UI 🚀
This application provides a simple, dedicated User Interface (UI) for interacting with your PostgreSQL databases. It allows you to execute SQL queries and instantly visualizes the returned data in a clear, structured table format.

####⚙️ Quick Setup & Execution
The application runs on port 9998 and is designed for easy deployment, including local execution via Docker Compose.

#### Environment Configuration
The application requires only one environment variable to function:

`CONNECTION_STRING`: This variable must contain the full connection URI for your PostgreSQL instance.

Example Format: `postgresql://username:password@host:port/databasename`

#### 🐳 Run Locally with Docker Compose
You can easily get this running on your local machine using Docker Compose, which handles the environment variables and port exposure for you:

```bash

docker-compose up -d
```

Once running, access the UI in your browser at: http://localhost:9998

#### ✨ Key Features
Query Execution: Send any valid PostgreSQL query directly to the database.

Structured Output: Results are returned and displayed neatly in an interactive table.

TLS-Ready: Built to securely connect using the standard PostgreSQL URI format.

#### Glimpse
<img width="1912" height="932" alt="image" src="https://github.com/user-attachments/assets/c5ff4824-2b08-4c78-885c-f68c27a11533" />

