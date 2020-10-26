BASE_IMG_NAME = nam012
BUILD_CMD = docker build --network=host
DOCKERFILE = Dockerfile

blender:
	$(BUILD_CMD) -f $(DOCKERFILE) -t $(BASE_IMG_NAME)-blender .

clean: 
	docker image rm $(BASE_IMG_NAME)-blender

