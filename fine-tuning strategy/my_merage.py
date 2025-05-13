from transformers import AutoModelForCausalLM, AutoTokenizer  
from peft import PeftModel  
import torch

# ------------------- Path Configuration -------------------
base_model_path = "./Qwen2.5-7B-Instruct/"                  # Base model path
lora_model_path = "./output/"      # Fine-tuned LoRA weights path
output_model_path = "./my_merage/output/"    # Output path for merged model

device = torch.device("cuda:0")

# ------------------- Load Base Model and Tokenizer -------------------
print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(base_model_path, trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)

# ------------------- Load LoRA Weights -------------------
print("Loading LoRA weights...")
lora_model = PeftModel.from_pretrained(base_model, lora_model_path)

# ------------------- Merge LoRA Weights into Base Model -------------------
print("Merging LoRA weights into base model...")
merged_model = lora_model.merge_and_unload()

# ------------------- Save Merged Model and Tokenizer -------------------
print(f"Saving merged model to {output_model_path}...")
merged_model.save_pretrained(output_model_path)
tokenizer.save_pretrained(output_model_path)

# ------------------- Validation: Load Merged Model for Inference -------------------
print("Loading merged model for validation...")
model = AutoModelForCausalLM.from_pretrained(
    output_model_path,
    torch_dtype="auto",
    trust_remote_code=True
).to(device)

tokenizer = AutoTokenizer.from_pretrained(output_model_path, trust_remote_code=True)

# ------------------- Inference Chat Function -------------------
def chat(prompt):
    """
    Generates a model response given a user prompt.

    Args:
        prompt (str): The user input for the assistant.

    Returns:
        str: The generated assistant response.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response

# ------------------- Inference Test -------------------
print("Running inference test...")
prompt = """  
Please refer to the Sub Table, Sub Content and Query to output the Thinking Process of deriving the answer, without providing the answer itself.  

### Sub_table  
table_0: Movements in Intangible Assets: Rights and Licenses, Internally Generated Software, and Software Under Development for the Years Ended June 30, 2019 and 2018  
|  | Rights and licenses | Internally generated software | Software under development | Total |  
| --- | --- | --- | --- | --- |  
| Opening net book amount at 1 July 2017 | 43 | 442 | 8,053 | 8,538 |  
| Closing net book amount | 13 | 6,385 | 6,509 | 12,907 |  
### Sub_content  
None  
### Query  
What was the difference between the total opening and closing net book account for intangible assets like rights, licenses, software, and development costs at NEXTDC in 2018?  
"""
res = chat(prompt)
print(res)