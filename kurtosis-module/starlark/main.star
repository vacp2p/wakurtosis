contents = read_file(
   # The path to the file to read, which must obey Kurtosis package syntax.
   # MANDATORY
   src_path = "waku_test_topology.json"
)

print(contents)

service = add_service(
    service_id = "first_waku_node",
    config = struct(
        image = "wakunode",
        ports = {"rpc" : struct(number = 8545, protocol = "TCP" )},
        entrypoint=[
            "/usr/bin/wakunode"
        ]
    ),
)

print(service)