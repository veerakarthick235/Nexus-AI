import sys

def main():
    print("🤖 Hello! I am a simple terminal chatbot.")
    print("I don't have an AI brain connected yet, but I can echo what you type!")
    print("Type 'quit' or 'exit' to stop.")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower().strip() in ['quit', 'exit']:
                print("Bot: Goodbye! Have a great day!")
                break
            
            # Simple echo response
            print(f"Bot: I heard you say: '{user_input}'")
            
        except (KeyboardInterrupt, EOFError):
            print("\nBot: Goodbye!")
            break

if __name__ == "__main__":
    main()
