

def send_json_rpc(plan, service_name, port_id, method, params, extract={}):
    recipe = PostHttpRequestRecipe(
        service_name=service_name,
        port_id=port_id,
        endpoint="",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}',
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200)

    return response