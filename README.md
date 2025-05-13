# ODHQA: Open-Domain Hybrid Data Numerical Reasoning Question Answering Dataset

## Introduction

**ODHQA** (Open-Domain Hybrid Data Numerical Reasoning Question Answering Dataset) is a benchmark dataset designed for open-domain Question Answering (QA) tasks that require advanced numerical reasoning over hybrid data types, such as combinations of text, tables, and numbers. ODHQA aims to promote the development and evaluation of QA systems with the ability to understand, retrieve, and reason over varied and complex data contexts.

Download the dataset here: [ODHQA Dataset (Google Drive)](https://drive.google.com/drive/folders/1koQcYExt5-GeAg_bXzN91wvXn2e96wZf?usp=drive_link)

## Citation

If you use ODHQA in your research, please cite our paper:

> Authors. "ODHQA: An Open-Domain Hybrid Data Numerical Reasoning Question Answering Dataset." (Year). [arXiv link or conference link]

## Dataset Structure

The ODHQA repository is organized as follows:

```
.
├── data/
│   ├── train_dataset.json      # Training set
│   ├── dev_dataset.json        # Development/validation set
│   └── test_dataset.json       # Test set
├── tools/
│   ├── expression_calculator.py  # Arithmetic expression parsing and evaluation
│   ├── operations_utils.py       # Sub-table/content extraction and JSON utilities
│   └── ...
├── config/
│   └── prompt_config.py        # Prompt templates for content extraction
├── fine-tuning strategy/
│   ├── my_lora.py              # LoRA fine-tuning script
│   └── my_merage.py            # Merge LoRA weights into base model
├── ODHybrid/
│   └── ODHybrid.py             # Main pipeline combining retrieval & LLM reasoning
└── README.md                   # Project information
```

### Main Files and Folders

- **data/**: Includes all dataset splits: `train_dataset.json`, `dev_dataset.json`, and `test_dataset.json`.
- **scripts/**: Contains utility scripts for data processing and numerical reasoning.
  - `expression_calculator.py`: Arithmetic expression parsing and calculation.
  - `operations_utils.py`: Functions for sub-table/sub-content extraction and JSON data handling.
- **config/prompt_config.py**: Prompt templates for sub-table and content generation.
- **fine-tuning strategy/**: Scripts for LoRA fine-tuning and merging LoRA weights into base models.
  - `my_lora.py`: LoRA fine-tuning.
  - `my_merage.py`: Weight merging.
- **ODHybrid/**: Entry point for the end-to-end QA system—retrieval, prompt construction, and inference.
  - `ODHybrid.py`: Entry point for the end-to-end QA system—retrieval, prompt construction, and inference.

## Getting Started

### Installation

Install the required dependencies by running:

```bash
pip install torch transformers peft datasets tqdm loguru langchain langchain-openai
```

### Data Preparation

1. **Download the dataset** from the link above and place the files in the `data/` directory.
2. **Configure your environment**: Set up your `.env` file with the correct API base URL and secret key for your LLM provider.

### Running the Inference Pipeline

To run the complete ODHybrid:

```bash
python ODHybrid.py
```

Inference results will be saved to `results.json` in the project root.

### Fine-Tuning with LoRA

To fine-tune your model using LoRA, navigate to the relevant directory and execute:

```bash
cd fine-tuning\ strategy
python my_lora.py
```

### Merging LoRA Weights

After fine-tuning, merge the LoRA weights with your base model:

```bash
cd fine-tuning\ strategy
python my_merage.py
```

## Download

You can either **clone the repository**:

```bash
git clone https://github.com/your-username/ODHQA-dataset.git
```

Or **download the dataset directly** from our [Google Drive](https://drive.google.com/drive/folders/1koQcYExt5-GeAg_bXzN91wvXn2e96wZf?usp=drive_link).

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Contact

For questions or suggestions, please contact [author@email.com] or open an issue in the repository.

---

