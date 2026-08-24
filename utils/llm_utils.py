import base64
from io import BytesIO
from openai import OpenAI, AsyncOpenAI
import re
import os
from typing import Optional

def get_openai_client(ASYNC: bool = False, api_key: Optional[str] = None, organization: Optional[str] = None) -> Optional[OpenAI | AsyncOpenAI]:
    if api_key is None:
        try:
            with open("openai_api_key.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❗️ API key file not found and OPENAI_API_KEY environment variable not set. Please create a file named 'openai_api_key.txt' with your API key or set the OPENAI_API_KEY environment variable.")
                return None

    if ASYNC:
        if organization:
            client = AsyncOpenAI(api_key=api_key, organization=organization)
        else:
            client = AsyncOpenAI(api_key=api_key)
        return client
    else:
        if organization:
            client = OpenAI(api_key=api_key, organization=organization)
        else:
            client = OpenAI(api_key=api_key)
    return client

def encode_image(image_pil):
    buffer = BytesIO()
    try:
        image_pil.save(buffer, format="JPEG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")
    finally:
        buffer.close()

def response_to_py_program(response, question):
    matches = re.findall(r"```python(.*)```", response, re.DOTALL)
    if matches:
        program = matches[0].strip()
        program = re.sub(r"^#+.*\n+", "", program).strip()
        program = f"### {question}\n\n{program}"
        return program
    else:
        return response.strip()

def response_to_epics_program(response, question=None):
    program = re.findall(r"```epic(.*)```", response, re.DOTALL)[0].strip()
    program = re.sub(r"^#+.*\n+", "", program).strip()
    # program = f"### {question}\n\n{program}"
    return program