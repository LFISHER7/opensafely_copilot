from django.shortcuts import render
import os
import openai
import pinecone
from dotenv import load_dotenv

load_dotenv()

# Get the OpenAI and Pinecone API keys from the .env file
openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone with the API key and select the index
pinecone.init(api_key=pinecone_api_key, environment='us-west4-gcp')
pinecone_index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))

def get_embedding(text, model="text-embedding-ada-002"):
    """
    Get the embedding for the given text using the OpenAI API.
    """
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']

def generate_answer(question="", supporting_text=[], system_message="You are a helpful assistant that can answer questions about the OpenSAFELY platform using the supporting text provided. If the answer is not in the supporting text, you can say 'No similar text found in the documentation. Please try again. If you are going to provide code blocks in your answer, the code blocks should only be copied from the supporting text'"):
    """
    Generate an answer to the given question using the OpenAI GPT-3.5 API.
    """
    if len(supporting_text) == 0:
        return "No similar text found in the documentation. Please try again."

    # Define the chat messages for the OpenAI API
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"The supporting texts from the documentation are: {[supporting_text[i] for i in supporting_text]}"},
        {"role": "user", "content": "What is the answer to the question?"},
        {"role": "user", "content": question}
    ]

    # Get the response from the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        n=1,
        temperature=0.5,
    )

    answer = response['choices'][0]['message']['content'].strip()
    return answer

def query_pinecone(query_vector, top_k=5):
    """
    Query the Pinecone index with the given query vector and return the top-k results.
    """
    results = pinecone_index.query(
        vector=query_vector,
        top_k=top_k,
        include_values=False,
        include_metadata=True
    )
    return results

def index(request, system_message=None):
    """
    View function for the homepage. Allows the user to ask a question and returns an answer with 
    the top 5 sections of supporting text from the OpenSAFELY documentation.
    """

    answer = None

    # When a POST request is received
    if request.method == 'POST':
        # Extract the user's query
        query = request.POST.get('question')
        # system message - get. if none, set to None
        system_message = request.POST.get('system_message')
        if system_message == '':
            system_message = None
        


        # Get the vector representation of the query using OpenAI's Text Embedding API
        query_embedding = get_embedding(query)

        # Search the Pinecone index to find the documents most similar to the query
        embeddings = query_pinecone(query_embedding, top_k=5)
        matches = embeddings['matches']
  
        # Create a dictionary of links to supporting text for each matching document
        supporting_text = {}
        for i in matches:
            link = i['id']
            header = link.split('/')[-1]
            subheader = link.split('/')[-2]

            # Capitalize the first letter of the header and replace dashes with spaces
            header = header[0].upper() + header[1:]
            subheader = subheader[0].upper() + subheader[1:]
            header = header.replace('-', ' ')
            subheader = subheader.replace('-', ' ')

            # Combine the subheader and header into a string representing the location of the supporting text
            
            if subheader == 'Docs.opensafely.org':
                supporting = header.replace('#', '')
            else:   
                supporting = f"{subheader}: {header.replace('#', '')}"
            supporting_text[link] = supporting

        # Generate an answer to the user's query using  GPT-3.5
        if system_message is None:
            print('NO SYSTEM MESSAGE. Using default')
            answer = generate_answer(query, supporting_text)
        else:
            print('SYSTEM MESSAGE. Using custom')
            print(f'SYSTEM MESSAGE: {system_message}')
            answer = generate_answer(query, supporting_text, system_message=system_message)

        # If the answer contains a code block, as indicated by ``` at the start and end of the answer, 
        # then separate out the code blocks from the text
        code_block_indices = []
        if '```' in answer:
            answer = answer.split('```')
            num_splits = len(answer)
            if num_splits % 2 != 0:
                for i in range(1, num_splits, 2):
                    code_block_indices.append(i)

        # If the answer doesn't contain any code blocks, wrap it in a list so it can be easily processed in the template
        else:
            answer = [answer]
            code_block_indices = []

        # Render the index.html template with the answer, supporting text, and code block information
        return render(request, 'index.html', {'answer': answer, 'supporting_text': supporting_text, 'code_block_indices': code_block_indices})

    # When a GET request is received
    return render(request, 'index.html', {'answer': answer})