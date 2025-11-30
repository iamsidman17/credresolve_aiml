import os
import json
import pandas as pd
import math
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import RAG pipeline
from rag import retrieve_policy

# Set API Key (In a real app, use os.environ)
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" # REMOVED FOR SECURITY

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0)

# Define State
class AgentState(TypedDict):
    scenario_id: str
    borrower_id: str
    loan_type: str
    principal: float
    dpd: int
    chat_history: str
    retrieved_policy: str
    selected_rule: str
    discount_percent: float
    min_offer: int

# --- Nodes ---

def retrieve_node(state: AgentState):
    """
    Retrieves relevant policy clauses.
    """
    query = f"{state['loan_type']} DPD {state['dpd']} {state['chat_history']}"
    policy_text = retrieve_policy(query)
    return {"retrieved_policy": policy_text}

def reason_node(state: AgentState):
    """
    Uses LLM to select the correct rule and discount percentage.
    """
    prompt = ChatPromptTemplate.from_template("""
    You are a Settlement Officer at CredResolve.
    Your goal is to strictly apply the Settlement Policy to determine the maximum discount percentage.

    **Borrower Details:**
    - Loan Type: {loan_type}
    - Principal: {principal}
    - DPD: {dpd}
    - Chat History: "{chat_history}"

    **Relevant Policy Clauses:**
    {retrieved_policy}

    **Instructions:**
    1. Analyze the borrower's situation against the policy clauses.
    2. Identify the specific rule that applies (e.g., "Job Loss", "Medical Emergency", "DPD > 90", "Small Balance", "Standard").
    3. Determine the maximum discount percentage (0.0 to 1.0) allowed by that rule.
    4. IMPORTANT: 
       - "Job Loss" rule applies ONLY if Loan Type is "Personal Loan" AND borrower mentions "Job Loss", "Unemployment", or "lost my job".
       - "Medical" rule applies ONLY if Loan Type is "Personal Loan" AND borrower mentions "Hospital" or "Medical".
       - "Small Balance" rule for Credit Cards (< 50k) overrides DPD rules.
       - "High Delinquency" applies if DPD > 90.
       - Otherwise, use "Standard Case".

    Output ONLY a JSON object with the following keys:
    - "rule_name": The name of the rule applied.
    - "discount_percent": The discount percentage as a float (e.g., 0.50 for 50%).
    """)
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({
            "loan_type": state["loan_type"],
            "principal": state["principal"],
            "dpd": state["dpd"],
            "chat_history": state["chat_history"],
            "retrieved_policy": state["retrieved_policy"]
        })
        
        # Clean response to ensure valid JSON
        response = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(response)
        
        return {
            "selected_rule": data.get("rule_name", "Unknown"),
            "discount_percent": float(data.get("discount_percent", 0.0))
        }
    except Exception as e:
        print(f"Error in reasoning for {state['scenario_id']}: {e}")
        # Fallback to safe default (Standard Case)
        return {"selected_rule": "Error Fallback", "discount_percent": 0.20}

def calculate_node(state: AgentState):
    """
    Calculates the strictly allowable counter-offer.
    """
    principal = state["principal"]
    discount = state["discount_percent"]
    
    max_discount_amount = principal * discount
    min_offer = principal - max_discount_amount
    
    # Round to nearest 100
    rounded_offer = round(min_offer / 100) * 100
    
    return {"min_offer": int(rounded_offer)}

# --- Graph Definition ---

workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("reason", reason_node)
workflow.add_node("calculate", calculate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "reason")
workflow.add_edge("reason", "calculate")
workflow.add_edge("calculate", END)

app = workflow.compile()

# --- Execution ---

def run_agent():
    print("Loading data...")
    borrower_df = pd.read_csv('data/borrower_data.csv')
    borrower_dict = borrower_df.set_index('borrower_id').to_dict('index')
    
    with open('data/chat_scenarios.json', 'r') as f:
        scenarios = json.load(f)
        
    results = []
    
    print("Running LangGraph Agent on scenarios...")
    # For demonstration/speed, let's run on all 1000. 
    # If it's too slow, we might need to batch or parallelize, but sequential is safer for rate limits.
    
    for i, scenario in enumerate(scenarios):
        if i % 50 == 0:
            print(f"Processing {i}/{len(scenarios)}...")
            
        borrower_id = scenario['borrower_id']
        borrower = borrower_dict.get(borrower_id)
        
        # Combine user messages
        user_text = " ".join([msg['content'] for msg in scenario['chat_history'] if msg['role'] == 'user'])
        
        initial_state = {
            "scenario_id": scenario['scenario_id'],
            "borrower_id": borrower_id,
            "loan_type": borrower['loan_type'],
            "principal": borrower['principal_outstanding'],
            "dpd": borrower['dpd'],
            "chat_history": user_text,
            "retrieved_policy": "",
            "selected_rule": "",
            "discount_percent": 0.0,
            "min_offer": 0
        }
        
        try:
            final_state = app.invoke(initial_state)
            results.append({
                "scenario_id": final_state["scenario_id"],
                "min_acceptable_offer": final_state["min_offer"]
            })
        except Exception as e:
            print(f"Failed to process {scenario['scenario_id']}: {e}")
            results.append({
                "scenario_id": scenario['scenario_id'],
                "min_acceptable_offer": 0 # Should ideally handle better
            })
            
    # Save results
    submission_df = pd.DataFrame(results)
    submission_df.to_csv('submission_agent.csv', index=False)
    print(f"Saved agent results to submission_agent.csv")

if __name__ == "__main__":
    run_agent()
