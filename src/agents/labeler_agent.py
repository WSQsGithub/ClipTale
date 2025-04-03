from agents import Agent


class LabelerAgent(Agent):
    def __init__(self, name: str = "Labler Agent", instructions: str = "Please label the audio files.") -> None:
        super().__init__(name=name, instructions=instructions)


async def main() -> None:
    from rich import print

    from agents import Runner

    labeler_agent = LabelerAgent()
    result = await Runner.run(starting_agent=labeler_agent, input="Please label the audio files.")

    print(result.final_output)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
