# AutoLogi

This repository contains the official implementation for the paper **"AutoLogi: Automated Generation of Logic Puzzles for Evaluating Reasoning Abilities of Large Language Models"** [paper url].

## DATA

### Benchmark Data
AutoLogi benchmark evaluation data is available in:
- `/testing-data/AutoLogi_en.jsonl` (English)
- `/testing-data/AutoLogi_cn.jsonl` (Chinese)

### Training Data
Located in `/training-data/`:
- `source_corpus_cn.jsonl` and `source_corpus_en.jsonl`: Source data as input
- `synthesized_data_cn.jsonl` and `synthesized_data_en.jsonl`: Data generated from source corpus using our synthesis method
- SFT and DPO data obtained through rejection-sampling using:
  - Qwen2.5-72b-instruct
  - Qwen2.5-7b-instruct

For detailed implementation of the rejection-sampling process, please refer to our paper.

## Evaluation

### Quick Start

#### Step 1: Generate Model Responses
Use the 'prompt' field in `/testing-data/AutoLogi_en.jsonl` and `/testing-data/AutoLogi_cn.jsonl` as input for your model. Store the model outputs in the 'gen' field as a list containing a string. See `/model_output/qwen2.5_72b_instruct_response_example_en.jsonl` for the expected format.

#### Step 2: Run Evaluation
```bash
cd /AutoLogi
python evaluation/eval.py --input_data ./model_output/qwen2.5_72b_instruct_response_example_en.jsonl --output_dir ./eval_results/
```
## Synthesize
The implementation of our synthesis method is in /synthsize/.

**Note**: Before running the code, you need to modify the API configurations according to your setup in function `utils\call_openai` and set the corresponding environment variables(`OPENAI_API_KEY`).

### Quick Start

Run the complete pipeline:
```bash
cd AutoLogi 
bash ./synthesize/script/en/pipeline.sh
```

### Stage-wise Execution

You can also run individual stages, such as:

```bash
# Stage 3 Reduce
bash /synthesize/script/en/delete.sh

# Stage 3 Augmentation  
bash /synthesize/script/en/add.sh
```

### Create Custom AutoLogi Training Set

1. Place your data in  `./training-data/` following the format of source_corpus_en.jsonl (must include 'question' and 'id' fields)
2. Modify the NAME variable in `./synthesize/script/en/pipeline.sh` to match your dataset name
3. Run the pipeline as described above
