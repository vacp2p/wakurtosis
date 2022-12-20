# Waku Configuration
WAKU_IMAGE = "statusteam/nim-waku:deploy-status-prod"
WAKU_RPC_PORT_ID = "rpc"
WAKU_TCP_PORT = 8545
WAKU_LIBP2P_PORT_ID = "libp2p"
WAKU_LIBP2P_PORT = 60000

# Prometheus Configuration
PROMETHEUS_IMAGE = "prom/prometheus:latest"
PROMETHEUS_PORT_ID = "prometheus"
PROMETHEUS_TCP_PORT = 8008
PROMETHEUS_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/prometheus.yml"

# Grafana Configuration
GRAFANA_IMAGE = "grafana/grafana:latest"
GRAFANA_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/config/"
GRAFANA_CUSTOMIZATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/customizations/"
GRAFANA_DASHBOARD_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/dashboards/"

GRAFANA_PORT_ID = "grafana"
GRAFANA_TCP_PORT = 3000

# Waku RPC methods
POST_RELAY_MESSAGE = "post_waku_v2_relay_v1_message"
GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"

GENERAL_TOML_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/kurtosis-module/starlark/config_files/waku_general.toml"
GENERAL_TOML_CONFIGURATION_NAME = "waku_general.toml"


def create_waku_id(other_node_info):
    ip = other_node_info["service"].ip_address
    port = other_node_info["service"].ports[WAKU_LIBP2P_PORT_ID].number
    node_id = other_node_info["id"]

    return '["/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + node_id + '"]'


def connect_wakunode_to_peer(service_id, port_id, other_node_info):
    method = CONNECT_TO_PEER_METHOD

    params = create_waku_id(other_node_info)

    response = send_json_rpc(service_id, port_id, method, params)

    print(response)


def send_waku_message(service_id, topic):
    topic = topic
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = '"' + topic + '"' + ", " + waku_message
    response = send_json_rpc(service_id, WAKU_RPC_PORT_ID, POST_RELAY_MESSAGE, params)
    print(response)


def send_json_rpc(service_id, port_id, method, params, extract={}):
    recipe = struct(
        service_id=service_id,
        port_id=port_id,
        endpoint="",
        method="POST",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}',
        extract=extract
    )

    response = request(recipe=recipe)

    return response


def get_wakunode_id(service_id, port_id):
    extract = {"waku_id": '.result.listenAddresses | .[0] | split("/") | .[-1]'}

    response = send_json_rpc(service_id, port_id, GET_WAKU_INFO_METHOD, "", extract)

    print(response)

    return response["extract.waku_id"]


def get_toml_configuration_artifact(wakunode_name, same_toml_configuration):
    if same_toml_configuration:
        artifact_id = upload_files(
            src=GENERAL_TOML_CONFIGURATION_PATH
        )
        file_name = GENERAL_TOML_CONFIGURATION_NAME
    else:
        artifact_id = upload_files(
            src="github.com/logos-co/wakurtosis/kurtosis-module/starlark/config_files/" + wakunode_name + ".toml"
        )
        file_name = wakunode_name + ".toml"

    return artifact_id, file_name


def instantiate_waku_nodes(waku_topology, same_toml_configuration):
    services = {}

    # Get up all waku nodes
    for wakunode_name in waku_topology.keys():
        CONFIG_LOCATION = "/tmp"  # todo maybe not good idea to use /tmp

        artifact_id, configuration_file = get_toml_configuration_artifact(wakunode_name, same_toml_configuration)

        waku_service = add_service(
            service_id=wakunode_name,
            config=struct(
                image=WAKU_IMAGE,
                ports={
                    WAKU_RPC_PORT_ID: PortSpec(number=WAKU_TCP_PORT, transport_protocol="TCP"),
                    PROMETHEUS_PORT_ID: PortSpec(number=PROMETHEUS_TCP_PORT, transport_protocol="TCP"),
                    WAKU_LIBP2P_PORT_ID: PortSpec(number=WAKU_LIBP2P_PORT,
                                                  transport_protocol="TCP"),
                },
                files={
                    CONFIG_LOCATION: artifact_id
                },
                entrypoint=[
                    "/usr/bin/wakunode", "--rpc-address=0.0.0.0",
                    "--metrics-server-address=0.0.0.0"
                ],
                cmd=[
                    "--topics=" + waku_topology[wakunode_name]["topics"],
                    "--metrics-server=True",
                    "--config-file=" + CONFIG_LOCATION + "/" + configuration_file,
                ]
            )
        )

        waku_info = {}
        exec_recipe = struct(
            service_id=wakunode_name,
            command=["sleep", "10"]
        )
        exec(exec_recipe)
        id = get_wakunode_id(wakunode_name, WAKU_RPC_PORT_ID)
        waku_info["id"] = id
        waku_info["service"] = waku_service

        services[wakunode_name] = waku_info

    return services


def interconnect_waku_nodes(topology_information, services):
    # Interconnect them
    for wakunode_name in topology_information.keys():
        peers = topology_information[wakunode_name]["static_nodes"]

        # todo: change to do only one rpc call
        for peer in peers:
            connect_wakunode_to_peer(wakunode_name, WAKU_RPC_PORT_ID, services[peer])


def send_test_messages(topology_information):
    for wakunode_name in topology_information.keys():
        # send message in topic
        for i in range(50):
            exec_recipe = struct(
                service_id=wakunode_name,
                command=["sleep", "0.5"]
            )
            exec(exec_recipe)
            send_waku_message(wakunode_name, "test")


def generate_template_data(services):
    template_data = {}
    node_data = []
    for wakunode_name in services.keys():
        node_data.append(
            '"' + services[wakunode_name]["service"].ip_address + ":" + str(services[wakunode_name]["service"].ports[
                                                                                PROMETHEUS_PORT_ID].number) + '"')

    data_as_string = ",".join(node_data)
    test = "[" + data_as_string + "]"

    template_data["targets"] = test

    return template_data


def create_prometheus_targets(services):
    # get ip and ports of all nodes
    template_data = generate_template_data(services)

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


def set_up_prometheus(services):
    # Create targets.json
    targets_artifact_id = create_prometheus_targets(services)

    # Set up prometheus
    CONFIG_LOCATION = "/test"
    CONFIG_LOCATION2 = "/tmp"
    artifact_id = upload_files(
        src=PROMETHEUS_CONFIGURATION_PATH
    )

    prometheus_service = add_service(
        service_id="prometheus",
        config=struct(
            image=PROMETHEUS_IMAGE,
            ports={
                PROMETHEUS_PORT_ID: PortSpec(number=9090, transport_protocol="TCP")
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


def set_up_graphana(prometheus_service):
    # Set up grafana
    CONFIGURATION_GRAFANA = "/etc/grafana/"
    DASHBOARDS_GRAFANA = "/var/lib/grafana/dashboards/"
    CUSTOMIZATION_GRAFANA = "/usr/share/grafana/"

    config_id = upload_files(
        src=GRAFANA_CONFIGURATION_PATH
    )
    customization_id = upload_files(
        src=GRAFANA_CUSTOMIZATION_PATH
    )
    dashboard_id = upload_files(
        src=GRAFANA_DASHBOARD_PATH
    )

    prometheus_url = prometheus_service.ip_address + ":" + str(prometheus_service.ports[PROMETHEUS_PORT_ID].number)
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
            image=GRAFANA_IMAGE,
            ports={
                GRAFANA_PORT_ID: PortSpec(number=GRAFANA_TCP_PORT, transport_protocol="TCP")
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


def run(args):
    waku_topology = read_file(src="github.com/logos-co/wakurtosis/kurtosis-module/starlark/waku_test_topology.json")

    same_toml_configuration = args.same_toml_configuration
    # waku_topology = json.decode(waku_topology)

    waku_topology = {
        "waku_0": {
            "ports_shift": 0,
            "topics": "test",
            "static_nodes": [
                "waku_1",
            ]
        },
        "waku_1": {
            "ports_shift": 1,
            "topics": "test",
            "static_nodes": [
                "waku_0"
            ]
        }
    }

    services = instantiate_waku_nodes(waku_topology, same_toml_configuration)

    # Set up prometheus + graphana
    prometheus_service = set_up_prometheus(services)
    set_up_graphana(prometheus_service)

    interconnect_waku_nodes(waku_topology, services)

    send_test_messages(waku_topology)
