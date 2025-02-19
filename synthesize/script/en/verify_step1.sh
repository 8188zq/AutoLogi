INPUT_PATH="./training-data/en_example.jsonl"
SAVE_PATH="/AutoLogi/synthesize/verify/output_en/example2.jsonl"
cd /AutoLogi/synthesize
python -m verify.verify_step1 --input_path=$INPUT_PATH --save_path=$SAVE_PATH