# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)
templates = import_module(system_variables.TEMPLATES_MODULE)


def set_up_grafana(prometheus_service):
    config_id, customization_id, dashboard_id = files.prepare_artifact_files_grafana()
    prometheus_data = files.generate_template_prometheus_url(prometheus_service)
    prometheus_template = templates.get_prometheus_template_content_for_grafana()

    artifact_id = render_templates(
        config={
            system_variables.CONTAINER_DATASOURCES_FILE_NAME_GRAFANA: struct(
                template=prometheus_template,
                data=prometheus_data,
            )
        }
    )

    grafana_service = add_service(
        service_id=system_variables.GRAFANA_SERVICE_ID,
        config=struct(
            image=system_variables.GRAFANA_IMAGE,
            ports={
                system_variables.GRAFANA_PORT_ID: PortSpec(number=system_variables.GRAFANA_TCP_PORT,
                                                           transport_protocol="TCP")
            },
            files={
                system_variables.CONTAINER_CONFIGURATION_GRAFANA: config_id,
                # customization_id: CUSTOMIZATION_GRAFANA,
                system_variables.CONTAINER_DASHBOARDS_GRAFANA: dashboard_id,
                system_variables.CONTAINER_DATASOURCES_GRAFANA: artifact_id
            }
        )
    )

    return grafana_service
