## Dev-testing CLI/library with MiniO

This project presents sample `ListMinioBucketObjectsCommand` command to demonstrate possible integration with MiniO

In order to dev-test such commands locally when you're developing them, you will need to run these external services, and one of the options is to run them using Docker

If you are developing on Windows, you might look into [WSL 2](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-containers)

Another option is running Linux VM locally, on your VPS, or on a separate machine (e.g. old laptop) in your network

We'll look into how to run MiniO locally on an available Linux system next.


## Running MiniO in Docker

First, make sure 'Docker' is installed in your system:
```
user@ubuntu:~$ docker --version
Docker version 27.2.0, build 3ab4256
```

You can use these few handy commands to set up and run docker image of MiniO:
```
mkdir -p ~/minio/data
docker run \
   -p 9000:9000 \
   -p 9001:9001 \
   --name minio \
   -v ~/minio/data:/data \
   -e "MINIO_ROOT_USER=admin" \
   -e "MINIO_ROOT_PASSWORD=admin123" \
   quay.io/minio/minio server /data --console-address ":9001"
```

Then you can start/stop this container using
```
docker container start minio
docker container stop minio
```

If your docker is executed in a Linux VM in the same network, you can go ahead and check MiniO web-console.

You'll need to find your VM's IP (using `ifconfig`), and then open 'your_linux_vm_ip:9001' in your browser (it might look like '192.168.1.6:9001')

If done correctly - you'll be greeted with MiniO login form - use MINIO_ROOT_USER/MINIO_ROOT_PASSWORD used in set up script (default ones were admin/admin123)

Use web-ui to create new bucket with name `test-bucket` and add few files into it's root

Update [params for running Minio](../tests/data/minio/params.yaml) with your Minio IP and credentials

Then you can run `python qubership_cli_samples list-minio-files --context_path=./minio/context.yaml` - it should list objects in your bucket in `result.yaml`