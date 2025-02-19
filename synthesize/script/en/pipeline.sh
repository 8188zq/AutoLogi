NAME="source_corpus_en"
cd /AutoLogi/synthesize
# verify 1
python -m verify.verify_step1 --name=$NAME 

# verify 2 & traverse
MAX_VERIFY_TIME=2
MAX_TRAVERSE_TIME=3
j=1
# 2*3
for i in 1 2; do
    # echo "$SAVE_PATH$i.$j.jsonl"
    python -m verify.verify_step2 --name=$NAME --verify_turn_id=$i --traverse_turn_id=$j --max_traverse_time=$MAX_TRAVERSE_TIME
    
    while [ $j -lt $((MAX_TRAVERSE_TIME+1)) ]; do
        # echo "Iteration $i.$j"
        python -m traverse.traverse --name=$NAME --verify_turn_id=$i --traverse_turn_id=$j
        j=$((j+1))
    done
    j=1
done
python ./traverse/get_final_res.py --name=$NAME --max_verify_time=$MAX_VERIFY_TIME --max_traverse_time=$MAX_TRAVERSE_TIME

# delete
python -m delete.delete --name=$NAME 

# add
python -m add.add_preprocess --name=$NAME 
python -m add.add --name=$NAME 

# convert
python -m convert.convert --name=$NAME 
python -m convert.deduplicate --name=$NAME 