# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)


def set_up_prometheus(plan, network_topology):
    # Create targets.json
    targets_artifact_id = create_prometheus_targets(plan, network_topology)

    # Set up prometheus
    artifact_id = plan.upload_files(
        src=vars.PROMETHEUS_CONFIGURATION_PATH,
        name="prometheus_config"
    )

    add_service_config = ServiceConfig(
        image=vars.PROMETHEUS_IMAGE,
        ports={
            vars.PROMETHEUS_PORT_ID: PortSpec(
                number=vars.CONTAINER_PROMETHEUS_TCP_PORT, transport_protocol="TCP")
        },
        files={
            vars.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS: artifact_id,
            vars.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS_2: targets_artifact_id
        },
        cmd=[
            "--config.file=" + vars.CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS +
            vars.CONTAINER_CONFIGURATION_FILE_NAME_PROMETHEUS
        ]
    )

    prometheus_service = plan.add_service(
        name=vars.PROMETHEUS_SERVICE_NAME,
        config=add_service_config
    )

    return prometheus_service


def create_prometheus_targets(plan, network_topology):
    # get ip and ports of all nodes

    template_data = files.generate_template_node_targets(network_topology,
                                                         vars.PROMETHEUS_PORT_ID, "targets")

    template = templates.get_prometheus_template()

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TARGETS_FILE_NAME_PROMETHEUS: struct(
                template=template,
                data=template_data,
            )
        },
        name=vars.PROMETHEUS_TEMPLATE_NAME
    )

    return artifact_id
