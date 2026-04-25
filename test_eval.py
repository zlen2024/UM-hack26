import asyncio
from agents.cs_agent import evaluate_kg_trigger

print("Empty string:", evaluate_kg_trigger(""))
print("Ayam:", evaluate_kg_trigger("i love ayam"))
