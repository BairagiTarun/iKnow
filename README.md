<<<<<<< HEAD
# NOTEGPT - README

## 📋 Project Overview
**NOTEGPT** is a Django-based intelligent note management system powered by advanced AI capabilities for semantic search, question-answering, entity recognition, and natural language processing. It leverages cutting-edge models like `Sentence-BERT`, `DistilBERT`, and `RoBERTa` to provide users with highly accurate responses and relevant notes based on their queries. Additionally, NOTEGPT integrates Gemini AI for generating insightful content, offering a powerful chat interface for efficient information retrieval.

---

## 🚀 Features
- **Semantic Search**: Retrieve the most relevant notes using `Sentence-BERT` embeddings and cosine similarity.
- **Question-Answering**: Uses `DistilBERT` and `RoBERTa` models to answer user queries based on note content.
- **Named Entity Recognition (NER)**: Extracts key entities using a pre-trained `BERT` model.
- **Gemini AI Integration**: Provides AI-generated content using Gemini API.
- **Chat Interface**: Interactive chat system for seamless querying and response.
- **Tag Extraction**: Extracts top tags from notes using TF-IDF for efficient categorization.
- **File Storage**: Option to save notes to a file system with timestamped filenames.

---

## 🛠️ Tech Stack
- **Backend**: Django, Python, REST API
- **AI Models**: 
  - `Sentence-BERT` (`all-MiniLM-L6-v2`) for semantic search
  - `DistilBERT` and `RoBERTa` for question answering
  - `BERT` for named entity recognition
  - Gemini API for generative AI responses
- **Data Science**: `sklearn`, `sentence-transformers`, `transformers`, `torch`
- **Database**: MySQL (can be configured to other relational databases)
- **Environment Management**: Python `dotenv` for environment variables

---

## 📂 Folder Structure
```
NOTEGPT/
├── notes/
│   ├── templates/
│   │   └── chat_interface.html
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── forms.py
│   ├── utils.py
│   ├── tests.py
├── manage.py
├── requirements.txt
├── README.md
├── .env
└── settings.py
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- MySQL or other supported relational database
- [Gemini API Key](https://gemini.com/api) for generative AI integration

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/NOTEGPT.git
cd NOTEGPT
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory and add your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=mysql://username:password@localhost:3306/notegpt_db
```

### 5. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Load Existing Notes (Optional)
```python
python manage.py shell
from notes.views import load_existing_notes
load_existing_notes()
```

### 7. Run the Django Server
```bash
python manage.py runserver
```
Visit `http://localhost:8000` in your browser.

---

## 🧪 Usage Guide

### Chat Interface
- Navigate to `/chat-interface/` to interact with the AI-powered chat system.
- Type in your query, and the system will fetch relevant notes or generate answers using Gemini AI.

### Saving Notes
- Use the `/save-note/` endpoint to add new notes:
```bash
curl -X POST http://localhost:8000/save-note/ -d "message=Your Note Here"
```

### Searching Notes
- Use the `/search-notes/` endpoint to perform semantic searches:
```bash
curl -X POST http://localhost:8000/search-notes/ -d "message=Your Search Query"
```

---

## 📄 API Endpoints

### 1. **Save Note**
- **URL**: `/save-note/`
- **Method**: `POST`
- **Data**: `message` (text content)
- **Response**: `{ "response": "Note saved successfully." }`

### 2. **Search Notes**
- **URL**: `/search-notes/`
- **Method**: `POST`
- **Data**: `message` (query string)
- **Response**: `{ "response": "Relevant answer or notes content." }`

### 3. **Query Gemini**
- **URL**: `/query-gemini/`
- **Method**: `POST`
- **Data**: `message` (query string)
- **Response**: `{ "response": "Generated content from Gemini AI." }`

---

## 🛡️ Security Considerations
- Ensure sensitive keys like `GEMINI_API_KEY` are stored securely in the `.env` file.
- Django's CSRF protection is enabled for sensitive endpoints.

---

## 📊 Future Improvements
- **Authentication**: Adding user authentication to secure notes.
- **Enhanced NER**: Using advanced models for better entity extraction.
- **UI Enhancements**: Improving the frontend with a modern, responsive design.
- **Integration with Cloud Storage**: Option to save notes to cloud platforms like AWS S3.

---

## 🤝 Contributions
Contributions are welcome! Please submit a pull request or open an issue on GitHub if you have suggestions or find bugs.

---

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## 📞 Contact
For any inquiries or support, please reach out to [tarun@example.com](mailto:bairagitarun06@gmail.com).

---

## 🌟 Acknowledgements
- [Google Generative AI](https://developers.google.com/ai)
- [Sentence-Transformers](https://www.sbert.net/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [Gemini API](https://gemini.com/api)

---

Feel free to customize this template as needed for your project!
=======
# iKnow
>>>>>>> 3359b283a4c4eb6e3cdaaa3d2e09861a37f2194b
