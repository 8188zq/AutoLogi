NAME="source_corpus_cn"

cd /AutoLogi/synthesize

# verify 1
echo "Starting: Verify Step 1"
python -m verify.verify_step1_cn --name=$NAME 

# verify 2 & traverse
MAX_VERIFY_TIME=2
MAX_TRAVERSE_TIME=3
j=1
# 2*3
for i in 1 2; do
    echo "Starting: Verify Step 2, Iteration $i.$j"
    python -m verify.verify_step2_cn --name=$NAME --verify_turn_id=$i --traverse_turn_id=$j --max_traverse_time=$MAX_TRAVERSE_TIME
    
    while [ $j -lt $((MAX_TRAVERSE_TIME+1)) ]; do
        echo "Starting: Traverse, Iteration $i.$j"
        python -m traverse.traverse_cn --name=$NAME --verify_turn_id=$i --traverse_turn_id=$j
        j=$((j+1))
    done
    j=1
done

echo "Starting: Get Final Results"
python ./traverse/get_final_res_cn.py --name=$NAME --max_verify_time=$MAX_VERIFY_TIME --max_traverse_time=$MAX_TRAVERSE_TIME

# delete
echo "Starting: Delete"
python -m delete.delete_cn --name=$NAME 

# add
echo "Starting: Add Preprocess"
python -m add.add_preprocess_cn --name=$NAME 
echo "Starting: Add"
python -m add.add_cn --name=$NAME 

# convert
echo "Starting: Convert"
python -m convert.convert_cn --name=$NAME 
echo "Starting: Deduplicate"
python -m convert.deduplicate_cn --name=$NAME
