App to train for danish citizenship

## Python Environment

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Setup

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already.
2. Install dependencies:
   ```bash
   poetry install
   ```

### Running Scripts

You can run the extraction scripts using `poetry run`:

```bash
poetry run python src/extraction/extract_ch1.py
```

### Question Generation

The project includes an AI-powered Generator-Critic system to create and verify citizenship test questions from study material.

To generate new questions from Chapter 1 and append them to `app/data/output_generated_questions.json`:

1.  Ensure you have a `GOOGLE_API_KEY` in your `.env` file.
2.  Run the script:
    ```bash
    poetry run python src/generate_questions.py
    ```

The script will automatically detect existing questions and continue numbering from the last one.

## Web Application

The frontend is a React application built with Vite.

### Setup

1. Navigate to the app directory:
   ```bash
   cd app
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

### Running Locally

To start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`. It combines questions from the official test data and the AI-generated questions.
