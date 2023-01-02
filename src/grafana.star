# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)

# todo pasar templates a .star
def get_prometheus_template_content():
    # template
    prometheus_template = """
        apiVersion: 1
        datasources:
            - name: Prometheus
              type: prometheus
              access: proxy
              org_id: 1
              url: http://{{.prometheus_url}}
              is_default: true
              version: 1
              editable: true
    """

    return prometheus_template


def set_up_graphana(prometheus_service):
    config_id, customization_id, dashboard_id = files.upload_files_grafana()
    prometheus_data = files.generate_template_prometheus_url(prometheus_service)
    prometheus_template = get_prometheus_template_content()

    artifact_id = render_templates(
        config={
            "datasources.yaml": struct(
                template=prometheus_template,
                data=prometheus_data,
            )
        }
    )

    grafana_service = add_service(
        service_id="grafana",
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
