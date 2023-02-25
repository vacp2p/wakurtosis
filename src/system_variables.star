# Waku Configuration
NWAKU_IMAGE = "statusteam/nim-waku:nwaku-trace"
GOWAKU_IMAGE = "gowaku"

RPC_PORT_ID = "rpc"

NODE_CONFIG_FILE_LOCATION = "github.com/logos-co/wakurtosis/config/topology_generated/"
CONTAINER_NODE_CONFIG_FILE_LOCATION = "/node/configuration_file/"
GENERAL_ENTRYPOINT = ["/bin/sh", "-c"]
CONFIG_FILE_STARLARK_PARAMETER = "config_file"

# Config file keys
KURTOSIS_KEY = "kurtosis"
WLS_KEY = "wls"
INTERCONNECTION_BATCH_KEY = "interconnection_batch"

# Waku Configuration
WAKU_RPC_PORT_PROTOCOL = "TCP"
WAKU_RPC_PORT_NUMBER = 8545
WAKU_LIBP2P_PORT_ID = "libp2p"
WAKU_LIBP2P_PORT_PROTOCOL = "TCP"
WAKU_LIBP2P_PORT = 60000

WAKUNODE_CONFIGURATION_FILE_FLAG = "--config-file="
WAKUNODE_PORT_SHIFT_FLAG = "--ports-shift="
NWAKU_ENTRYPOINT = "/usr/bin/wakunode --rpc-address=0.0.0.0 --metrics-server-address=0.0.0.0 --log-level=TRACE"
GOWAKU_ENTRYPOINT = "/usr/bin/waku --rpc-address=0.0.0.0 --metrics-server-address=0.0.0.0"
NOMOS_ENTRYPOINT = ["/usr/bin/nomos-node"]
NOMOS_CONTAINER_CONFIG_FILE_LOCATION = '/etc/nomos/config.yml'

# Nomos Configuration
NOMOS_IMAGE = "nomos"
NOMOS_HTTP_PORT_ID = "http"
NOMOS_HTTP_PORT = 8080
NOMOS_LIBP2P_PORT_ID = "libp2p"
NOMOS_LIBP2P_PORT = 3000
NOMOS_SETUP_WAIT_TIME = "5"
NOMOS_NET_INFO_URL = "/network/info"
NOMOS_NET_CONN_URL = "/network/conn"

# Prometheus Configuration
PROMETHEUS_IMAGE = "prom/prometheus:latest"
PROMETHEUS_SERVICE_NAME = "prometheus"
PROMETHEUS_PORT_ID = "prometheus"
PROMETHEUS_PORT_PROTOCOL = "TCP"
PROMETHEUS_PORT_NUMBER = 8008
PROMETHEUS_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/prometheus.yml"
PROMETHEUS_TEMPLATE_NAME = "prometheus_targets"


CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS = "/test/"
CONTAINER_CONFIGURATION_LOCATION_PROMETHEUS_2 = "/tmp/"
CONTAINER_CONFIGURATION_FILE_NAME_PROMETHEUS = "prometheus.yml"
CONTAINER_TARGETS_FILE_NAME_PROMETHEUS = "targets.json"
CONTAINER_PROMETHEUS_TCP_PORT = 9090

# Grafana Configuration
GRAFANA_IMAGE = "grafana/grafana:latest"
GRAFANA_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/config/"
GRAFANA_CUSTOMIZATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/customizations/"
GRAFANA_DASHBOARD_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/dashboards/"

GRAFANA_SERVICE_NAME = "grafana"
GRAFANA_PORT_ID = "grafana_tcp"
GRAFANA_TCP_PORT = 3000

CONTAINER_CONFIGURATION_GRAFANA = "/etc/grafana/"
CONTAINER_DASHBOARDS_GRAFANA = "/var/lib/grafana/dashboards/"
CONTAINER_CUSTOMIZATION_GRAFANA = "/usr/share/grafana/"
CONTAINER_DATASOURCES_GRAFANA = "/etc/grafana/provisioning/datasources/"
CONTAINER_DATASOURCES_FILE_NAME_GRAFANA = "datasources.yaml"

# Gennet topology Keys
GENNET_NODES_KEY = "nodes"
GENNET_ALL_CONTAINERS_KEY = "containers"
GENNET_IMAGE_KEY = "image"
GENNET_CONFIG_KEY = "node_config"
GENNET_NODE_CONTAINER_KEY = "container_id"
GENNET_STATIC_NODES_KEY = "static_nodes"
GENNET_GOWAKU_IMAGE_VALUE = "go-waku"
GENNET_NWAKU_IMAGE_VALUE = "nim-waku"

PEER_ID_KEY = "peer_id"
IP_KEY = "ip_address"
PORTS_KEY = "ports"

# WLS Configuration
WLS_IMAGE = "wls:0.0.1"
WLS_SERVICE_NAME = "wls"
WLS_CONFIG_PATH = "/wls/config"
WLS_TARGETS_PATH = "/wls/targets"
WLS_TOMLS_PATH = "/wls/tomls"
WLS_CMD = ["python3", "wls.py"]

CONTAINER_WLS_CONFIGURATION_FILE_NAME = "wls.yml"
CONTAINER_TARGETS_FILE_NAME_WLS = "targets.json"

# Waku RPC methods
POST_RELAY_MESSAGE_METHOD = "post_waku_v2_relay_v1_message"
GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"
GET_PEERS_METHOD = "get_waku_v2_admin_v1_peers"

# Import locations
WAKU_MODULE = "github.com/logos-co/wakurtosis/src/waku.star"
NODE_BUILDERS_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/node_builders.star"
WAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/waku_builder.star"
NWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/nwaku_builder.star"
GOWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/gowaku_builder.star"
PROMETHEUS_MODULE = "github.com/logos-co/wakurtosis/src/monitoring/prometheus.star"
GRAFANA_MODULE = "github.com/logos-co/wakurtosis/src/monitoring/grafana.star"
ARGUMENT_PARSER_MODULE = "github.com/logos-co/wakurtosis/src/arguments_parser.star"
FILE_HELPERS_MODULE = "github.com/logos-co/wakurtosis/src/file_helpers.star"
TEMPLATES_MODULE = "github.com/logos-co/wakurtosis/src/templates.star"
WLS_MODULE = "github.com/logos-co/wakurtosis/src/wls.star"
CALL_PROTOCOLS = "github.com/logos-co/wakurtosis/src/call_protocols.star"
NOMOS_MODULE = "github.com/logos-co/wakurtosis/src/nomos.star"

TEST_ARGUMENTS_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_arguments_parser.star"
TEST_FILES_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_file_helpers.star"
TEST_NODE_BUILDERS_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_node_builders.star"
TEST_WAKU_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_waku_methods.star"

# Default main starlark arguments
TOPOLOGIES_LOCATION = "github.com/logos-co/wakurtosis/config/topology_generated/"
DEFAULT_TOPOLOGY_FILE = "network_data.json"
TEST_FILES_LOCATION = "github.com/logos-co/wakurtosis/config/test_files/"
DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE = "test_network_data.json"
DEFAULT_CONFIG_FILE = "github.com/logos-co/wakurtosis/config/config.json"

# Default Simulation Parameters
SIMULATION_TIME = 300
MESSAGE_RATE = 25
MIN_PACKET_SIZE = 1
MAX_PACKET_SIZE = 1024
