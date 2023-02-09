# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)
templates = import_module(system_variables.TEMPLATES_MODULE)


def set_up_prometheus(plan, services):
    # Create targets.json
    targets_artifact_id = create_prometheus_targets(plan, services)

    # Set up prometheus
    artifact_id = plan.upload_files(
        src=system_variables.PROMETHEUS_CONFIGURATION_PATH,
        name="prometheus_config"
    )

    prometheus_service = plan.add_service(
        service_name=system_variables.PROMETHEUS_SERVICE_ID,
        config=ServiceConfig(
            image=system_variables.PROMETHEUS_IMAGE,
            ports={
                system_variables.PROMETHEUS_PORT_ID: PortSpec(
                    number=system_variables.CONTAINER_PROMETHEUS_TCP_PORT, transport_protocol="TCP")
            },
            files={
                system_variables.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS: artifact_id,
                system_variables.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS_2: targets_artifact_id
            },
            cmd=[
                "--config.file=" + system_variables.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS +
                system_variables.CONTAINER_CONFIGURATION_FILE_NAME_PROMETHEUS
            ]
        )
    )

    return prometheus_service


def create_prometheus_targets(plan, services):
    # get ip and ports of all nodes
    template_data = files.generate_template_node_targets(services,
                                                         system_variables.PROMETHEUS_PORT_ID)

    template = templates.get_prometheus_template()

    artifact_id = plan.render_templates(
        config={
            system_variables.CONTAINER_TARGETS_FILE_NAME_PROMETHEUS: struct(
                template=template,
                data=template_data,
            )
        },
        name="prometheus_targets"
    )

    return artifact_id
