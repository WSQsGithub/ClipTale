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


def set_global_provider() -> None:
    """
    This function configures the global OpenAI client settings using environment variables.
    It sets up an async OpenAI client with the provided base URL and API key, and configures
    it as the default client for all agents and tools.

    Environment Variables:
        LLM_BASE_URL: Base URL for the OpenAI API endpoint
        LLM_API_KEY: API key for authentication with OpenAI

    Raises:
        ValueError: If LLM_BASE_URL or LLM_API_KEY environment variables are not set

    Returns:
        None

    Example:
        >>> set_global_provider()
        # Sets up OpenAI client globally using environment variables
    """
    BASE_URL = os.getenv("LLM_BASE_URL")
    API_KEY = os.getenv("LLM_API_KEY")

    if not BASE_URL or not API_KEY:
        raise ValueError("Please set LLM_BASE_URL and LLM_API_KEY via env var.")  # noqa: TRY003

    client = AsyncOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
    )
    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def __init__(self, BASE_URL: Optional[str] = None, API_KEY: Optional[str] = None) -> None:
        self.BASE_URL = os.getenv("LLM_BASE_URL")
        self.API_KEY = os.getenv("LLM_API_KEY")
        self.MODEL_NAME = os.getenv("LLM_MODEL_NAME")

        if not self.BASE_URL or not self.API_KEY or not self.MODEL_NAME:
            raise ValueError("Please set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME via env var or code.")  # noqa: TRY003

        self.client = AsyncOpenAI(
            base_url=self.BASE_URL,
            api_key=self.API_KEY,
        )

    def get_model(self, model_name: Optional[str] = None) -> Model:
        """
        Retrieves an OpenAI chat completion model instance.

        Args:
            model_name (Optional[str]): The name of the OpenAI model to use. If None, uses the default model.

        Returns:
            Model: An instance of OpenAIChatCompletionsModel configured with the specified model name and client.

        Example:
            >>> provider = OpenAIProvider()
            >>> model = provider.get_model("gpt-4")
        """
        if model_name is None:
            model_name = self.MODEL_NAME
        return OpenAIChatCompletionsModel(model=model_name, openai_client=self.client)  # type: ignore # noqa: PGH003


async def main() -> None:
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
