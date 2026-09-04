from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from pydantic import Field, ConfigDict
from langchain_core.outputs import ChatGeneration, ChatResult
from typing import List, Optional, Dict, Any
import requests


class CustomChatModel(BaseChatModel):
    model_name: str = Field(..., min_length=1)
    api_url: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    temperature: float = Field(default=0.5, ge=0)
    top_p: float = Field(default=1.0, alias="topP")
    streaming: bool = Field(default=True)
    model_config = ConfigDict(env_prefix="MY_MODEL_")

    @property
    def _llm_type(self) -> str:
        return "custom-chat-model"

    def __init__(self, api_url: str, api_key: str, model: str, stream: bool = True):
        super().__init__(api_url=api_url, api_key=api_key, model_name=model)
        self.temperature = 0.5
        self.top_p = 1
        # Azure OpenAI doesn't work well with generic stream mode
        if "openai.azure.com" in api_url:
            stream = False
        self.streaming = stream

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成响应"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})

        is_azure = "openai.azure.com" in self.api_url

        if is_azure:
            payload = {
                "messages": formatted_messages,
                "max_tokens": 4096,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key,
            }
        else:
            payload = {
                "messages": formatted_messages,
                "model": self.model_name,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "stream": self.streaming,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

        try:
            if self.streaming:
                # Streaming response
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    stream=True,
                )
                response.raise_for_status()
                content = self._parse_stream(response)
                return ChatResult(
                    generations=[ChatGeneration(message=AIMessage(content=content))],
                    llm_output={"streamed": True},
                )
            else:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

    def _parse_stream(self, response: requests.Response) -> str:
        """Parse SSE streaming response."""
        content = ""
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    import json
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        content += chunk
                except json.JSONDecodeError:
                    continue
        return content

    def _parse_response(self, data: Dict) -> ChatResult:
        """解析 API 响应为 LangChain 格式"""
        choices = data.get("choices", [])
        if not choices:
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=""))],
                llm_output=data,
            )
        choice = choices[0]
        message_data = choice.get("message", {})
        content = message_data.get("content", "")
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))],
            llm_output=data,
        )
