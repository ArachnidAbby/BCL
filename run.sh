
python3 src/Main.py
llc -filetype=obj src/testing/output.ll
gcc src/testing/output.o -no-pie -o src/testing/output
./src/testing/output