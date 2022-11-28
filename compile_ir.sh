llc -filetype=obj tests/output.ll
gcc tests/output.o -no-pie -o tests/output 
tests/output