override FILE = console_cube.bcl

env/bin/activate: requirements.txt
	python3.11 -m venv env 
	./env/bin/pip3.11 install -r requirements.txt

run: env/bin/activate
	./env/bin/python3.11 src/main.py compile tests/$(FILE)

run-dev: env/bin/activate
	./env/bin/python3.11 src/main.py compile tests/$(FILE) --dev

unittest: env/bin/activate
	./env/bin/python3.11 tests/Basic_Test.py

compile: env/bin/activate
	./env/bin/python3.11 -m nuitka --follow-imports --experimental=python3.11 src/main.py

vs-build: syntax_highlighting/package.json
	cd syntax_highlighting/; \
	  vsce package

profile_cpu: env/bin/activate
	./env/bin/python3.11 -m cProfile -o tests/random/program.prof src/main.py hmmmm
	./env/bin/snakeviz tests/random/program.prof

# build sphinx html docs
sphinx-build: env/bin/activate
	./env/bin/sphinx-build -b html docs/source/ docs/build/html

# clean sphinx build files
sphinx-clean: env/bin/activate
	rm -rf docs/build

clean:
	rm -rf __pycache__
	rm -rf env
	rm -rf main.build/