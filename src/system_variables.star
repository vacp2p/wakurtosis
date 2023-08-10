# IMAGES
NWAKU_IMAGE = "statusteam/nim-waku:nwaku-trace3"
GOWAKU_IMAGE = "gowaku"
NOMOS_IMAGE = "nomos-node"

# If changing this, you'll likely need to change it as well in gennet
ID_STR_SEPARATOR = "-"

NODE_CONFIG_FILE_LOCATION = "github.com/logos-co/wakurtosis/config/topology_generated/"
RUN_SCRIPT_FILE = "github.com/logos-co/wakurtosis/bash-utils/run_waku_node.sh"
CONFIG_FILE_LOCATION = "github.com/logos-co/wakurtosis/config/"
CONTAINER_NODE_CONFIG_FILE_LOCATION = "/node/configuration_file/"
CONTAINER_NODE_SCRIPT_RUN_LOCATION = "/opt/"
GENERAL_ENTRYPOINT = ["/bin/sh", "-c"]
CONFIG_FILE_STARLARK_PARAMETER = "config_file"

# Config file keys
KURTOSIS_KEY = "kurtosis"
WLS_KEY = "wls"
INTERCONNECT_NODES = "interconnect_nodes"
INTERCONNECTION_BATCH_KEY = "interconnection_batch"

# Waku Configuration
WAKU_RPC_PORT_ID = "rpc"
WAKU_RPC_PORT_PROTOCOL = "TCP"
WAKU_RPC_PORT_NUMBER = 8545
WAKU_LIBP2P_PORT_ID = "libp2p"
WAKU_LIBP2P_PORT_PROTOCOL = "TCP"
WAKU_LIBP2P_PORT = 60000
WAKU_DISCV5_PORT_ID = "discv5"
WAKU_DISCV5_PORT_NUMBER = 9000
WAKU_DISCV5_PORT_PROTOCOL = "UDP"

WAKUNODE_CONFIGURATION_FILE_FLAG = "--config-file="
WAKUNODE_PORT_SHIFT_FLAG = "--ports-shift="
# NWAKU_ENTRYPOINT = "/usr/bin/wakunode --rpc-address=0.0.0.0 --metrics-server-address=0.0.0.0 --log-level=TRACE"
NWAKU_SCRIPT_ENTRYPOINT = "run_waku_node.sh"
GOWAKU_ENTRYPOINT = "/usr/bin/waku --rpc-address=0.0.0.0 --metrics-server-address=0.0.0.0"
NOMOS_ENTRYPOINT = "/usr/bin/nomos-node"
NOMOS_PORT_SHIFT_FLAG = "--ports-shift="
NOMOS_CONTAINER_CONFIG_FILE_LOCATION = '/etc/nomos/config.yaml'

# Nomos Configuration
NOMOS_RPC_PORT_PROTOCOL = "TCP"
NOMOS_RPC_PORT_NUMBER = 8080
NOMOS_LIBP2P_PORT_PROTOCOL = "TCP"
NOMOS_LIBP2P_PORT_ID = "libp2p"
NOMOS_LIBP2P_PORT = 3000
NOMOS_NET_INFO_URL = "/network/info"
NOMOS_NET_CONN_URL = "/network/conn"
NOMOS_CARNOT_INFO = "/carnot/info"
NOMOS_PROMETHEUS_PORT_NUMBER = 8080

# Prometheus Configuration
PROMETHEUS_IMAGE = "prom/prometheus:latest"
PROMETHEUS_SERVICE_NAME = "prometheus"
PROMETHEUS_PORT_ID = "prom"
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
GRAFANA_PORT_ID = "grafana" + ID_STR_SEPARATOR + "tcp"
GRAFANA_TCP_PORT = 3000

CONTAINER_CONFIGURATION_GRAFANA = "/etc/grafana/"
CONTAINER_DASHBOARDS_GRAFANA = "/var/lib/grafana/dashboards/"
CONTAINER_CUSTOMIZATION_GRAFANA = "/usr/share/grafana/"
CONTAINER_DATASOURCES_GRAFANA = "/etc/grafana/provisioning/datasources/"
CONTAINER_DATASOURCES_FILE_NAME_GRAFANA = "datasources.yaml"

# Gennet topology Keys
GENNET_KEY = "gennet"
GENNET_IMAGE = "gennet"
GENNET_SERVICE_NAME = "gennet"
GENNET_CONFIG_ARTIFACT_NAME = "gennet-config"
GENNET_NODES_KEY = "nodes"
GENNET_PORT_SHIFT_KEY = "port_shift"
GENNET_ALL_CONTAINERS_KEY = "containers"
GENNET_IMAGE_KEY = "image"
GENNET_CONFIG_KEY = "node_config"
GENNET_NODE_CONTAINER_KEY = "container_id"
GENNET_STATIC_NODES_KEY = "static_nodes"
GENNET_GOWAKU_IMAGE_VALUE = "go-waku"
GENNET_NWAKU_IMAGE_VALUE = "nim-waku"
GENNET_NOMOS_IMAGE_VALUE = "nomos"

PEER_ID_KEY = "peer_id"
IP_KEY = "ip_address"
KURTOSIS_IP_KEY = "kurtosis_ip"
PORTS_KEY = "ports"

# WLS Configuration
WLS_IMAGE = "wls:0.0.1"
WLS_SERVICE_NAME = "wls"
WLS_CONFIG_PATH = "/wls/config/"
WLS_TARGETS_PATH = "/wls/targets/"
WLS_TOMLS_PATH = "/wls/tomls/"
WLS_TOPOLOGY_PATH = "/wls/network_topology/"
WLS_CONFIG_FILE_FLAG = "--config_file"
WLS_TOPOLOGY_FILE_FLAG = "--topology_file"
WLS_CONFIG_ARTIFACT_NAME = "config_file"
WLS_TOPOLOGY_ARTIFACT_NAME = "wls_topology"
WLS_TOMLS_ARTIFACT_NAME = "tomls_artifact"

CONTAINER_WLS_CONFIGURATION_FILE_NAME = "config.json"
CONTAINER_TOPOLOGY_FILE_NAME_WLS = "network_data.json"

#collectnet configuration
COLLECTNET_IMAGE = "collectnet:latest"
COLLECTNET_SERVICE_NAME = "CollectNet"
COLLECTNET_CONFIG_PATH = "/collectnet/config/"
COLLECTNET_TARGETS_PATH = "/collectnet/targets/"
COLLECTNET_NETDATA_PATH = "/collectnet/network_topology/"
COLLECTNET_CONFIG_FILE_FLAG = "--config_file"
COLLECTNET_NETDATA_FILE_FLAG = "--network-data-file"
COLLECTNET_SAMPLING_INTERVAL_FLAG = "--sampling-interval"
COLLECTNET_DEBUG_FLAG = "--no-debug"
COLLECTNET_CONFIG_ARTIFACT_NAME = "config_file_artefact"
COLLECTNET_NETDATA_ARTIFACT_NAME = "network_data_artefact"


CONTAINER_COLLECTNET_CONFIG_FILE_NAME = "config.json"
CONTAINER_COLLECTNET_NETDATA_FILE_NAME = "network_data.json"

# Waku RPC methods
POST_RELAY_MESSAGE_METHOD = "post_waku_v2_relay_v1_message"
GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"
GET_PEERS_METHOD = "get_waku_v2_admin_v1_peers"

# Import locations
WAKU_MODULE = "github.com/logos-co/wakurtosis/src/waku.star"
NODE_BUILDERS_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/node_builders.star"
DISPATCHERS_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/dispatchers.star"
WAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/waku_builder.star"
NWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/nwaku_builder.star"
GOWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/gowaku_builder.star"
NOMOS_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/nomos_builder.star"
PROMETHEUS_MODULE = "github.com/logos-co/wakurtosis/src/monitoring/prometheus.star"
GRAFANA_MODULE = "github.com/logos-co/wakurtosis/src/monitoring/grafana.star"
ARGUMENT_PARSER_MODULE = "github.com/logos-co/wakurtosis/src/arguments_parser.star"
FILE_HELPERS_MODULE = "github.com/logos-co/wakurtosis/src/file_helpers.star"
TEMPLATES_MODULE = "github.com/logos-co/wakurtosis/src/templates.star"
WLS_MODULE = "github.com/logos-co/wakurtosis/src/wls.star"
COLLECTNET_MODULE = "github.com/logos-co/wakurtosis/src/collectnet.star"
CALL_PROTOCOLS = "github.com/logos-co/wakurtosis/src/call_protocols.star"
NOMOS_MODULE = "github.com/logos-co/wakurtosis/src/nomos.star"
ASSERTIONS_MODULE = "github.com/logos-co/wakurtosis/src/assertions.star"


TEST_ARGUMENTS_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_arguments_parser.star"
TEST_FILES_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_file_helpers.star"
TEST_WAKU_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_waku_methods.star"
TEST_WLS_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_wls.star"
TEST_NODE_BUILDERS_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/tests/test_node_builders.star"
TEST_WAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/tests/test_waku_builder.star"
TEST_GOWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/tests/test_gowaku_builder.star"
TEST_NWAKU_BUILDER_MODULE = "github.com/logos-co/wakurtosis/src/node_builders/types/tests/test_nwaku_builder.star"

# Default main starlark arguments
TOPOLOGIES_LOCATION = "github.com/logos-co/wakurtosis/config/topology_generated/"
DEFAULT_TOPOLOGY_FILE = "network_data.json"
TEST_FILES_LOCATION = "github.com/logos-co/wakurtosis/config/test_files/"
DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE = "test_network_data.json"
DEFAULT_CONFIG_FILE = "github.com/logos-co/wakurtosis/config/config.json"
