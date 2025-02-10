# Competitor Data Aggregation & SWOT Analysis Workflow

This project implements a multi-agent workflow designed to aggregate competitor data from various sources and generate a detailed SWOT analysis. The workflow uses multiple agents, each performing a specialized task, such as retrieving competitor data, performing NLP analysis, generating feature comparisons, and ultimately creating a comprehensive business report.

## Features
- Aggregates competitor data from sources such as Crunchbase, LinkedIn, Reddit, Google, and G2.
- Natural Language Processing (NLP) for extracting key insights.
- Feature comparison between competitors and the startup.
- Automated SWOT analysis generation.
- Final report includes a detailed competitor landscape and strategic recommendations.

## Technology Stack
- **Python** for the core logic of the workflow.
- **Agents** from the `phi` package to handle various tasks such as data retrieval and analysis.
- **Groq** for running language models.
- **TavilyTools** for web scraping and API integrations.
  
## Setup Instructions

### Prerequisites
- Python 3.x
- [Groq API](https://groq.com/) account to use the language models.
- [Tavily API](https://tavily.com/) account for data scraping and API integrations.

### Environment Variables
Before running the project, make sure to set up the required API keys in your environment variables:

- `GROQ_API_KEY`: Your Groq API key.
- `TAVILY_API_KEY`: Your Tavily API key.

You can set these variables in your environment or create a `.env` file in the project directory with the following content:





### Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/your-username/competitor-analysis-workflow](https://github.com/sabahatijaz/multi-agent-LLM-based-prototype.git
   cd multi-agent-LLM-based-prototype

# multi-agent, LLM-based prototype
## Setup Steps
1. Create Virtual env and activate it
2. Run: pip install -r requirements.txt
3. Create a .env with following and add your api keys:
TAVILY_API_KEY=''
GROQ_API_KEY=''
4. Run: python main.py
