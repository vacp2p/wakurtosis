system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def set_up_graphana(prometheus_service):
    # Set up grafana
    CONFIGURATION_GRAFANA = "/etc/grafana/"
    DASHBOARDS_GRAFANA = "/var/lib/grafana/dashboards/"
    CUSTOMIZATION_GRAFANA = "/usr/share/grafana/"

    config_id = upload_files(
        src=system_variables.GRAFANA_CONFIGURATION_PATH
    )
    customization_id = upload_files(
        src=system_variables.GRAFANA_CUSTOMIZATION_PATH
    )
    dashboard_id = upload_files(
        src=system_variables.GRAFANA_DASHBOARD_PATH
    )

    prometheus_url = prometheus_service.ip_address + ":" + str(
        prometheus_service.ports[system_variables.PROMETHEUS_PORT_ID].number)
    prometheus_info = {"prometheus_url": prometheus_url}

    # template
    template = """
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

    artifact_id = render_templates(
        config={
            "datasources.yaml": struct(
                template=template,
                data=prometheus_info,
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
                CONFIGURATION_GRAFANA: config_id,
                # customization_id: CUSTOMIZATION_GRAFANA,
                DASHBOARDS_GRAFANA: dashboard_id,
                "/etc/grafana/provisioning/datasources/": artifact_id
            }
        )
    )

    return grafana_service
