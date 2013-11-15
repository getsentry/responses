develop:
	pip install -e . --use-mirrors
	make install-test-requirements

install-test-requirements:
	pip install "file://`pwd`#egg=responses[tests]" --use-mirrors

test: develop lint
	@echo "Running Python tests"
	py.test .
	@echo ""

lint:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 .
	@echo ""
