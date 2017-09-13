lambda_package: venv
	mkdir -p lambda_package
	./venv/bin/pip install -r requirements.txt -t lambda_package

lambda.zip: lambda_package
	rm -f lambda.zip
	zip lambda *.py
	cd lambda_package && zip -r ../lambda.zip .

venv:
	virtualenv venv

clean:
	rm -rf lambda_package
	rm -rf venv


docker_build:
	docker run -v ${PWD}:/app/ --rm oremj/lambda_builder_python36 sh -c 'cd app && make clean lambda.zip'

.PHONY: docker_build
