# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)


def set_up_grafana(plan, prometheus_service):
    config_id, customization_id, dashboard_id = files.prepare_artifact_files_grafana(plan,
        "grafana_config", "grafana_customization", "grafana_dashboard")
    prometheus_data = files.generate_template_prometheus_url(prometheus_service)
    prometheus_template = templates.get_prometheus_template_content_for_grafana()

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_DATASOURCES_FILE_NAME_GRAFANA: struct(
                template=prometheus_template,
                data=prometheus_data,
            )
        },
        name="grafana_target"
    )

    add_service_config = ServiceConfig(
        image=vars.GRAFANA_IMAGE,
        ports={
            vars.GRAFANA_PORT_ID: PortSpec(number=vars.GRAFANA_TCP_PORT,
                                           transport_protocol="TCP")
        },
        files={
            vars.CONTAINER_CONFIGURATION_GRAFANA: config_id,
            # customization_id: CUSTOMIZATION_GRAFANA,
            vars.CONTAINER_DASHBOARDS_GRAFANA: dashboard_id,
            vars.CONTAINER_DATASOURCES_GRAFANA: artifact_id
        }
    )

    grafana_service = plan.add_service(
        name=vars.GRAFANA_SERVICE_NAME,
        config=add_service_config
    )

    return grafana_service
