develop: setup-git install-deps

install-deps:
	pip install -e "file://`pwd`#egg=responses[tests]"

setup-git:
	pip install "pre-commit>=1.8.2,<1.9.0"
	pre-commit install
	git config branch.autosetuprebase always

test: develop lint
	@echo "Running Python tests"
	py.test .
	@echo ""

lint:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 .
	@echo ""
