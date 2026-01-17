from core        import Log, Run, Utils, Parser, Signature, Anon, Headers
from curl_cffi   import requests, CurlMime
from dataclasses import dataclass, field
from bs4         import BeautifulSoup
from json        import dumps, loads
from secrets     import token_hex
from uuid        import uuid4
import time
import random

# Remove free-proxy import and functionality

@dataclass
class Models:
    models: dict[str, list[str]] = field(default_factory=lambda: {
        "grok-3-auto": ["MODEL_MODE_AUTO", "auto"],
        "grok-3-fast": ["MODEL_MODE_FAST", "fast"],
        "grok-4": ["MODEL_MODE_EXPERT", "expert"],
        "grok-4-mini-thinking-tahoe": ["MODEL_MODE_GROK_4_MINI_THINKING", "grok-4-mini-thinking"]
    })

    def get_model_mode(self, model: str, index: int) -> str:
        return self.models.get(model, ["MODEL_MODE_AUTO", "auto"])[index]

_Models = Models()

class Grok:
    
    
    def __init__(self, model: str = "grok-3-auto", proxy: str = None) -> None:
        self.session: requests.session.Session = requests.Session(impersonate="chrome136", default_headers=False)
        # Optimize session with connection pooling and keep-alive
        self.session.verify = False  # Disable SSL verification for faster connections
        self.session.headers.update({
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=10, max=1000"
        })
        self.headers: Headers = Headers()
        
        self.model_mode: str = _Models.get_model_mode(model, 0)
        self.model: str = model
        self.mode: str = _Models.get_model_mode(model, 1)
        self.c_run: int = 0
        self.keys: dict = Anon.generate_keys()
        
        # Store original proxy
        self.original_proxy = proxy
        
        # Set up proxy if provided
        if proxy:
            self.session.proxies = {
                "all": proxy
            }
        
        # Initialize optimized retry settings
        self.max_retries: int = 3  # Reduced max retries for faster failure
        self.base_delay: float = 0.05  # Significantly reduced base delay for faster retries
        self.max_delay: float = 15.0  # Reduced maximum delay
        self.backoff_factor: float = 1.2  # Reduced backoff factor for faster retries
        
        # Fast retry settings for quick bypass
        self.fast_retry_attempts: int = 3  # Increased fast retry attempts
        self.fast_delay: float = 0.05  # Very short delay for fast retries
    
    def _calculate_delay(self, attempt: int, is_fast_retry: bool = False) -> float:
        """Calculate delay with exponential backoff and jitter"""
        if is_fast_retry:
            # Use fast retry settings
            base_delay = min(self.fast_delay * (1.1 ** attempt), 1.0)  # Even faster exponent
        else:
            # Calculate base delay with exponential backoff
            base_delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        
        # Reduce jitter range for more predictable timing
        jitter_range = base_delay * 0.1  # Reduced jitter to 10%
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(base_delay + jitter, 0.02)  # Further reduced minimum delay
        return delay
    
    def _create_new_session(self):
        """Create a new session with fresh impersonation to bypass rate limits"""
        new_session = requests.Session(impersonate="chrome136", default_headers=False)
        # Optimize new session with same performance settings
        new_session.verify = False
        new_session.headers.update({
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=10, max=1000"
        })
        if hasattr(self, 'session') and hasattr(self.session, 'proxies'):
            new_session.proxies = getattr(self.session, 'proxies', {})
        return new_session
    
    # Remove _get_free_proxy method since we're removing free-proxy functionality
    
    def _handle_rate_limit(self, message: str, extra_data: dict = None) -> dict:
        """Handle rate limiting with multiple strategies including fast bypass"""
        
        # First, try fast retries with minimal delay
        for fast_attempt in range(self.fast_retry_attempts):
            delay = self._calculate_delay(fast_attempt, is_fast_retry=True)
            Log.Info(f"Rate limited (fast retry {fast_attempt + 1}/{self.fast_retry_attempts}). Waiting {delay:.2f}s before fast retry...")
            time.sleep(delay)
            
            try:
                # Create a new instance with the same proxy settings
                new_grok = Grok(self.model, self.original_proxy)
                
                # If we have extra_data, use continue_convo, otherwise use start_convo
                if extra_data:
                    # Load conversation state in new instance
                    new_grok._load(extra_data)
                    new_grok.c_run = 1
                    new_grok.anon_user = extra_data["anon_user"]
                    new_grok.keys["privateKey"] = extra_data["privateKey"]
                    new_grok.c_request(new_grok.actions[1])
                    new_grok.c_request(new_grok.actions[2])
                    result = new_grok.continue_conversation(message, extra_data)
                    
                    # If successful, return result
                    if "error" not in result or "rate limiting" not in str(result.get("error", "")).lower():
                        return result
                else:
                    result = new_grok.start_convo(message, extra_data)
                    
                    # If successful, return result
                    if "error" not in result or "rate limiting" not in str(result.get("error", "")).lower():
                        return result
                        
            except Exception as e:
                Log.Error(f"Fast retry attempt {fast_attempt + 1} failed: {str(e)}")
                continue  # Continue to normal retries
        
        # If fast retries didn't work, proceed with normal retries
        for attempt in range(self.max_retries):
            delay = self._calculate_delay(attempt)
            Log.Info(f"Rate limited (normal retry {attempt + 1}/{self.max_retries}). Waiting {delay:.2f}s before retry...")
            time.sleep(delay)
            
            try:
                # Create a new instance with the same proxy settings
                new_grok = Grok(self.model, self.original_proxy)
                
                # If we have extra_data, use continue_convo, otherwise use start_convo
                if extra_data:
                    # Load conversation state in new instance
                    new_grok._load(extra_data)
                    new_grok.c_run = 1
                    new_grok.anon_user = extra_data["anon_user"]
                    new_grok.keys["privateKey"] = extra_data["privateKey"]
                    new_grok.c_request(new_grok.actions[1])
                    new_grok.c_request(new_grok.actions[2])
                    result = new_grok.continue_conversation(message, extra_data)
                    
                    # If successful, return result
                    if "error" not in result or "rate limiting" not in str(result.get("error", "")).lower():
                        return result
                else:
                    result = new_grok.start_convo(message, extra_data)
                    
                    # If successful, return result
                    if "error" not in result or "rate limiting" not in str(result.get("error", "")).lower():
                        return result
                        
            except Exception as e:
                Log.Error(f"Normal retry attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:  # Last attempt
                    Log.Error("All retry attempts failed")
                    return {"error": "All retry attempts failed due to rate limiting"}
        
        return {"error": "Failed after maximum retries"}
    
    def _load(self, extra_data: dict = None) -> None:
        
        if not extra_data:
            self.session.headers = self.headers.LOAD
            # Optimized loading with shorter timeout
            load_site: requests.models.Response = self.session.get('https://grok.com/c', timeout=10)
            self.session.cookies.update(load_site.cookies)
            
            scripts: list = [s['src'] for s in BeautifulSoup(load_site.text, 'html.parser').find_all('script', src=True) if s['src'].startswith('/_next/static/chunks/')]

            self.actions, self.xsid_script = Parser.parse_grok(scripts)
            
            self.baggage: str = Utils.between(load_site.text, '<meta name="baggage" content="', '"')
            self.sentry_trace: str = Utils.between(load_site.text, '<meta name="sentry-trace" content="', '-')
        else:
            self.session.cookies.update(extra_data["cookies"])

            self.actions: list = extra_data["actions"]
            self.xsid_script: list =  extra_data["xsid_script"]
            self.baggage: str = extra_data["baggage"]
            self.sentry_trace: str = extra_data["sentry_trace"]
            
    
    def c_request(self, next_action: str) -> None:
        
        self.session.headers = self.headers.C_REQUEST
        self.session.headers.update({
            'baggage': self.baggage,
            'next-action': next_action,
            'sentry-trace': f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
        })
        self.session.headers = Headers.fix_order(self.session.headers, self.headers.C_REQUEST)
        
        if self.c_run == 0:
            self.session.headers.pop("content-type")
            
            mime = CurlMime()
            mime.addpart(name="1", data=bytes(self.keys["userPublicKey"]), filename="blob", content_type="application/octet-stream")
            mime.addpart(name="0", filename=None, data='[{"userPublicKey":"$o1"}]')
            
            c_request: requests.models.Response = self.session.post("https://grok.com/c", multipart=mime, timeout=10)
            self.session.cookies.update(c_request.cookies)
            
            self.anon_user: str = Utils.between(c_request.text, '{"anonUserId":"', '"')
            self.c_run += 1
            
        else:
            
            match self.c_run:
                case 1:
                    data: str = dumps([{"anonUserId":self.anon_user}])
                case 2:
                    data: str = dumps([{"anonUserId":self.anon_user,**self.challenge_dict}])
            
            c_request: requests.models.Response = self.session.post('https://grok.com/c', data=data, timeout=10)
            self.session.cookies.update(c_request.cookies)

            match self.c_run:
                case 1:
                    start_idx = c_request.content.hex().find("3a6f38362c")
                    if start_idx != -1:
                        start_idx += len("3a6f38362c")
                        end_idx = c_request.content.hex().find("313a", start_idx)
                        if end_idx != -1:
                            challenge_hex = c_request.content.hex()[start_idx:end_idx]
                            challenge_bytes = bytes.fromhex(challenge_hex)

                    self.challenge_dict: dict = Anon.sign_challenge(challenge_bytes, self.keys["privateKey"])
                    Log.Success(f"Solved Challenge: {self.challenge_dict}")
                case 2:
                    self.verification_token, self.anim = Parser.get_anim(c_request.text, "grok-site-verification")
                    self.svg_data, self.numbers = Parser.parse_values(c_request.text, self.anim, self.xsid_script)
                    
            self.c_run += 1
        
    
    def start_convo(self, message: str, extra_data: dict = None) -> dict:
        
        if not extra_data:
            self._load()
            self.c_request(self.actions[0])
            self.c_request(self.actions[1])
            self.c_request(self.actions[2])
            xsid: str = Signature.generate_sign('/rest/app-chat/conversations/new', 'POST', self.verification_token, self.svg_data, self.numbers)
        else:
            self._load(extra_data)
            self.c_run: int = 1
            self.anon_user: str = extra_data["anon_user"]
            self.keys["privateKey"] = extra_data["privateKey"]
            self.c_request(self.actions[1])
            self.c_request(self.actions[2])
            xsid: str = Signature.generate_sign(f'/rest/app-chat/conversations/{extra_data["conversationId"]}/responses', 'POST', self.verification_token, self.svg_data, self.numbers)

        self.session.headers = self.headers.CONVERSATION
        self.session.headers.update({
            'baggage': self.baggage,
            'sentry-trace': f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            'x-statsig-id': xsid,
            'x-xai-request-id': str(uuid4()),
            'traceparent': f"00-{token_hex(16)}-{token_hex(8)}-00"
        })
        self.session.headers = Headers.fix_order(self.session.headers, self.headers.CONVERSATION)
        
        if not extra_data:
            conversation_data: dict = {
                'temporary': False,
                'modelName': self.model,
                'message': message,
                'fileAttachments': [],
                'disableSearch': False,
                'enableImageGeneration': True,
                'returnImageBytes': False,
                'returnRawGrokInXaiRequest': False,
                'enableImageStreaming': True,
                'imageGenerationCount': 2,
                'forceConcise': False,
                'toolOverrides': {},
                'enableSideBySide': True,
                'sendFinalMetadata': True,
                'isReasoning': False,
                'webpageUrls': [],
                'disableTextFollowUps': False,
                'responseMetadata': {
                    'requestModelDetails': {
                        'modelId': self.model,
                    },
                },
                'disableMemory': False,
                'forceSideBySide': False,
                'modelMode': self.model_mode,
                'isAsyncChat': False,
            }
            
            # Optimized timeout for faster response
            convo_request: requests.models.Response = self.session.post('https://grok.com/rest/app-chat/conversations/new', json=conversation_data, timeout=15)
            
            if "modelResponse" in convo_request.text:
                response = conversation_id = parent_response = image_urls = None
                stream_response: list = []
                
                for response_dict in convo_request.text.strip().split('\n'):  
                    data: dict = loads(response_dict)

                    token: str = data.get('result', {}).get('response', {}).get('token')
                    if token:
                        stream_response.append(token)
                        
                    if not response and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('message'):
                        response: str = data['result']['response']['modelResponse']['message']

                    if not conversation_id and data.get('result', {}).get('conversation', {}).get('conversationId'):
                        conversation_id: str = data['result']['conversation']['conversationId']

                    if not parent_response and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('responseId'):
                        parent_response: str = data['result']['response']['modelResponse']['responseId']
                    
                    if not image_urls and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('generatedImageUrls', {}):
                        image_urls: str = data['result']['response']['modelResponse']['generatedImageUrls']
                    
                
                return {
                    "response": response,
                    "stream_response": stream_response,
                    "images": image_urls,
                    "extra_data": {
                        "anon_user": self.anon_user,
                        "cookies": self.session.cookies.get_dict(),
                        "actions": self.actions,
                        "xsid_script": self.xsid_script,
                        "baggage": self.baggage,
                        "sentry_trace": self.sentry_trace,
                        "conversationId": conversation_id,
                        "parentResponseId": parent_response,
                        "privateKey": self.keys["privateKey"]
                    }
                }
            else:
                # Enhanced rate limit detection with multiple patterns
                response_text = convo_request.text
                
                # Check for various rate limiting indicators
                rate_limit_indicators = [
                    'Grok is under heavy usage right now',
                    'under heavy usage',
                    'rate limit',
                    'too many requests',
                    'try again later',
                    'exceeded',
                    'limit exceeded',
                    'throttled'
                ]
                
                if any(indicator.lower() in response_text.lower() for indicator in rate_limit_indicators):
                    Log.Info("Detected rate limiting, implementing retry strategy")
                    return self._handle_rate_limit(message, extra_data)
                elif 'rejected by anti-bot rules' in response_text:
                    # Try fast retry first to bypass anti-bot
                    for fast_attempt in range(self.fast_retry_attempts):
                        delay = self._calculate_delay(fast_attempt, is_fast_retry=True)
                        Log.Info(f"Anti-bot detected (fast retry {fast_attempt + 1}/{self.fast_retry_attempts}). Waiting {delay:.2f}s before retry...")
                        time.sleep(delay)
                        
                        try:
                            new_grok = Grok(self.model, self.original_proxy)
                            result = new_grok.start_convo(message=message, extra_data=extra_data)
                            
                            if "error" not in result or "anti-bot" not in str(result.get("error", "")).lower():
                                return result
                        except Exception as e:
                            Log.Error(f"Anti-bot fast retry {fast_attempt + 1} failed: {str(e)}")
                            continue
                    
                    # If fast retry doesn't work, create new instance with fresh session to bypass anti-bot
                    new_grok = Grok(self.model, self.original_proxy)
                    return new_grok.start_convo(message=message, extra_data=extra_data)
                else:
                    Log.Error("Something went wrong")
                    Log.Error(response_text)
                    return {"error": response_text}
        else:
            conversation_data: dict = {
                'message': message,
                'modelName': self.model,
                'parentResponseId': extra_data["parentResponseId"],
                'disableSearch': False,
                'enableImageGeneration': True,
                'returnImageBytes': False,
                'returnRawGrokInXaiRequest': False,
                'fileAttachments': [],
                'enableImageStreaming': True,
                'imageGenerationCount': 2,
                'forceConcise': False,
                'toolOverrides': {},
                'enableSideBySide': True,
                'sendFinalMetadata': True,
                'customPersonality': '',
                'isReasoning': False,
                'webpageUrls': [],
                'metadata': {
                    'requestModelDetails': {
                        'modelId': self.model,
                    },
                    'request_metadata': {
                        'model': self.model,
                        'mode': self.mode,
                    },
                },
                'disableTextFollowUps': False,
                'disableArtifact': False,
                'isFromGrokFiles': False,
                'disableMemory': False,
                'forceSideBySide': False,
                'modelMode': self.model_mode,
                'isAsyncChat': False,
                'skipCancelCurrentInflightRequests': False,
                'isRegenRequest': False,
            }

            # Optimized timeout for faster response
            convo_request: requests.models.Response = self.session.post(f'https://grok.com/rest/app-chat/conversations/{extra_data["conversationId"]}/responses', json=conversation_data, timeout=15)

            if "modelResponse" in convo_request.text:
                response = conversation_id = parent_response = image_urls = None
                stream_response: list = []
                
                for response_dict in convo_request.text.strip().split('\n'):
                    data: dict = loads(response_dict)

                    token: str = data.get('result', {}).get('token')
                    if token:
                        stream_response.append(token)
                        
                    if not response and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('message'):
                        response: str = data['result']['response']['modelResponse']['message']

                    if not parent_response and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('responseId'):
                        parent_response: str = data['result']['modelResponse']['responseId']
                        
                    if not image_urls and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('generatedImageUrls', {}):
                        image_urls: str = data['result']['modelResponse']['generatedImageUrls']
                
                return {
                    "response": response,
                    "stream_response": stream_response,
                    "images": image_urls,
                    "extra_data": {
                        "anon_user": self.anon_user,
                        "cookies": self.session.cookies.get_dict(),
                        "actions": self.actions,
                        "xsid_script": self.xsid_script,
                        "baggage": self.baggage,
                        "sentry_trace": self.sentry_trace,
                        "conversationId": extra_data["conversationId"],
                        "parentResponseId": parent_response,
                        "privateKey": self.keys["privateKey"]
                    }
                }
            else:
                # Enhanced rate limit detection with multiple patterns
                response_text = convo_request.text
                
                # Check for various rate limiting indicators
                rate_limit_indicators = [
                    'Grok is under heavy usage right now',
                    'under heavy usage',
                    'rate limit',
                    'too many requests',
                    'try again later',
                    'exceeded',
                    'limit exceeded',
                    'throttled'
                ]
                
                if any(indicator.lower() in response_text.lower() for indicator in rate_limit_indicators):
                    Log.Info("Detected rate limiting, implementing retry strategy")
                    return self._handle_rate_limit(message, extra_data)
                elif 'rejected by anti-bot rules' in response_text:
                    # Create new instance with fresh session to bypass anti-bot
                    new_grok = Grok(self.model, self.original_proxy)
                    return new_grok.start_convo(message=message, extra_data=extra_data)
                else:
                    Log.Error("Something went wrong")
                    Log.Error(response_text)
                    return {"error": response_text}
    
    def continue_conversation(self, message: str, extra_data: dict) -> dict:
        """Continue an existing conversation"""
        # Set up the session with the provided extra_data
        self._load(extra_data)
        self.c_run: int = 1
        self.anon_user: str = extra_data["anon_user"]
        self.keys["privateKey"] = extra_data["privateKey"]
        self.c_request(self.actions[1])
        self.c_request(self.actions[2])
        xsid: str = Signature.generate_sign(f'/rest/app-chat/conversations/{extra_data["conversationId"]}/responses', 'POST', self.verification_token, self.svg_data, self.numbers)
        
        self.session.headers = self.headers.CONVERSATION
        self.session.headers.update({
            'baggage': self.baggage,
            'sentry-trace': f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            'x-statsig-id': xsid,
            'x-xai-request-id': str(uuid4()),
            'traceparent': f"00-{token_hex(16)}-{token_hex(8)}-00"
        })
        self.session.headers = Headers.fix_order(self.session.headers, self.headers.CONVERSATION)
        
        conversation_data: dict = {
            'message': message,
            'modelName': self.model,
            'parentResponseId': extra_data["parentResponseId"],
            'disableSearch': False,
            'enableImageGeneration': True,
            'returnImageBytes': False,
            'returnRawGrokInXaiRequest': False,
            'fileAttachments': [],
            'enableImageStreaming': True,
            'imageGenerationCount': 2,
            'forceConcise': False,
            'toolOverrides': {},
            'enableSideBySide': True,
            'sendFinalMetadata': True,
            'customPersonality': '',
            'isReasoning': False,
            'webpageUrls': [],
            'metadata': {
                'requestModelDetails': {
                    'modelId': self.model,
                },
                'request_metadata': {
                    'model': self.model,
                    'mode': self.mode,
                },
            },
            'disableTextFollowUps': False,
            'disableArtifact': False,
            'isFromGrokFiles': False,
            'disableMemory': False,
            'forceSideBySide': False,
            'modelMode': self.model_mode,
            'isAsyncChat': False,
            'skipCancelCurrentInflightRequests': False,
            'isRegenRequest': False,
        }

        # Increase timeout for handling rate limits
        convo_request: requests.models.Response = self.session.post(f'https://grok.com/rest/app-chat/conversations/{extra_data["conversationId"]}/responses', json=conversation_data, timeout=45)

        if "modelResponse" in convo_request.text:
            response = parent_response = image_urls = None
            stream_response: list = []
            
            for response_dict in convo_request.text.strip().split('\n'):
                data: dict = loads(response_dict)

                token: str = data.get('result', {}).get('token')
                if token:
                    stream_response.append(token)
                    
                if not response and data.get('result', {}).get('modelResponse', {}).get('message'):
                    response: str = data['result']['modelResponse']['message']

                if not parent_response and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('responseId'):
                    parent_response: str = data['result']['modelResponse']['responseId']
                    
                if not image_urls and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('generatedImageUrls', {}):
                    image_urls: str = data['result']['modelResponse']['generatedImageUrls']
            
            return {
                "response": response,
                "stream_response": stream_response,
                "images": image_urls,
                "extra_data": {
                    "anon_user": self.anon_user,
                    "cookies": self.session.cookies.get_dict(),
                    "actions": self.actions,
                    "xsid_script": self.xsid_script,
                    "baggage": self.baggage,
                    "sentry_trace": self.sentry_trace,
                    "conversationId": extra_data["conversationId"],
                    "parentResponseId": parent_response,
                    "privateKey": self.keys["privateKey"]
                }
            }
        else:
            # Enhanced rate limit detection with multiple patterns
            response_text = convo_request.text
            
            # Check for various rate limiting indicators
            rate_limit_indicators = [
                'Grok is under heavy usage right now',
                'under heavy usage',
                'rate limit',
                'too many requests',
                'try again later',
                'exceeded',
                'limit exceeded',
                'throttled'
            ]
            
            if any(indicator.lower() in response_text.lower() for indicator in rate_limit_indicators):
                Log.Info("Detected rate limiting, implementing retry strategy")
                return self._handle_rate_limit(message, extra_data)
            elif 'rejected by anti-bot rules' in response_text:
                # Try fast retry first to bypass anti-bot
                for fast_attempt in range(self.fast_retry_attempts):
                    delay = self._calculate_delay(fast_attempt, is_fast_retry=True)
                    Log.Info(f"Anti-bot detected (fast retry {fast_attempt + 1}/{self.fast_retry_attempts}). Waiting {delay:.2f}s before retry...")
                    time.sleep(delay)
                    
                    try:
                        new_grok = Grok(self.model, self.original_proxy)
                        result = new_grok.continue_conversation(message=message, extra_data=extra_data)
                        
                        if "error" not in result or "anti-bot" not in str(result.get("error", "")).lower():
                            return result
                    except Exception as e:
                        Log.Error(f"Anti-bot fast retry {fast_attempt + 1} failed: {str(e)}")
                        continue
                
                # If fast retry doesn't work, create new instance with fresh session to bypass anti-bot
                new_grok = Grok(self.model, self.original_proxy)
                return new_grok.continue_conversation(message=message, extra_data=extra_data)
            else:
                Log.Error("Something went wrong")
                Log.Error(response_text)
                return {"error": response_text}