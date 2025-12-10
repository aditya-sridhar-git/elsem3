# Quick test to verify LLM is working
from config import CFG, HAS_LANGCHAIN, llm

print(f"LangChain enabled: {CFG.enable_langchain}")
print(f"Has LangChain: {HAS_LANGCHAIN}")
print(f"LLM model: {CFG.llm_model}")

if HAS_LANGCHAIN and llm:
    print("\nTesting LLM...")
    try:
        response = llm.invoke("What is 2+2? Answer in one sentence.")
        print(f"LLM Response: {response.content}")
        print("\n✅ LLM is working!")
    except Exception as e:
        print(f"❌ LLM Error: {str(e)}")
else:
    print("❌ LangChain not properly initialized")
