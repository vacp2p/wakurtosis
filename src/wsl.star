# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)

def create_config(plan, wls_config):
    
    # Traffic simulation parameters
    wsl_yml_template = templates.get_wsl_template()

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_WSL_CONFIGURATION_FILE_NAME: struct(
                template=wsl_yml_template,
                data=wls_config,
            )
        },
        name="wsl_config"
    )
    
    return artifact_id

def create_targets(plan, services):
    
    # Get private ip and ports of all nodes
    template_data = files.generate_template_node_targets(services, vars.RPC_PORT_ID)

    # Template
    template = """
        {{.targets}}
    """

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TARGETS_FILE_NAME_WSL: struct(
                template=template,
                data=template_data,
            )
        },
        name="wsl_targets"
    )

    return artifact_id

def init(plan, services, wsl_config):
    
    # Generate simulation config
    wsl_config = create_config(plan, wsl_config)

    tomls_artifact = plan.upload_files(
        src = vars.NODE_CONFIG_FILE_LOCATION,
        name = "tomls_artifact",
    )

    # Create targets.json
    wsl_targets = create_targets(plan, services)


    add_service_config = ServiceConfig(
        image=vars.WSL_IMAGE,
        ports={},
        files={
            vars.WSL_CONFIG_PATH: wsl_config,
            vars.WSL_TARGETS_PATH: wsl_targets,
            vars.WSL_TOMLS_PATH: tomls_artifact
        },
        cmd=["python3", "wsl.py"]
    )
    wsl_service = plan.add_service(
        service_name=vars.WSL_SERVICE_NAME,
        config=add_service_config
    )

    return wsl_service

