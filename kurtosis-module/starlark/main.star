contents = read_file(
   # The path to the file to read, which must obey Kurtosis package syntax.
   # MANDATORY
   src_path = "github.com/logos-co/wakurtosis/master/kurtosis-module/starlark/waku_test_topology.json"
)


service = add_service(
    service_id = "first_waku_node",
    config = struct(
        image = "wakunode",
        ports = {"rpc" : struct(number = 8545, protocol = "TCP" )},
        entrypoint=[
            "/usr/bin/wakunode", "--rpc-address=0.0.0.0"
        ],
        cmd=[
            "--topics='test_topic'", '--rpc-admin=true', '--keep-alive=true'
        ]
    ),
)

print("done")