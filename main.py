import json
from typing import Optional, Iterator
from textwrap import dedent
from phi.agent import Agent
from phi.workflow import Workflow, RunResponse, RunEvent
from phi.model.groq import Groq
from phi.storage.workflow.sqlite import SqlWorkflowStorage
from phi.utils.pprint import pprint_run_response
from phi.utils.log import logger
from phi.tools.tavily import TavilyTools
import os 

class ReportGenerator(Workflow):
    searcher: Agent = Agent(
    model=Groq(id="llama3-8b-8192", api_key=os.environ.get('GROQ_API_KEY')),
    tools=[TavilyTools(api_key=os.environ.get('TAVILY_API_KEY'))], 
    instructions=[
        "Your task is to retrieve competitor data from multiple sources, including Crunchbase, LinkedIn, Reddit, Google, and G2.",
        "Aggregate the top 5 competitors based on a given startup website or product query.",
        "Ensure the data is normalized and consistent across sources, resolving any missing or conflicting data.",
        "Provide a comprehensive summary of each competitor, including key features, market positioning, and recent activities.",
        "Your output should be a well-structured dataset of competitors that can be used by the other agents for further processing."
    ],
)

    nlp_agent: Agent = Agent(
    model=Groq(id="llama3-8b-8192", api_key=os.getenv('GROQ_API_KEY')),
    instructions=[
        "Your task is to preprocess and analyze the competitor data retrieved by the searcher agent.",
        "Carefully read the data and apply natural language processing techniques to extract key insights, such as features, product descriptions, and business strategies.",
        "Ensure the extracted data is clean, tokenized, and ready for further analysis by the feature comparison and SWOT agents.",
        "Provide structured outputs that clearly outline key attributes of each competitor for subsequent tasks."
    ],
)


    comparison_agent: Agent = Agent(
    model=Groq(id="llama3-8b-8192", api_key=os.getenv('GROQ_API_KEY')),
    instructions=[
        "Your task is to compare the features of the startup's product/service with the top 5 competitors identified by the searcher agent.",
        "Carefully analyze the data and highlight similarities and differences in product features, pricing, and key differentiators.",
        "Generate a structured feature comparison summary that highlights common features, unique selling points, and potential areas of improvement.",
        "This comparison will feed into the final competitor analysis report and help inform strategic recommendations."
    ],
    expected_output=dedent("""\
                           An engaging, informative, and well-structured article in the following format:
                           [
    {
        "text": "Competitor A",
        "keywords": ["innovation", "expensive", "user-friendly"],
        "entities": [["Company X", "ORG"], ["New York", "GPE"], ["global growth", "ORG"]]
    },
    {
        "text": "Competitor B",
        "keywords": ["outdated", "scalable", "market leader"],
        "entities": [["Company Y", "ORG"], ["California", "GPE"], ["rising competition", "ORG"]]
    }
]""")
)


    swot_agent: Agent = Agent(
    model=Groq(id="llama3-8b-8192", api_key=os.getenv('GROQ_API_KEY')),
    instructions=[
        "Your task is to generate a detailed SWOT analysis for the startup and its top 5 competitors.",
        "Carefully review the data provided by the searcher and NLP agents and assess each competitor's strengths, weaknesses, opportunities, and threats.",
        "Synthesize the SWOT analysis into actionable insights, focusing on how the startup can position itself in the market.",
        "Ensure that the SWOT analysis is concise, well-structured, and highlights key strategic recommendations for the startup."
    ],
)
    report_agent: Agent = Agent(
    model=Groq(id="llama3-8b-8192", api_key=os.getenv('GROQ_API_KEY')),
    instructions=[
        "Your task is to generate a comprehensive business report that includes the following sections:",
        "- A detailed SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) for the given company, based on the provided data.",
        "- A comparison of the company's products or services with its competitors, highlighting key differentiators, similarities, and potential competitive advantages.",
        "- Summarize the competitor landscape, including notable strategies, market positioning, and business features.",
        "- Ensure that the report is structured, clear, and professional, with a concise executive summary at the beginning.",
        "- Use formal language and ensure that the data is presented in a logical and easy-to-understand manner."
    ],
)



    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        """This is where the main logic of the workflow is implemented."""

        logger.info(f"Generating a SWOT analysis on: {topic}")
        if use_cache:
            cached_topic = self.get_cached_topic(topic)
            if cached_topic:
                yield RunResponse(content=cached_topic, event=RunEvent.workflow_completed)
                return

        search_results= self.get_search_results(topic)
        # If no search_results are found for the topic, end the workflow
        if search_results is None:
            yield RunResponse(
                event=RunEvent.workflow_completed,
                content=f"Sorry, could not find any articles on the topic: {topic}",
            )
            return
        preprocessed=self.nlp_preprocessing( search_results)
        comparison=self.feature_comparison(topic=topic,search_results=preprocessed)
        swot= self.swot_analysis(topic,search_results=preprocessed,comparison=comparison)
        yield from self.generate_report(topic,search_results=preprocessed,comparison=comparison, swot=swot)

    def get_cached_topic(self, topic: str) -> Optional[str]:
        """Get the cached  for a topic."""

        logger.info("Checking if cached topic exists")
        return self.session_state.get("topic", {}).get(topic)

    def add_topic_to_cache(self, topic: str, topic_data: Optional[str]):
        """Add a topic to the cache."""

        logger.info(f"Saving topic: {topic}")
        self.session_state.setdefault("topic", {})
        self.session_state["topic"][topic] = topic_data

    def get_search_results(self, topic: str):
        """Get the search results for a topic."""

        MAX_ATTEMPTS = 3

        for attempt in range(MAX_ATTEMPTS):
            try:
                searcher_response = self.searcher.run(topic)

                if not searcher_response or not searcher_response.content:
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Empty searcher response")
                    continue

                return searcher_response.content

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {str(e)}")

        logger.error(f"Failed to get search results after {MAX_ATTEMPTS} attempts")
        return None

    def nlp_preprocessing(self, search_results):
        res=self.nlp_agent.run(json.dumps(search_results, indent=4), stream=False)
        return res.content
    

    def feature_comparison(self, topic: str, search_results):
        writer_input = {"topic": topic, "search results": search_results}

        return self.comparison_agent.run(json.dumps(writer_input, indent=4), stream=False).content

    def swot_analysis(self, topic: str, search_results, comparison):
        writer_input = {"topic": topic, "search results": search_results, "comparison":  comparison}
        res=self.swot_agent.run(json.dumps(writer_input, indent=4), stream=False)
        return res.content
    

    def generate_report(self, topic: str, search_results, comparison, swot):
        writer_input = {"topic": topic, "search results": search_results, "comparison":  comparison, "SWOT_Analyis": swot}
        yield from self.report_agent.run(json.dumps(writer_input, indent=4), stream=True)
        self.add_topic_to_cache(topic, self.report_agent.run_response.content)

if __name__ == "__main__":
    from rich.prompt import Prompt

    # Get topic from user
    topic = Prompt.ask(
        "[bold]Enter a  topic[/bold]\n✨",
        default="Dell",
    )

    url_safe_topic = topic.lower().replace(" ", "-")

    generate_report = ReportGenerator(
        session_id=f"generate-report-on-{url_safe_topic}",
        storage=SqlWorkflowStorage(
            table_name="generate_resport_workflows",
            db_file="tmp/workflows.db",
        ),
    )

    report: Iterator[RunResponse] = generate_report.run(topic=topic, use_cache=True)

    pprint_run_response(report, markdown=True)
