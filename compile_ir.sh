llc -filetype=obj tests/output.ll
gcc tests/output.o -no-pie -o tests/output -L/lib/ -l:libSDL2.so
tests/output