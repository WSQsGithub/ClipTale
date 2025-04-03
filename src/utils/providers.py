import os
from typing import Optional

from openai import AsyncOpenAI

from agents import (
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

BASE_URL = os.getenv("LLM_BASE_URL") or ""
API_KEY = os.getenv("LLM_API_KEY") or ""
MODEL_NAME = os.getenv("LLM_MODEL_NAME") or ""


def set_global_provider() -> None:
    """
    Set the LLM provider to OpenAI.
    This function will effect all the agents and tools.
    """
    client = AsyncOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
    )
    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def __init__(self, BASE_URL: Optional[str] = None, API_KEY: Optional[str] = None) -> None:
        self.BASE_URL = BASE_URL or os.getenv("LLM_BASE_URL")
        self.API_KEY = API_KEY or os.getenv("LLM_API_KEY")
        if not self.BASE_URL or not self.API_KEY or not self.MODEL_NAME:
            raise ValueError("Please set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME via env var or code.")  # noqa: TRY003

        self.client = AsyncOpenAI(
            base_url=self.BASE_URL,
            api_key=self.API_KEY,
        )

    def get_model(self, model_name: Optional[str] = None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=self.client)


async def main():
    from agents import Agent, Runner

    agent = Agent(name="Assistant", instructions="You only respond in haikus.")

    # CUSTOM_MODEL_PROVIDER = CustomModelProvider()

    # This will use the custom model provider
    # result = await Runner.run(
    #     agent,
    #     "What's the weather in Tokyo?",
    #     run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER),
    # )
    # print(result.final_output)

    # If you uncomment this, it will use OpenAI directly, not the custom provider
    result = await Runner.run(
        agent,
        "What's the weather in Tokyo?",
    )
    print(result.final_output)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
