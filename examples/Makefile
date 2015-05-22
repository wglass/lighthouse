WORKDIR=${PWD}

all: docker-images

sdist:
	@echo "generating source dist for lighthouse..."
	cd ${WORKDIR}/../ && python setup.py sdist -d ${WORKDIR} && cd ${WORKDIR}

docker-images: sdist zk-image cache-image webapp-image multiapp-image widgets-image sprockets-image client-image partner-image proxy-image

zk-image:
	@echo "Creating zookeeper docker image...".
	docker build -t "lighthouse.examples.zk" -f dockerfiles/Dockerfile.zookeeper .

base-image:
	@echo "Creating base node image..."
	docker build -t "lighthouse.examples.base" -f dockerfiles/Dockerfile.base .

cache-image: base-image
	@echo "Creating cache docker image..."
	docker build -t "lighthouse.examples.cache" -f dockerfiles/Dockerfile.cache .

webapp-image: base-image
	@echo "Creating webapp docker image..."
	docker build -t "lighthouse.examples.webapp" -f dockerfiles/Dockerfile.webapp .

multiapp-image: base-image
	@echo "Creating multiapp docker image..."
	docker build -t "lighthouse.examples.multiapp" -f dockerfiles/Dockerfile.multiapp .

widgets-image: base-image
	@echo "Creating widgets docker image..."
	docker build -t "lighthouse.examples.widgets" -f dockerfiles/Dockerfile.widgets .

sprockets-image: base-image
	@echo "Creating sprockets docker image..."
	docker build -t "lighthouse.examples.sprockets" -f dockerfiles/Dockerfile.sprockets .

proxy-image: base-image
	@echo "Creating proxy docker image..."
	docker build -t "lighthouse.examples.proxy" -f dockerfiles/Dockerfile.proxy .

partner-image:
	@echo "Creating partner docker image..."
	docker build -t "lighthouse.examples.partner" -f dockerfiles/Dockerfile.partner .

client-image: base-image
	@echo "Creating client docker image..."
	docker build -t "lighthouse.examples.client" -f dockerfiles/Dockerfile.client .

clean:
	rm lighthouse-*.tar.gz
