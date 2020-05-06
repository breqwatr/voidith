""" lib for arcus services """

import voithos.lib.aws.ecr as ecr


def pull(service):
    """ Pull one of the arcus services from ECR and retag it """
    services = {
        "api": "breqwatr/arcus-api",
        "client": "breqwatr/arcus-client",
        "mgr": "breqwatr/arcus-mgr",
    }
    image = services[service]
    ecr.pull(image)
