import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Initialize embeddings (using local model to avoid API costs for this part)
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Global vector store variable
vectorstore = None

def initialize_rag():
    """
    Indexes the settlement policy into a Chroma vector store.
    """
    global vectorstore
    
    print("Initializing RAG pipeline...")
    
    # Load policy
    policy_path = "data/settlement_policy.md"
    with open(policy_path, "r") as f:
        policy_text = f.read()
        
    # Split by headers to keep context together
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    docs = markdown_splitter.split_text(policy_text)
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embedding_function,
        collection_name="settlement_policy",
        persist_directory="./chroma_db" # Optional: persist to disk
    )
    print("RAG pipeline initialized.")

def retrieve_policy(query, k=2):
    """
    Retrieves relevant policy clauses based on the query.
    """
    global vectorstore
    if vectorstore is None:
        initialize_rag()
        
    results = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in results])

if __name__ == "__main__":
    # Test the pipeline
    initialize_rag()
    
    test_query = "Personal Loan with Job Loss"
    print(f"\nQuery: {test_query}")
    print(f"Result:\n{retrieve_policy(test_query)}")
    
    test_query = "Credit Card DPD > 90"
    print(f"\nQuery: {test_query}")
    print(f"Result:\n{retrieve_policy(test_query)}")
