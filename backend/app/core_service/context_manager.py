import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.database.models.message import Message
from app.database.models.memory import Memory
from app.core_service.token_counter import BaseTokenCounter, SimpleTokenCounter

logger = logging.getLogger("jarvis.context_manager")

class ContextManager:
    def __init__(self, token_counter: BaseTokenCounter = None):
        self.token_counter = token_counter or SimpleTokenCounter()
        self.max_tokens = settings.AI_MAX_TOKENS

    def build_context(self, system_prompt: str, history: List[Message], new_request: str, relevant_memories: List[Memory] = None, document_context: str = "") -> List[Dict[str, Any]]:
        """
        Builds the context array for the LLM.
        Priority:
        1. System Prompt + Memories
        2. RAG Document Context
        3. New User Request
        4. Recent Messages
        """
        mem_text = ""
        if relevant_memories:
            mem_text = "\n\nRelevant user memories:\n" + "\n".join([f"- {m.content}" for m in relevant_memories])
            
        if document_context:
            mem_text += "\n\n" + document_context
            
        sys_msg = {"role": "system", "content": system_prompt + mem_text}
        new_msg = {"role": "user", "content": new_request}


        
        # Calculate base tokens (System + New Request)
        base_tokens = self.token_counter.count_messages([sys_msg, new_msg])
        
        available_budget = self.max_tokens - base_tokens
        if available_budget <= 0:
            logger.warning("System prompt and new request exceed max token budget. LLM request might fail or be truncated.")
            # Even if it exceeds, we must return the bare minimum
            return [sys_msg, new_msg]

        # Select recent messages and fit them into the budget
        selected_history = []
        current_history_tokens = 0
        
        # Reverse history to start from the most recent
        reversed_history = list(reversed(history))
        
        for msg in reversed_history:
            # Reconstruct dictionary with specific formatting
            msg_dict = {"role": msg.role}
            if msg.role == "tool":
                msg_dict["content"] = msg.content or ""
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                if msg.tool_name:
                    msg_dict["name"] = msg.tool_name
            elif msg.role == "assistant" and msg.tool_calls:
                msg_dict["content"] = msg.content
                msg_dict["tool_calls"] = msg.tool_calls
            else:
                msg_dict["content"] = msg.content or ""

            msg_tokens = self.token_counter.count_messages([msg_dict])
            
            if current_history_tokens + msg_tokens > available_budget:
                break # Budget exhausted
                
            selected_history.insert(0, msg_dict) # Prepend to maintain correct order
            current_history_tokens += msg_tokens
            
            # Enforce RECENT_MESSAGE_LIMIT if it's set > 0
            if settings.RECENT_MESSAGE_LIMIT > 0 and len(selected_history) >= settings.RECENT_MESSAGE_LIMIT:
                break
                
        final_messages = [sys_msg] + selected_history + [new_msg]
        
        logger.info(f"Context built: {len(final_messages)} messages, approx {base_tokens + current_history_tokens} tokens")
        return final_messages
