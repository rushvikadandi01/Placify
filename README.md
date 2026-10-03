# Placify

> Your AI-powered placement preparation companion.

Placify is an AI-powered placement preparation platform designed to help students prepare for technical and aptitude-based placements through guided practice, interview preparation, progress tracking, and personalized study plans.

## ✨ Features

### 🧠 AI Placement Assistant

- AI-powered placement preparation assistant
- Intent-based routing for different placement areas
- Supports DSA, Aptitude, Interview, Core CS, HR, Project Interview, and Study Planning

### 💻 DSA Practice

Practice Data Structures and Algorithms questions by:

- Topic
- Difficulty
- Practice session

Supported topics include:

- Arrays
- Strings
- HashMap
- HashSet
- Linked List
- Stack
- Queue
- Binary Tree
- BST
- Heap
- Graph
- Recursion
- Sorting
- Searching
- Dynamic Programming

The DSA module also provides AI-powered hints and explanations.

### 🎯 Aptitude Practice

Practice aptitude questions across:

**Quantitative Aptitude**
- Percentages
- Profit & Loss
- Ratio & Proportion
- Averages
- Time & Work
- Time, Speed & Distance
- Simple Interest
- Compound Interest
- Number System

**Logical Reasoning**
- Number Series
- Coding & Decoding
- Blood Relations
- Directions
- Syllogisms
- Seating Arrangement

**Verbal Ability**
- Grammar
- Vocabulary
- Sentence Correction
- Reading Comprehension

Questions are organized by Easy, Medium, and Hard difficulty levels.

### 🎤 Interview Preparation

Placify supports three interview modes:

- Technical
- HR
- Project

Technical interview topics include:

- DSA
- DBMS
- Operating Systems
- Computer Networks
- OOP
- Java
- Python
- AI/ML

Interview evaluation includes:

- Score
- Strengths
- Weaknesses
- Feedback
- Missing points
- Suggested answer
- Communication feedback
- Technical feedback
- Follow-up questions

### 📊 Progress Tracking

Placify stores training progress using SQLite.

The platform tracks:

- Total sessions
- Questions attempted
- Questions answered correctly
- Overall accuracy
- Interview scores
- DSA sessions
- Aptitude sessions
- Interview sessions
- Topic-wise performance

### 📅 Personalized Study Plans

Placify can generate personalized study plans using the student's existing progress.

The study planner considers:

- Strengths
- Weaknesses
- Available study hours
- Number of preparation days
- Selected focus areas
- Placement goals

The generated plan contains daily tasks, topics, activities, durations, and recommendations.

---

## 🛠️ Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Pydantic
- SQLite

### AI

- OpenAI-compatible LLM API
- Modular AI service architecture

### Development

- Git
- GitHub
- Uvicorn
- npm

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      Placify UI      │
                    │     React + Vite     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI API     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       ┌───────────┐     ┌───────────┐     ┌────────────┐
       │ DSA Agent │     │ Aptitude  │     │ Interview  │
       │           │     │   Agent   │     │   Agent    │
       └───────────┘     └───────────┘     └────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │      AI Service      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        SQLite        │
                    │  Progress Tracking   │
                    └──────────────────────┘