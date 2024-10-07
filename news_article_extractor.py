from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import time
import validators
import json
import re

# Load environment variables from a .env file
load_dotenv()

# Instantiate OpenAI client using API key from environment variables
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class NewsArticleExtractor:
    def __init__(self):
        # Initialize the NewsArticleExtractor class
        
        # Read Jina API key from environment variables
        self.api_key = os.getenv('JINA_API_KEY')
        self.base_url = 'https://r.jina.ai/'  # Base URL for the Jina API

        # Ensure the Jina API key was successfully loaded
        if not self.api_key:
            raise ValueError("Jina API key not found in environment variables.")  # Raise error if key is missing
        
    # Ensure the OpenAI API key was successfully loaded
    if not client.api_key:
        raise ValueError("OpenAI API key not found in environment variables.") 

    def extract_from_url(self, url: str):
        # Extract key attributes from the article found at the given URL

        # Validate the URL to check if it's in a correct format
        if not validators.url(url):
            raise ValueError(f"Invalid URL format: {url}")

        # Construct the full API request URL
        full_url = f'{self.base_url}{url}'

        # Prepare headers for the API request
        headers = {
            'Authorization': f'Bearer {self.api_key}',  # JinaAI Reader API key for authorization
            'X-Return-Format': 'markdown'  # Specify that we expect markdown content
        }

        # Send GET request to the API
        response = requests.get(full_url, headers=headers)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            content = response.text  # Extract the text content of the article
            return self.extract_key_attributes(content)  # Process and return key attributes
        else:
            # Raise an error if the request failed
            raise Exception(f"Failed to fetch the URL: {url}, Status code: {response.status_code}")

    def extract_key_attributes(self, content: str):
        # Extract specific attributes from the content of the article

        # Prepare a list of messages to send to the OpenAI API
        messages = [
            {"role": "system", 
             "content": """
             You are an expert assistant specialized in extracting detailed and structured attributes from news articles. 
             Your task is to return the requested information in the exact format specified below. 
             Only include the requested fields, without any additional explanations or irrelevant information.
             Format each field as 'Field Name: Value'. If a field is not available, return 'Field Name: N/A'.
             Your response must be accurate, structured, and professional.
             """},
            
            {"role": "user", 
             "content": f"""
            Here is the content of a news article in markdown format:
            {content}
            Please extract the following information in the exact format as shown below:
            1. Author Name: [Value]
            2. Main Topic: [Value]
            3. Short Summary: [Value]
            4. Keywords: [Value]
            5. Publication Date: [Value]
            6. Multimedia Descriptions (if any): [Value]
            7. Related Links or References: [Value]
            8. Language of the Article: [Value]
            9. Source Information: [Value]
            10. Other Insights: [Value]
            If any field is missing or not available, return 'N/A' as the value.
            """}
            ]
        
        # Call the OpenAI API to generate a response
        retries = 3  # Number of times to retry in case of an error
        for attempt in range(retries):
            try:
                # Request a completion from the OpenAI API with the provided messages
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500,  # Limit the response length
                    temperature=0.5  # Control randomness in the response
                )
                result = response.choices[0].message.content  # Extract the generated content

                # Parse the result into JSON format and save it to a file
                return self.parse_to_json(result, filename="output.json")  
            except Exception as e:
                # Log and handle any errors
                print(f"Error on attempt {attempt + 1}: {e}")
                time.sleep(2)  # Wait for 2 seconds before retrying
                if attempt == retries - 1:
                    raise Exception("Max retries reached, unable to complete request.")  # Stop after max retries

    def parse_to_json(self, result: str, filename: str):
        # Parse the structured response into a JSON object and save it to a file
        
        attributes = {}  # Initialize an empty dictionary to store attributes
        lines = result.split("\n")  # Split the generated result into lines for easier processing
        multimedia_descriptions = []  # List to hold multimedia descriptions
        related_links = []  # List to hold related links

        # Loop through each line and extract the corresponding information
        for line in lines:
            line = line.strip()  # Remove any leading or trailing whitespace
            line = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering from lines if present
            
            # Check for specific field prefixes and extract the values
            if "Author Name:" in line:
                attributes["author"] = line.replace("Author Name:", "").strip()  # Extract author
            elif "Main Topic:" in line:
                attributes["main_topic"] = line.replace("Main Topic:", "").strip()  # Extract main topic
            elif "Short Summary:" in line:
                attributes["summary"] = line.replace("Short Summary:", "").strip()  # Extract summary
            elif "Keywords:" in line:
                attributes["keywords"] = line.replace("Keywords:", "").strip()  # Extract keywords
            elif "Publication Date:" in line:
                attributes["publication_date"] = line.replace("Publication Date:", "").strip()  # Extract date
            elif "Multimedia Descriptions (if any):" in line:
                # Handle multimedia descriptions
                if "N/A" in line:
                    attributes["multimedia_descriptions"] = "N/A"  # If no multimedia, set to N/A
                else:
                    continue  # Continue processing multimedia descriptions if present
            elif "Related Links or References:" in line:
                continue  # Skip the header line for related links
            elif line.startswith("- "):  # Identify links in the article
                related_links.append(line.strip())  # Add related links to the list
            elif "Language of the Article:" in line:
                attributes["language"] = line.replace("Language of the Article:", "").strip()  # Extract language
            elif "Source Information:" in line:
                attributes["source_information"] = line.replace("Source Information:", "").strip()  # Extract source info
            elif "Other Insights:" in line:
                attributes["other_insights"] = line.replace("Other Insights:", "").strip()  # Extract other insights

        # Add the multimedia descriptions and related links to the attributes
        if multimedia_descriptions:
            attributes["multimedia_descriptions"] = multimedia_descriptions
        if related_links:
            attributes["related_links"] = related_links

        # Ensure all required fields have values, set defaults if missing
        attributes.setdefault("author", "N/A")
        attributes.setdefault("main_topic", "N/A")
        attributes.setdefault("summary", "N/A")
        attributes.setdefault("keywords", "N/A")
        attributes.setdefault("publication_date", "N/A")
        attributes.setdefault("multimedia_descriptions", "N/A")
        attributes.setdefault("related_links", "N/A")
        attributes.setdefault("language", "N/A")
        attributes.setdefault("source_information", "N/A")
        attributes.setdefault("other_insights", "N/A")

        # Save the parsed attributes to a JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(attributes, f, ensure_ascii=False, indent=4)

        print(f"JSON data successfully saved to {filename}")  # Confirm file was saved

        # Return the JSON as a formatted string
        return json.dumps(attributes, ensure_ascii=False, indent=4)


# Example
extractor = NewsArticleExtractor()  # Instantiate the extractor class
url = 'https://www.cnn.com/2024/10/06/weather/tropical-storm-milton-florida-sunday/index.html'  # URL of a news article
key_attributes = extractor.extract_from_url(url)  # Extract key attributes from the article
print(key_attributes)  # Print the extracted information