from workflow import graph

def run_test():
    print("--- Test 1: Greeting ---")
    result1 = graph.invoke({"user_input": "Hello, how are you?"})
    print(f"Gatekeeper Response: {result1.get('gatekeeper_response')}")
    print(f"Manager Response: {result1.get('manager_response')}")
    print()

    print("--- Test 2: Normal Order ---")
    result2 = graph.invoke({"user_input": "Can you check my order #123?"})
    print(f"Gatekeeper Response: {result2.get('gatekeeper_response')}")
    print(f"Manager Response: {result2.get('manager_response')}")
    print(f"Worker Error: {result2.get('worker_error')}")
    print()

    print("--- Test 3: Failed Order ---")
    result3 = graph.invoke({"user_input": "Can you check my order #123? It might fail."})
    print(f"Gatekeeper Response: {result3.get('gatekeeper_response')}")
    print(f"Manager Response: {result3.get('manager_response')}")
    print(f"Worker Error: {result3.get('worker_error')}")
    print()

if __name__ == "__main__":
    run_test()
