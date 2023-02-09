# docker run --volume=/:/rootfs:ro
# --volume=/var/run:/var/run:rw
# --volume=/var/lib/docker/:/var/lib/docker:ro
# --volume=/dev/disk/:/dev/disk:ro
# --volume=/sys:/sys:ro
# --volume=/etc/machine-id:/etc/machine-id:ro
# --volume=/mnt/windows_docker/:/rootfs/var/lib/docker:ro
# --publish=8080:8080
# --detach=true
# --name=cadvisor
# --privileged
# --device=/dev/kmsg

# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)


def set_up_cadvisor(plan):
    root_id, varrun_id, varlibdocker, devdisk_id, sys_id, machineid_id, wsl_id = files.prepare_artifact_folders_cadvisor(
        plan)

    add_service_config = ServiceConfig(
        image=system_variables.CADVISOR_IMAGE,
        ports={
            system_variables.CADVISOR_PORT_ID: PortSpec(number=system_variables.CADVISOR_TCP_PORT,
                                                        transport_protocol="TCP")
        },
        files={
            system_variables.CONTAINER_ROOT_CADVISOR: root_id,
            system_variables.CONTAINER_VARRUN_CADVISOR: varrun_id,
            system_variables.CONTAINER_VARLIBDOCKER_CADVISOR: varlibdocker,
            system_variables.CONTAINER_DEVDISK_CADVISOR: devdisk_id,
            system_variables.CONTAINER_SYS_CADVISOR: sys_id,
            system_variables.CONTAINER_MACHINEID_CADVISOR: machineid_id,
            system_variables.CONTAINER_WSL: wsl_id
        }
    )

    cadvisor_service = plan.add_service(
        service_name=system_variables.GRAFANA_SERVICE_NAME,
        config=add_service_config
    )

    return cadvisor_service
