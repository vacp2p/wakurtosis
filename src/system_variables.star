# Waku Configuration
WAKU_IMAGE = "statusteam/nim-waku:019f357d"
WAKU_RPC_PORT_ID = "rpc"
WAKU_TCP_PORT = 8545
WAKU_LIBP2P_PORT_ID = "libp2p"
WAKU_LIBP2P_PORT = 60000
WAKU_SETUP_WAIT_TIME = "5"

WAKU_CONFIG_FILE_LOCATION = "/waku/configuration_file"
WAKU_ENTRYPOINT = ["/usr/bin/wakunode", "--rpc-address=0.0.0.0", "--metrics-server-address=0.0.0.0"]

# Prometheus Configuration
PROMETHEUS_IMAGE = "prom/prometheus:latest"
PROMETHEUS_PORT_ID = "prometheus"
PROMETHEUS_TCP_PORT = 8008
PROMETHEUS_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/prometheus.yml"

# Grafana Configuration
GRAFANA_IMAGE = "grafana/grafana:latest"
GRAFANA_CONFIGURATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/config/"
GRAFANA_CUSTOMIZATION_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/customizations/"
GRAFANA_DASHBOARD_PATH = "github.com/logos-co/wakurtosis/monitoring/configuration/dashboards/"

GRAFANA_PORT_ID = "grafana"
GRAFANA_TCP_PORT = 3000

# WSL Configuration
WSL_IMAGE = "wsl:0.0.1"
WSL_CONFIG_PATH = "/wsl/config"
WSL_TARGETS_PATH = "/wsl/targets"

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
WSL_MODULE = "github.com/logos-co/wakurtosis/src/wsl.star"

# Default main starlark arguments
SAME_TOML_CONFIGURATION_NAME = "same_toml_configuration"
SAME_TOML_CONFIGURATION = True

TOPOLOGY_FILE_NAME = "topology"
TOPOLOGIES_LOCATION = "github.com/logos-co/wakurtosis/config/network_topology/"
DEFAULT_TOPOLOGY_FILE = "waku_test_topology_small.json"

NUMBER_TEST_MESSAGES = 50
DELAY_BETWEEN_TEST_MESSAGE = "0.5"