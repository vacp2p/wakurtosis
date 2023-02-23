# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)

def create_config(plan, wls_config):
    
    # Traffic simulation parameters
    wls_yml_template = templates.get_wls_template()

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_WLS_CONFIGURATION_FILE_NAME: struct(
                template=wls_yml_template,
                data=wls_config,
            )
        },
        name="wls_config"
    )
    
    return artifact_id

def create_targets(plan, services):
    
    # Get private ip and ports of all nodes
    template_data = files.generate_template_node_targets(services, vars.RPC_PORT_ID, "targets")

    # Template
    template = """
        {{.targets}}
    """

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TARGETS_FILE_NAME_WLS: struct(
                template=template,
                data=template_data,
            )
        },
        name="wls_targets"
    )

    return artifact_id

def init(plan, services, wls_config):
    
    # Generate simulation config
    wls_config = create_config(plan, wls_config)

    tomls_artifact = plan.upload_files(
        src = vars.NODE_CONFIG_FILE_LOCATION,
        name = "tomls_artifact",
    )

    # Create targets.json
    wls_targets = create_targets(plan, services)


    add_service_config = ServiceConfig(
        image=vars.WLS_IMAGE,
        ports={},
        files={
            vars.WLS_CONFIG_PATH: wls_config,
            vars.WLS_TARGETS_PATH: wls_targets,
            vars.WLS_TOMLS_PATH: tomls_artifact
        },
        cmd=vars.WLS_CMD
    )
    wls_service = plan.add_service(
        service_name=vars.WLS_SERVICE_NAME,
        config=add_service_config
    )

    return wls_service

