from dotenv import load_dotenv
load_dotenv()  # Loading environment variables from .env file

# Importing the Groq Chat Model
from langchain_groq import ChatGroq

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


response = llm.invoke("Reply with exactly : Manchester United is the best football team in the world.")


print(response.content)
