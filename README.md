# Japanese Learning Assistant (Streamlit)

A simple Python app to review Japanese lessons from your Google Doc.

## Setup

1.  **Install Requirements**:
    ```bash
    pip install streamlit openai requests
    ```

2.  **Run the App**:
    ```bash
    streamlit run streamlit_app.py
    ```

## Usage

1.  Enter your **OpenAI API Key** in the sidebar.
2.  (Optional) Change the Google Doc URL if needed.
3.  Select a **Month** and **Lesson** from the dropdowns.
4.  Click **Start Daily Quiz** to generate questions.

## Features

- **Auto-Parsing**: Reads dates `@ MM-DD` from the doc.
- **AI Quizzes**: Generates questions using GPT-3.5.
- **Session State**: Keeps track of your quiz progress without page reloads.
