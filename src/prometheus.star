# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)


def set_up_prometheus(services):
    # Create targets.json
    targets_artifact_id = create_prometheus_targets(services)

    # Set up prometheus
    CONFIG_LOCATION = "/test"
    CONFIG_LOCATION2 = "/tmp"
    artifact_id = upload_files(
        src=system_variables.PROMETHEUS_CONFIGURATION_PATH
    )

    prometheus_service = add_service(
        service_id="prometheus",
        config=struct(
            image=system_variables.PROMETHEUS_IMAGE,
            ports={
                system_variables.PROMETHEUS_PORT_ID: PortSpec(number=9090, transport_protocol="TCP")
            },
            files={
                CONFIG_LOCATION: artifact_id,
                CONFIG_LOCATION2: targets_artifact_id
            },
            cmd=[
                "--config.file=" + CONFIG_LOCATION + "/prometheus.yml"
            ]
        )
    )

    return prometheus_service


def create_prometheus_targets(services):
    # get ip and ports of all nodes
    template_data = files.generate_template_targets_with_port(services, system_variables.PROMETHEUS_PORT_ID)

    # template
    template = """
    [
        {
            "labels": {
                "job": 
                "wakurtosis"
            }, 
            "targets" : {{.targets}} 
        }
    ]
    """

    artifact_id = render_templates(
        config={
            "targets.json": struct(
                template=template,
                data=template_data,
            )
        }
    )

    return artifact_id
