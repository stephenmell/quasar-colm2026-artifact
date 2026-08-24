#
#
from typing import TypeVar
import asyncio
import pydantic
from openai import AsyncOpenAI

#
from utils import (
    get_openai_client,
)

_T = TypeVar("_T")

client : AsyncOpenAI = get_openai_client(ASYNC=True)

async def query_ai_assistant_async(query: str, output_schema: type[_T]) -> _T:
    """Queries a Large Language Model with `query` and returns the language model's output. It must be used to process unstructured data into structured one.
    It is absolutely imperative that you use this function to parse data whose structure you don't know insted of parsing using regular expressions and/or
    string manipulation.
    There is no need to specify the expected output format in the query itself as the format will be specified on the side with `output_schema`
    with the build-in API of the assistant.
    :param query: a string with the query. Make sure to provide sufficient instructions to the AI assistant so that it can understand what it needs to do.
    Avoid just passing it tool outputs without additional instructions.
    :param output_schema: a Pydantic BaseModel class that specifies the expected output format from the model.
    The fields should have types as specific as possible to make sure the parsing is correct and accurate.
    allowed types are:
    - `int`
    - `str`
    - `float`
    - `bool`
    - `datetime.datetime` (assume `datetime` is imported from `datetime`)
    - `enum.Enum` classes
    - `pydantic.BaseModel` classes that you can define (assume that `BaseModel` is imported from `pydantic`) or are already defined in these instructions.
    - `pydantic.EmailStr` (assume that `EmailStr` is imported from `pydantic`)
    """
    assert issubclass(output_schema, pydantic.BaseModel)
    response = await client.beta.chat.completions.parse(
        # model="o3",
        model="gpt-4.1",
        # model="gpt-4.1-mini",
        # model = "gpt-4o-2024-08-06",
        # model = "gpt-4o-mini-2024-07-18",
        # model = "claude-3-5-sonnet-20241022",
        # model = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        response_format=output_schema,
        messages=[
            {
                "role": "system",
                "content": "You are a data-extraction assistant. You will be given a query and some data, and you should faithfully extract it into a structured format.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                ]
            },
        ],
        # max_tokens=10,
        temperature=0,
    )
    # print(response)
    s = response.choices[0].message.content
    if s is None:
        s = ""
    return output_schema.model_validate_json(s)

def query_ai_assistant_sync(query: str, output_schema: type[_T]) -> _T:
    return asyncio.run(query_ai_assistant_async(query, output_schema))

if __name__ == "__main__":
    from datetime import datetime
    class LunchEventInfo(pydantic.BaseModel):
        id_: str
        start_time: datetime
    
    lunch_event_info = query_ai_assistant_sync(
# "From the following events, extract the id and start_time of the lunch event with Sarah. Only return the lunch event.",
"""
From the following events, extract the id and start_time of the lunch event with Sarah. Only return the lunch event.
**2025-06-16**
Morning routine: 7:30-8:00
Sarah: 12:30-1:30
Dinner: 6:00-7:30
""",
        output_schema=LunchEventInfo,
    )
    print(lunch_event_info)