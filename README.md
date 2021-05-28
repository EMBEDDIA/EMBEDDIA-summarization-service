# basic-xl-user-comments

Model: https://huggingface.co/sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens

Paper: https://www.aclweb.org/anthology/2021.hackashop-1.13/

## To run locally (without docker) on port 8080:

```
 $ pip install -r requirements.txt
 $ python server.py 8080
```

## To run with Docker on port 8080

```
 $ sudo docker build -t my_test_app .
 $ sudo docker run -p 8082:8080 my_test_app
```

## Linting, etc.

The project comes with a bunch of linting (style checking, etc) tools pre-
configured. You can manually run the linters with

```$ isort -rc . && black . && flake8 .```

Development becomes easier, if you configure git to automatically run the
linters whenever you try to commit using a pre-commit hook. You can
install the relevant pre-commit hooks with `pre-commit install` (with the
virtual environment loaded).
