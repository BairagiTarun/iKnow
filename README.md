# KMSimba Knowledge Management System


KMSimba is an advanced **Knowledge Management System (KMS)** designed to store, organize, and retrieve unstructured data such as text notes, documents, and images. It leverages cutting-edge technologies like **Natural Language Processing (NLP)**, **Machine Learning (ML)**, and **semantic search** to provide an intelligent and user-friendly platform for managing knowledge.

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Technologies Used](#technologies-used)
4. [Installation](#installation)
5. [Usage](#usage)
6. [File Structure](#file-structure)
7. [Future Enhancements](#future-enhancements)
8. [Contributing](#contributing)
9. [License](#license)
10. [Contact](#contact)

---

## Overview

KMSimba addresses the challenges of managing unstructured data by providing:
- A **chat-based interface** for saving and searching notes.
- A **file upload system** that processes PDFs, Word documents, and images.
- **Automated tagging** for efficient organization and retrieval.
- **Deduplication** to prevent redundant uploads.
- **Scalable architecture** built on Django and SQLite.

It is ideal for students, professionals, researchers, and personal users seeking a unified platform for knowledge management.

---

## Features

### Chat-Based Interface
- **Save Mode**: Save notes via the chat interface.
- **Search Mode**: Perform semantic searches and get precise answers using DistilBERT.

### File Upload and Processing
- Extract text from **PDFs**, **Word documents**, and **images**.
- Detect objects in images using **YOLO**.
- Perform OCR on images using **Tesseract**.

### Automated Tagging
- Automatically generate tags using **spaCy NLP**.
- Perform tag-based searches for faster retrieval.

### Semantic Search
- Use **TF-IDF vectorization** and **cosine similarity** for context-aware search results.

### File Management
- Rename, download, and delete uploaded files seamlessly.
- Prevent duplicate uploads using **SHA-256 hashing**.

---

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript/jQuery, AJAX
- **Backend**: Django Framework, Python
- **Database**: SQLite
- **AI/ML**:
  - Transformers (Hugging Face): DistilBERT for question-answering.
  - YOLO: Object detection in images.
  - spaCy: Keyword extraction and tagging.
  - Tesseract OCR: Text extraction from images.
- **File Processing**:
  - pdfplumber: Extract text from PDFs.
  - textract: Process `.doc` files.
  - docx2txt: Extract text from `.docx` files.
  - PyMuPDF (fitz): Extract images from PDFs.
  - Pillow (PIL): Image processing.

---

## Installation

### Prerequisites
1. **Python 3.8 or higher**
2. **Tesseract OCR** (for Windows users):
   - Download and install Tesseract from [here](https://github.com/tesseract-ocr/tesseract).
   - Update the `pytesseract.pytesseract.tesseract_cmd` path in the code if necessary.
3. **Django**: Install Django using `pip install django`.

### Steps to Run the Project
1. Clone the repository:
   ```bash
   git clone https://github.com/BairagiTarun/iKnow.git
   ```
2. Navigate to the project directory:
   ```bash
   cd <project_directory>
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```
6. Access the application at `http://127.0.0.1:8000/`.

---

## Usage

### Chat Interface
1. Navigate to the **Chat Interface** (`/`).
2. Toggle between **Save Mode** and **Search Mode** using the toggle button.
3. In **Save Mode**, type your note and press "Save."
4. In **Search Mode**, ask questions and receive context-aware answers.

### File Upload and Search
1. Navigate to the **Upload Interface** (`/upload/`).
2. Upload files (PDFs, DOCX, images).
3. Enter keywords in the search bar to find files based on tags.

---

## File Structure

```
KMSimba/
├── README.md                # Project documentation
├── requirements.txt         # List of dependencies
├── manage.py                # Django management script
├── notes/                   # Main app directory
│   ├── models.py            # Database models (Note, File, Tag, FileTag)
│   ├── views.py             # Backend logic for handling requests
│   ├── urls.py              # URL routing
│   ├── forms.py             # Forms for file upload and search
│   ├── utils.py             # Utility functions for file processing, tagging, etc.
│   ├── static/              # Static files (CSS, JS)
│   │   ├── notes/
│   │       ├── styles.css   # Styles for the chat interface
│   │       ├── upload.css   # Styles for the upload interface
│   ├── templates/           # HTML templates
│       ├── chat_interface.html  # Chat-based interface
│       ├── upload.html          # File upload and search interface
└── kmsimba/                 # Django project directory
    ├── settings.py          # Django settings
    ├── urls.py              # Root URL configuration
```

---

## Future Enhancements

1. **Cloud Integration**: Store files on AWS S3 or Google Drive for scalability.
2. **Advanced NLP Features**: Add summarization and translation capabilities.
3. **Mobile App Development**: Extend accessibility to smartphones.
4. **Collaboration Tools**: Enable team collaboration with shared notes and files.

---

## Contributing

We welcome contributions to enhance KMSimba! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeatureName`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeatureName`).
5. Open a pull request.

---

## License

This project is licensed under the **MIT License**.

---

## Contact

For any queries or feedback, please contact:

- Email: [imtarunbairagi@gmail.com]
- GitHub: [@BairagiTarun]

Thank you for using **KMSimba**!

---