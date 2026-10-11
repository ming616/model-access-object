import asyncio
import os

from model_service_connector_pool import (
    ConnectorMetadata,
    InMemoryConnectorRegistry,
    ModelServiceConnectorPool,
    OpenAICompatibleConnector,
)

from model_access_object import ModelAccessObject, ModelCapabilityRequirement, MSCPAdapter


async def main() -> None:
    registry = InMemoryConnectorRegistry()
    registry.register(
        OpenAICompatibleConnector(
            ConnectorMetadata(
                "configured-service",
                "openai-compatible",
                os.environ["MODEL_SERVICE_MODEL"],
                capabilities={"text"},
                supports_streaming=True,
            ),
            base_url=os.environ["MODEL_SERVICE_BASE_URL"],
            api_key=os.environ.get("MODEL_SERVICE_API_KEY"),
        )
    )
    async with ModelServiceConnectorPool(registry) as pool:
        mao = ModelAccessObject(MSCPAdapter(pool, acquire_timeout=5, invocation_timeout=60))
        async with mao.stream(
            "writer-01",
            "writer",
            "introduction",
            [{"role": "user", "content": "Explain layered model access in one paragraph."}],
            requirement=ModelCapabilityRequirement(required_tags={"text"}),
        ) as chunks:
            async for chunk in chunks:
                print(chunk.content, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())
