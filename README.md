# CredResolve Settlement Agent

## Overview
This project implements a **LangGraph-based Settlement Agent** for CredResolve. The agent functions as a virtual Settlement Officer, negotiating debt settlements with borrowers based on a strict policy.

## Problem Statement
(From `problem.txt`)

### 1. Business Problem
CredResolve has thousands of borrowers who want to settle their debts but cannot pay the full amount. We have a complex Settlement Policy that dictates how much discount we can offer based on:
- Risk
- DPD (Days Past Due)
- Loan Type

Human agents struggle to memorize these rules, leading to revenue loss or failed recoveries.

### 2. Challenge
Build a LangGraph-based Settlement Agent that:
1.  Reads the borrower conversation from Live Chat.
2.  Performs **RAG** to retrieve the correct policy clause.
3.  Calculates the **Strictly Optimal Counter-Offer**.
4.  Generates the appropriate response.

### 3. Solution Approach
The solution uses a **LangGraph** workflow with the following nodes:
-   **Retrieve**: Uses a RAG pipeline (ChromaDB + SentenceTransformers) to fetch relevant policy clauses from `data/settlement_policy.md`.
-   **Reason**: Uses **Google Gemini 2.0 Flash Lite** to analyze the borrower's situation and select the applicable rule (e.g., "Job Loss", "Medical Emergency").
-   **Calculate**: Deterministically calculates the minimum acceptable offer based on the selected rule's discount percentage.

## Setup & Usage

### Prerequisites
-   Python 3.10+
-   Google Gemini API Key

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/iamsidman17/credresolve_aiml.git
    cd credresolve_aiml
    ```
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Agent
1.  Set your API key:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```
2.  Run the agent:
    ```bash
    python3 agent.py
    ```
3.  The results will be saved to `submission_agent.csv`.

## Files
-   `agent.py`: Main LangGraph agent implementation.
-   `rag.py`: RAG pipeline for policy retrieval.
-   `solve.py`: Deterministic script (baseline).
-   `data/`: Contains dataset and policy.
