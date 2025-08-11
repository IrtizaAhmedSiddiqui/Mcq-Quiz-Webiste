# MCQ Quiz Application

A comprehensive Multiple Choice Question (MCQ) quiz application built with Streamlit that allows users to:

- Upload Excel files containing MCQ questions
- Take full quizzes or random question sets
- Mark important questions for focused practice
- Track performance and view detailed results
- Search and navigate through questions easily

## Features

- **File Upload**: Support for Excel files (.xlsx, .xls, .xlsm)
- **Quiz Types**: Full quiz or random question selection
- **Question Marking**: Mark important questions for later review
- **Progress Tracking**: Real-time score and progress monitoring
- **Detailed Results**: Comprehensive performance analysis with grading
- **Responsive Design**: Wide layout with sidebar navigation

## File Format

The application expects Excel files with the following structure:

- Column 1: Question/Choice identifiers (Question, A, B, C, D)
- Column 2: Question text or choice text
- Column 4: Correct answer indicator

## Local Development

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run quiz.py
   ```

## Deployment

This application is ready for deployment on Streamlit Community Cloud. Simply connect your GitHub repository and deploy!

## Requirements

- Python 3.8+
- Streamlit 1.28.0+
- pandas 1.5.0+
- openpyxl 3.0.0+
- streamlit-option-menu 0.3.0+
