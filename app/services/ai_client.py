import json
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.fast_model = settings.FAST_MODEL
        self.deep_model = settings.DEEP_MODEL

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2000,
            response_format: Optional[Dict[str, str]] = None
    ) -> str:
        if model is None:
            model = self.fast_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://clearity.app",
            "X-Title": "Clearity"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            payload["response_format"] = response_format

        logger.info(f"Sending request to OpenRouter with model {model}, max_tokens={max_tokens}")
        logger.debug(f"Messages: {json.dumps(messages, ensure_ascii=False)}")
        
        import time
        start_time = time.time()

        async with httpx.AsyncClient(timeout=1200.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                elapsed_time = time.time() - start_time
                
                # Log raw response for debugging
                logger.debug(f"Raw API response status: {response.status_code}")
                logger.debug(f"Raw API response body: {response.text[:500]}...")  # First 500 chars
                
                result = response.json()
                logger.debug(f"Parsed JSON result keys: {result.keys()}")
                
                # Check if OpenRouter returned an error
                if "error" in result:
                    error_msg = result["error"].get("message", "Unknown error")
                    error_code = result["error"].get("code", "unknown")
                    logger.error(f"OpenRouter API error: {error_code} - {error_msg}")
                    raise Exception(f"OpenRouter API error: {error_msg} (code: {error_code})")
                
                # Check for model fallback
                if "model" in result:
                    actual_model = result.get("model", "unknown")
                    if actual_model != model:
                        logger.warning(f"Model fallback detected! Requested: {model}, Got: {actual_model}")
                
                # Log usage statistics
                if "usage" in result:
                    usage = result["usage"]
                    completion_tokens = usage.get("completion_tokens", 0)
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    tokens_per_sec = completion_tokens / elapsed_time if elapsed_time > 0 else 0
                    
                    logger.info(f"⚡ API Stats: {elapsed_time:.1f}s | "
                              f"Tokens: {completion_tokens}/{max_tokens} ({completion_tokens/max_tokens*100:.1f}%) | "
                              f"Speed: {tokens_per_sec:.1f} t/s | "
                              f"Prompt: {prompt_tokens} | Total: {total_tokens}")
                    
                    if completion_tokens >= max_tokens * 0.95:
                        logger.warning(f"⚠️  Response likely truncated! Used {completion_tokens} of {max_tokens} tokens (95%+)")

                message = result["choices"][0]["message"]
                content = message.get("content", "")
                
                # Handle reasoning models (content in reasoning field)
                if not content and "reasoning" in message:
                    logger.info("Detected reasoning model - extracting content from reasoning field")
                    content = message["reasoning"]
                elif not content and "reasoning_details" in message:
                    logger.info("Detected reasoning model - extracting content from reasoning_details field")
                    reasoning_parts = message.get("reasoning_details", [])
                    content = "\n".join([part.get("text", "") for part in reasoning_parts if "text" in part])
                
                logger.info(f"Received response from OpenRouter (length: {len(content) if content else 0})")
                
                # Log full content if it's short, or truncated if long
                if content:
                    if len(content) < 200:
                        logger.info(f"Full response content: {content}")
                    else:
                        logger.info(f"Response content (truncated): {content[:200]}...")
                else:
                    logger.warning("Response content is EMPTY or None even after checking reasoning fields!")
                    logger.warning(f"Full API result: {json.dumps(result, ensure_ascii=False)}")

                return content

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
                raise
            except KeyError as e:
                logger.error(f"Unexpected response structure from OpenRouter: {e}")
                logger.error(f"Response data: {json.dumps(result, ensure_ascii=False)}")
                raise
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {str(e)}")
                raise

    async def fast_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat_completion(messages, model=self.fast_model, **kwargs)

    async def deep_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat_completion(messages, model=self.deep_model, **kwargs)

    async def json_completion(self, messages: List[Dict[str, str]], use_deep: bool = False, **kwargs) -> Dict[str, Any]:
        model = self.deep_model if use_deep else self.fast_model
        response = ""
        max_tokens = kwargs.get('max_tokens', 2000)

        try:
            response = await self.chat_completion(
                messages,
                model=model,
                response_format={"type": "json_object"},
                **kwargs
            )
            logger.debug(f"Attempting to parse JSON response of length: {len(response)}")
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: '{response}'")
            logger.error(f"JSON decode error: {str(e)}")
            
            # Check if response might be truncated
            if len(response) > max_tokens * 3:  # Rough estimate: 1 token ~= 4 chars
                logger.error(f"Response length ({len(response)} chars) suggests it may have been truncated at max_tokens={max_tokens}")
                logger.error("Consider increasing max_tokens parameter")
            
            # Try to clean up common formatting issues
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            logger.info(f"Trying cleaned response: '{response_clean[:100]}...'")
            try:
                return json.loads(response_clean)
            except json.JSONDecodeError as e2:
                logger.error(f"Cleaned JSON also failed to parse: {str(e2)}")
                logger.error(f"Response appears to be incomplete. Last 100 chars: ...{response[-100:]}")
                raise ValueError(
                    f"AI response appears to be truncated or invalid JSON. "
                    f"Try increasing max_tokens (current: {max_tokens}). "
                    f"Error: {str(e)}"
                )


ai_client = AIClient()
