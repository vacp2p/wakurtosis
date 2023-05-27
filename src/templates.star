# GRAFANA
def get_prometheus_template_content_for_grafana():
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

# PROMETHEUS
def  get_prometheus_template():
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

    return template


def get_enr_template():
    template = "{{.enr}}"

    return template