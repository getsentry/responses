develop: setup-git install-deps

install-deps:
	pip install -e "file://`pwd`#egg=responses[tests]"

install-pre-commit:
	pip install "pre-commit>=1.10.1,<1.11.0"

setup-git: install-pre-commit
	pre-commit install
	git config branch.autosetuprebase always

test: develop lint
	@echo "Running Python tests"
	py.test .
	@echo ""

lint: install-pre-commit
	@echo "Linting Python files"
	pre-commit run -a
	@echo ""
