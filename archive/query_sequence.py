import requests

def ask_local_node(prompt):
    # This is the local RPC endpoint for Ollama
    url = "http://localhost:11434/api/generate"
    
    # The raw payload we are sending to the model
    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False # Tells the server to send the whole answer at once
    }
    
    print("Transmitting to local AI node...")
    
    # Send the POST request
    response = requests.post(url, json=payload)
    
    # Extract the text from the JSON response
    result = response.json()
    return result["response"]

if __name__ == "__main__":
    my_question = "Explain the concept of a cryptographic hash function in one simple sentence."
    answer = ask_local_node(my_question)
    
    print("\n--- AI RESPONSE ---")
    print(answer)