hx_util docker
==============

You don't have to install locally to use hx_util; you can run the cli from a
[docker](https://docs.docker.com/get-started/get-docker/) container.

    # clone this repo
    $> git clone https://github.com/Colin-Fredericks/hx_util.git

    # build the image
    $> cd hx_util
    $> docker build --tag hxutil --file docker/Dockerfile .
    ...

    # run the cli in the container
    # in this example, we are using an export that is located in
    # hx_util/files/course-export.tar.gz
    $> docker run -v $(pwd):/opt/exports hxutil wrapper_hx_util.sh /opt/exports/files/course-export.tar.gz

Note that, for the docker container, the export input has to be tarred and gzipped.
The result is generated in hx_util/files/result.tar.gz

