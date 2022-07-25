env/bin/activate: requirements.txt
	python3 -m venv env
	./env/bin/pip3 install -r requirements.txt

run: env/bin/activate
	./env/bin/python3 src/Main.py hmm

build: env/bin/activate
	./env/bin/python3 -m ursina.build

vs-build: syntax_highlighting/package.json
	cd syntax_highlighting/
	vsce package

# build sphinx html docs
sphinx-build: env/bin/activate
	./env/bin/sphinx-build -b html docs/source/ docs/build/html

# clean sphinx build files
sphinx-clean: env/bin/activate
	rm -rf docs/build

clean:
	rm -rf __pycache__
	rm -rf env  