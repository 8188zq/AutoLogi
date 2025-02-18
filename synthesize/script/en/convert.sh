cd /AutoLogi/synthesize

NAME="example"
python -m convert.convert_en --name=$NAME 
python -m convert.deduplicate --name=$NAME 
