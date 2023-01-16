# Waku Configuration
WAKU_IMAGE = "statusteam/nim-waku:019f357d"
WAKU_RPC_PORT_ID = "rpc"
WAKU_TCP_PORT = 8545
WAKU_LIBP2P_PORT_ID = "libp2p"
WAKU_LIBP2P_PORT = 60000
WAKU_SETUP_WAIT_TIME = "5"

WAKU_CONFIGURATION_FILES_LOCATION = "github.com/logos-co/wakurtosis/config/waku_config_files/"
WAKU_CONFIGURATION_FILE_EXTENSION = ".toml"

WAKU_CONFIG_FILE_CONTAINER_LOCATION = "/waku/configuration_file"
WAKU_ENTRYPOINT = ["/usr/bin/wakunode", "--rpc-address=0.0.0.0", "--metrics-server-address=0.0.0.0"]

# Prometheus Configuration
PROMETHEUS_IMAGE = "prom/prometheus:latest"
PROMETHEUS_SERVICE_ID = "prometheus"
PROMETHEUS_PORT_ID = "prometheus_tcp"
PROMETHEUS_TCP_PORT = 8008
PROMETHEUS_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/prometheus.yml"

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

GRAFANA_SERVICE_ID = "grafana"
GRAFANA_PORT_ID = "grafana_tcp"
GRAFANA_TCP_PORT = 3000

CONTAINER_CONFIGURATION_GRAFANA = "/etc/grafana/"
CONTAINER_DASHBOARDS_GRAFANA = "/var/lib/grafana/dashboards/"
CONTAINER_CUSTOMIZATION_GRAFANA = "/usr/share/grafana/"
CONTAINER_DATASOURCES_GRAFANA = "/etc/grafana/provisioning/datasources/"
CONTAINER_DATASOURCES_FILE_NAME_GRAFANA = "datasources.yaml"

# WSL Configuration
WSL_IMAGE = "wsl:0.0.1"
WSL_SERVICE_ID = "wsl"
WSL_CONFIG_PATH = "/wsl/config"
WSL_TARGETS_PATH = "/wsl/targets"
CONTAINER_WSL_CONFIGURATION_FILE_NAME = "wsl.yml"
CONTAINER_TARGETS_FILE_NAME_WSL = "targets.json"

# Gennet Configuration
GENNET_IMAGE = "gennet:0.0.1"
GENNET_SERVICE_ID = "gennet"
GENNET_CONFIG_PATH = "/gennet/config"
CONTAINER_GENNET_CONFIGURATION_FILE_NAME = "gennet.yml"

# Waku RPC methods
POST_RELAY_MESSAGE = "post_waku_v2_relay_v1_message"
GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"
GET_PEERS_METHOD = "get_waku_v2_admin_v1_peers"

GENERAL_TOML_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/config/waku_config_files/waku_general.toml"
GENERAL_TOML_CONFIGURATION_NAME = "waku_general.toml"

# Import locations
WAKU_MODULE = "github.com/logos-co/wakurtosis/src/waku_methods.star"
PROMETHEUS_MODULE = "github.com/logos-co/wakurtosis/src/prometheus.star"
GRAFANA_MODULE = "github.com/logos-co/wakurtosis/src/grafana.star"
ARGUMENT_PARSER_MODULE = "github.com/logos-co/wakurtosis/src/arguments_parser.star"
FILE_HELPERS_MODULE = "github.com/logos-co/wakurtosis/src/file_helpers.star"
TEMPLATES_MODULE = "github.com/logos-co/wakurtosis/src/templates.star"
WSL_MODULE = "github.com/logos-co/wakurtosis/src/wsl.star"
GENNET_MODULE = "github.com/logos-co/wakurtosis/src/gennet.star"

TEST_ARGUMENTS_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_arguments_parser.star"
TEST_FILES_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_file_helpers.star"
TEST_WAKU_MODULE = "github.com/logos-co/wakurtosis/src/tests/test_waku_methods.star"

# Default main starlark arguments
SAME_TOML_CONFIGURATION_ARGUMENT_NAME = "same_toml_configuration"
SAME_TOML_CONFIGURATION_DEFAULT_ARGUMENT_VALUE = True

TOPOLOGY_FILE_NAME_ARGUMENT_NAME = "topology_file"
DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE = "waku_test_topology_small.json"
TOPOLOGIES_LOCATION = "github.com/logos-co/wakurtosis/config/network_topology/"
DEFAULT_TOPOLOGY_FILE = "network_data.json"

NUMBER_TEST_MESSAGES = 50
DELAY_BETWEEN_TEST_MESSAGE = "0.5"

# Default Simulation Parameters
SIMULATION_TIME = 300
MESSAGE_RATE = 25
MIN_PACKET_SIZE = 1
MAX_PACKET_SIZE = 1024

# Default Network / Topology parameters
NUM_NODES = 3
NUM_TOPICS = 1
NODE_TYPE = "desktop"
NETWORK_TYPE = "scalefree"
NUM_PARTITIONS = 1
NUM_SUBNETS = 1

# Global config
DEFAULT_CONFIG_FILE = "github.com/logos-co/wakurtosis/config/config.json"

# Tests
NUMBER_TEST_MESSAGES = 5
DELAY_BETWEEN_TEST_MESSAGE = "0.5"