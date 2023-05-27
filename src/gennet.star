# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)



def init(plan, config, enr):
    config_file_name =  config.split("/")[-1]

    config_artifact = plan.upload_files(
        src = vars.CONFIG_FILE_LOCATION,
        name = vars.GENNET_CONFIG_ARTIFACT_NAME,
    )
    # ENR file
    enr_data = {"enr": enr}
    enr_artifact = plan.render_templates(
        config={
            "enr.txt": struct(
                template = templates.get_enr_template(),
                data=enr_data
            )
        }
    )

    # Gennet configuration
    add_service_config = ServiceConfig(
        image=vars.GENNET_IMAGE,
        files={
            # Config folder
            "/config/": config_artifact,
            # ENR file
            "/enr_info/": enr_artifact
        },
        cmd= ["--config-file", "/config/"+config_file_name, "--traits-dir", "/config/traits"]
    )

    gennet_service = plan.add_service(
        name=vars.GENNET_SERVICE_NAME,
        config=add_service_config
    )

    return gennet_service
