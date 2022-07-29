llc -filetype=obj test.ll
gcc test.o -no-pie -o test
./test