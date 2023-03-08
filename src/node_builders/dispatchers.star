# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
nomos = import_module(vars.NOMOS_MODULE)
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)
nwaku_builder = import_module(vars.NWAKU_BUILDER_MODULE)
gowaku_builder = import_module(vars.GOWAKU_BUILDER_MODULE)
nomos_builder = import_module(vars.NOMOS_BUILDER_MODULE)


service_builder_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: gowaku_builder.prepare_gowaku_service,
    vars.GENNET_NWAKU_IMAGE_VALUE: nwaku_builder.prepare_nwaku_service,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos_builder.prepare_nomos_service
}

service_info_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.get_wakunode_peer_id,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.get_wakunode_peer_id,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.get_nomos_peer_id
}

service_multiaddr_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.create_node_multiaddress,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.create_node_multiaddress,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.create_node_multiaddress
}

service_connect_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.connect_wakunode_to_peers,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.connect_wakunode_to_peers,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.connect_nomos_to_peers
}

ports_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku_builder.add_waku_ports_info_to_topology,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku_builder.add_waku_ports_info_to_topology,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos_builder.add_nomos_ports_info_to_topology
}