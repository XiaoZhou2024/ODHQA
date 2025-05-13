import os
import json
import torch
import torch.nn as nn
from tqdm import tqdm
from datasets import load_dataset
from torch.nn import CrossEntropyLoss
from peft import LoraConfig, get_peft_model
from torch.utils.tensorboard import SummaryWriter
from modelscope import AutoModelForCausalLM, AutoTokenizer
import logging
from datetime import datetime
from config.prompt_config import *
from utils.utils import *

# Set CUDA device
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ----------------------------- Logging Configuration -----------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------- Data Path and Loading -----------------------------
json_path = './my_lora_dataset.json'

def read_json(path):
    """
    Reads a JSON file and returns the loaded data.
    """
    with open(path, 'r', encoding='utf-8') as f:
        datas = json.load(f)
    return datas

datas = read_json(json_path)

# ----------------------------- Model and Tokenizer Loading -----------------------------
device = "cuda:0"
model_path = './Qwen2.5-7B-Instruct'

if not os.path.exists(model_path):
    logger.error(f"Model directory {model_path} does not exist. Please check the path.")
    raise FileNotFoundError(f"Model directory {model_path} not found.")
else:
    logger.info(f"Model directory {model_path} found.")

logger.info("Loading pre-trained model...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise e

logger.info("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_path)
logger.info("Tokenizer loaded successfully.")

# ----------------------------- Data Preprocessing -----------------------------
def preprocess(tokenizer, batch_messages):
    """
    Preprocesses a batch of messages for model input and target creation.
    Pads sequences to the same length and generates input, target, and mask tensors.
    """
    input_list = []
    target_list = []

    im_start = tokenizer('<|im_start|>').input_ids
    im_end = tokenizer('<|im_end|>').input_ids
    newline = tokenizer('\n').input_ids
    pad = tokenizer('<|endoftext|>').input_ids
    ignore = [-100]

    for group in batch_messages:
        input_ids = []
        target_ids = []
        for msg in group:
            role = tokenizer(msg['role']).input_ids
            content = tokenizer(msg['content']).input_ids
            if msg['role'] in ['system', 'user']:
                ignore_parts = role + newline + content
                input_ids += im_start + ignore_parts + im_end + newline
                target_ids += im_start + ignore * len(ignore_parts) + im_end + newline
            else:
                ignore_parts = role + newline
                input_ids += im_start + ignore_parts + content + im_end + newline
                target_ids += im_start + ignore * len(ignore_parts) + content + im_end + newline
        input_list.append(input_ids)
        target_list.append(target_ids)

    # Padding
    max_len = max([len(ids) for ids in input_list])
    for input_ids, target_ids in zip(input_list, target_list):
        input_ids += pad * (max_len - len(input_ids))
        target_ids += ignore * (max_len - len(target_ids))
    batch_input_ids = torch.tensor(input_list, dtype=torch.long)
    batch_target_ids = torch.tensor(target_list, dtype=torch.long)
    batch_mask = batch_input_ids.ne(pad[0]).type(torch.long)

    return batch_input_ids, batch_target_ids, batch_mask

# ----------------------------- Chat Function -----------------------------
def chat(prompt):
    """
    Generates a response from the model given a user prompt.
    """
    messages = [
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

def get_chat_template(input, output):
    """
    Returns a chat template in the format required by the model.
    """
    return [{"role": "user", "content": input}, {"role": "assistant", "content": output}]

# ----------------------------- Loss Calculation -----------------------------
def compute_loss(input):
    """
    Computes the cross-entropy loss for a batch of inputs.
    """
    batch_input_ids, batch_target_ids, batch_mask = preprocess(tokenizer, input)
    model_outputs = model(batch_input_ids.to(device))
    logits = model_outputs.logits[:, :-1, :]
    targets = batch_target_ids[:, 1:].to(device)

    loss_fn = CrossEntropyLoss()
    loss = loss_fn(logits.reshape(-1, logits.size(2)), targets.reshape(-1))
    loss_value = loss.item()
    return loss_value

def calculate_individual_loss(input):
    """
    Computes the average loss for each sequence in the batch individually.
    """
    batch_input_ids, batch_target_ids, batch_mask = preprocess(tokenizer, input)
    model_outputs = model(batch_input_ids.to(device))
    logits = model_outputs.logits
    targets = batch_target_ids.to(device)

    loss_fn = CrossEntropyLoss(reduction='none')
    logits = logits[:, :-1, :]
    targets = targets[:, 1:]

    logits_flat = logits.reshape(-1, logits.size(-1))
    targets_flat = targets.reshape(-1)
    token_losses = loss_fn(logits_flat, targets_flat)
    token_losses = token_losses.view(logits.size(0), logits.size(1))
    individual_losses = token_losses.mean(dim=1)
    return torch.tensor(individual_losses, requires_grad=True)

# ----------------------------- LoRA Configuration -----------------------------
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ----------------------------- Training Loop -----------------------------
writer = SummaryWriter(log_dir='./logs')
model.train()

chunk_size = 4
epochs = 4

for epoch in range(epochs):
    for i in tqdm(range(0, len(datas), chunk_size)):
        chunks = datas[i:i + chunk_size]
        input_to_result = []
        input_to_reasons = []
        input_and_reasons_to_result = []

        for chunk in chunks:
            sub_table = chunk['sub_table']
            sub_content = chunk['sub_content']
            query = chunk['qa']['question']
            question_type = chunk['qa']['question_type']
            answer = chunk['qa']['answer']
            program = chunk['qa']['program']
            think_process = chunk['think_process']

            if isinstance(answer, list):
                answer = str(answer)

            if question_type == 'arithmetic':
                input_want_reason = arithmetic_input_want_reason_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query)
                input = arithmetic_input_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query)
                input_with_reason = arithmetic_input_with_reason_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query, thinking_process=think_process)

                input_to_reasons.append(get_chat_template(input_want_reason, think_process))
                input_and_reasons_to_result.append(get_chat_template(input_with_reason, program))
                input_to_result.append(get_chat_template(input, program))
            else:
                input_want_reason = span_selection_input_want_reason_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query)
                input = span_selection_input_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query)
                input_with_reason = span_selection_input_with_reason_template.format(
                    sub_table=sub_table, sub_content=sub_content, query=query, thinking_process=think_process)
                input_to_reasons.append(get_chat_template(input_want_reason, think_process))
                input_and_reasons_to_result.append(get_chat_template(input_with_reason, answer))
                input_to_result.append(get_chat_template(input, answer))

        # Loss comparison for reward model
        matrix_01 = [1 if compute_loss([a]) > compute_loss([b]) else 0 for a, b in zip(input_to_result, input_and_reasons_to_result)]
        print("matrix_01:")
        print(matrix_01)

        update_input_to_reasons = [row if flag == 1 else [] for flag, row in zip(matrix_01, input_to_reasons)]

        input_to_reasons_loss = calculate_individual_loss(update_input_to_reasons)
        print("input_to_reasons_loss:")
        print(input_to_reasons_loss)
        input_and_reasons_to_result_loss = calculate_individual_loss(input_and_reasons_to_result)
        print("input_and_reasons_to_result_loss")
        print(input_and_reasons_to_result_loss)
        total_loss = input_to_reasons_loss + input_and_reasons_to_result_loss
        print("total_loss:")
        print(total_loss)

        total_loss = total_loss.sum()

        optimizer = torch.optim.SGD(model.parameters())
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

    model.save_pretrained(f"./output/{epoch+1}")
    tokenizer.save_pretrained(f"./output/{epoch+1}")
    writer.close()