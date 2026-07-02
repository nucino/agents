# src/financial_researcher/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool  # type: ignore[import]

@CrewBase
class ResearchCrew():
    """Research crew for comprehensive topic analysis and reporting"""

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[attr-defined]
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],  # type: ignore[attr-defined]
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config['research_task']  # type: ignore[attr-defined]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config['analysis_task'],  # type: ignore[attr-defined]
            output_file='output/report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )