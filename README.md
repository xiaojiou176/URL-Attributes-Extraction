# URL Attributes Extraction Project

## Overview
This project automates the extraction of useful attributes from a news article URL. The purpose of the project is to accelerate the preparation of documentation, such as for visa petitions, by extracting key metadata like author name, main topic, summary, and other relevant attributes. The extracted content is saved as a JSON file, making it easy to further process and use the data.

## Features
- Automatically extracts the following key information from news articles:
  - Author Name
  - Main Topic
  - Short Summary
  - Keywords
  - Publication Date
  - Multimedia Descriptions (if any)
  - Related Links or References
  - Language of the Article
  - Source Information
  - Other Insights
- Saves the extracted information in JSON format for further analysis or integration with other systems.
- Flexible architecture, allowing future support for other content types (e.g., PDFs, videos).


## Requirements

### Prerequisites
Before you begin, ensure you have met the following requirements:
- **Python 3.x**
- **OpenAI API key**: Add this to a `.env` file to allow access to the API.

### Tools Used
- **OpenAI's GPT model** for content extraction and summarization.
- **Jina AI tools** like [Jina Reader](https://jina.ai/reader) for converting web content to markdown.