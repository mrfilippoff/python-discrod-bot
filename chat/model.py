import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# based on https://huggingface.co/microsoft/DialoGPT-medium
class ChatBot:
  def __init__(self, model_name='microsoft/DialoGPT-small'):
    self.model, self.tokenizer = self.load_model(model_name)
    self.chat_history_ids = None
    
  def load_model(self, model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return model, tokenizer

  def get_reply(self, user_message):
    message_ids = self.tokenizer.encode(user_message + self.tokenizer.eos_token, return_tensors='pt')

    if self.chat_history_ids is not None:
      message_ids = torch.cat([self.chat_history_ids, message_ids], dim=-1)

    self.chat_history_ids = self.model.generate(
      message_ids,
      pad_token_id=self.tokenizer.eos_token_id, 
      do_sample=True, 
      max_new_tokens=1500, 
      top_k=100, 
      top_p=0.95,
      temperature=0.8
    )
    
    return self.tokenizer.decode(
      self.chat_history_ids[:, message_ids.shape[-1]:][0], 
      skip_special_tokens=True,
    )
