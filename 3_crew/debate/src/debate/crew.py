from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Debate():
    """Debate crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'],  # type: ignore
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],  # type: ignore
            verbose=True
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'],  # type: ignore
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'],  # type: ignore
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'],  # type: ignore
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""

        return Crew(
            agents=self.agents,  # type: ignore  # Automatically created by the @agent decorator
            tasks=self.tasks,  # type: ignore  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
