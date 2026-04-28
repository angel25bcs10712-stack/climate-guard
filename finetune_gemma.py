# ClimateGuard: Fine-tuning Gemma 4 for Disaster Response
# This script is designed to run on a Kaggle T4 GPU.

"""
Dependencies:
!pip install unsloth
!pip install --no-deps xformers trl peft accelerate bitsandbytes
"""

from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. Load Model & Tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/gemma-4-4b-it-bnb-4bit", # Using the 4-bit quantized version
    max_seq_length = 2048,
    load_in_4bit = True,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
)

# 3. Training Data Prompt
prompt = """<start_of_turn>user
{}
Context: {}<end_of_turn>
<start_of_turn>model
{}<end_of_turn>"""

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    contexts     = examples["context"]
    responses    = examples["response"]
    texts = []
    for instruction, context, response in zip(instructions, contexts, responses):
        text = prompt.format(instruction, context, response)
        texts.append(text)
    return { "text" : texts, }

# 4. Load Dataset
dataset = load_dataset("json", data_files="training_data.json", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True)

# 5. Trainer Setup
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = 2048,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Increased steps for 30+ examples
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        output_dir = "outputs",
    ),
)

# 6. Start Training
trainer.train()

# 7. Save the Fine-tuned Model for Ollama
model.save_pretrained_gguf("climateguard_gemma_4b", tokenizer, quantization_method = "q4_k_m")
print("Model saved and ready for Ollama deployment.")
