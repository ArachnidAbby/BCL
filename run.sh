
python3 Main.py
llc -filetype=obj output.ll
gcc output.o -no-pie -o output
./output