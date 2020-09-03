""" Arcus API integrations commands """
import click

from voithos.lib.system import error, is_port_open
import voithos.lib.service.arcus.integrations as intgs


def _validate_addr(api_addr):
    """ Ensure that the provided API addr has a port and protocol """
    example = "example: http://preview.breqwatr.com:1234"
    # require that the protocol be specified
    if "http" not in api_addr or "//" not in api_addr:
        error(f"ERROR: --api-addr requires protocol - {example}", exit=True)
    # require that the port be specified
    if ":" not in api_addr.replace("://", ""):
        error(f"ERROR: --api-addr requires port - {example}", exit=True)
    # Check if the specified port is actually up to avoid ugly stack traces
    split_addr = api_addr.split("//")[1].split(":")
    host = split_addr[0]
    port = int(split_addr[1])
    if not is_port_open(host, port):
        error("ERROR: --api-address does not appear online", exit=True)


def _validate_type(api_addr, type_name):
    """ Ensure that the given type name exists """
    types = intgs.list_types(api_addr)
    matching_type = next((t for t in types if t["type"] == type_name), None)
    if matching_type is None:
        error(
            f"ERROR: The given type '{type_name}' is not valid. Type is case sensitive.", exit=True
        )


def _print_validate_fields_error(intg_type):
    """ Print the required fields - intg_type is the return from intgs.show_type """
    error("ERROR: The following fields (and only these fields) must be used with --field / -f")
    for name in intg_type["fields"].keys():
        error(f"  {name}")
    error("... Correct the fields and try again", exit=True)


def _validate_fields(api_addr, intg_type_name, input_fields):
    """ Ensure that the required fields are present """
    # Pull a list of the required fields from the integration type
    intg_type = intgs.show_type(api_addr, intg_type_name)
    reqd_fields = intg_type["fields"].keys()
    num_expected_fields = len(reqd_fields)
    num_input_fields = len(input_fields)
    if num_expected_fields != num_input_fields:
        error(f"ERROR: Wrong qty of fields ... {num_expected_fields} != {num_input_fields}")
        _print_validate_fields_error(intg_type)
    for input_field in input_fields:
        if input_field[0] not in reqd_fields:
            error(f"ERROR: Invalid field: {input_field[0]}")
            _print_validate_fields_error(intg_type)


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.command(name="list-types")
def integrations_list_types(api_addr):
    """ List available integration-types """
    _validate_addr(api_addr)
    types = intgs.list_types(api_addr)
    for intg_type in types:
        click.echo(intg_type["type"])
        for field in intg_type["fields"]:
            click.echo(f"  {field}: {intg_type['fields'][field]}")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.argument("type_name")
@click.command(name="show-type")
def integrations_show_type(api_addr, type_name):
    """ Show the properties of an integration-type """
    _validate_addr(api_addr)
    intg_type = intgs.show_type(api_addr, type_name)
    if intg_type is None:
        error(f"ERROR: type {type_name} is not valid")
        return
    click.echo(intg_type["type"])
    for field in intg_type["fields"]:
        click.echo(f"  {field}: {intg_type['fields'][field]}")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.option("--username", "-u", required=True, help="OpenStack administrator username")
@click.option("--password", "-p", required=True, help="OpenStack administrator password")
@click.command(name="list")
def integrations_list(api_addr, username, password):
    """ List the current integrations """
    _validate_addr(api_addr)
    intg_list = intgs.list_integrations(api_addr, username, password)
    click.echo("--------")
    for elem in intg_list:
        click.echo(f"id:           {elem['id']}")
        click.echo(f"display_name: {elem['display_name']}")
        click.echo(f"links:        {elem['links']}")
        click.echo("fields:")
        intg_type = intgs.show_type(api_addr, elem["type"])
        fields = intg_type["fields"]
        for field in fields:
            click.echo(f"  {field}:   {elem[field]}")
        click.echo("--------")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.option("--username", "-u", required=True, help="OpenStack administrator username")
@click.option("--password", "-p", required=True, help="OpenStack administrator password")
@click.option("--id", "-i", "intg_id", required=True, help="ID of the integration to edit")
@click.command(name="delete")
def integrations_delete(api_addr, username, password, intg_id):
    """ Delete an integration """
    _validate_addr(api_addr)
    success = intgs.delete_integration(api_addr, username, password, intg_id)
    if success:
        click.echo("Successfully deleted Integration")
    else:
        error("Failed to delete Integration")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.option("--username", "-u", required=True, help="OpenStack administrator username")
@click.option("--password", "-p", required=True, help="OpenStack administrator password")
@click.option("--type", "-t", "intg_type", required=True, help="Integration type to be created")
@click.option(
    "--field",
    "-f",
    "fields",
    multiple=True,
    nargs=2,
    help="Format: --field <key1> '<value1>' --field <key2> '<value2>'",
)
@click.command(name="create")
def integrations_create(api_addr, username, password, intg_type, fields):
    """ Create a new integration """
    _validate_addr(api_addr)
    _validate_type(api_addr, intg_type)
    _validate_fields(api_addr, intg_type, fields)
    success = intgs.create_integration(api_addr, username, password, intg_type, fields)
    if success:
        click.echo("Successfully created Integration")
    else:
        error("Failed to create Integration")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.option("--username", "-u", required=True, help="OpenStack administrator username")
@click.option("--password", "-p", required=True, help="OpenStack administrator password")
@click.option("--id", "-i", "intg_id", required=True, help="ID of the integration to edit")
@click.option("--links-csv", "links_csv", default=None, help="Reset this integrations links")
@click.option(
    "--field",
    "-f",
    "fields",
    multiple=True,
    nargs=2,
    help="Format: --field <key1> '<value1>' --field <key2> '<value2>'",
)
@click.command(name="update")
def integrations_update(api_addr, username, password, intg_id, fields, links_csv):
    """ Update an integration properties """
    _validate_addr(api_addr)
    links = None if links_csv is None else links_csv.split(",")
    success = intgs.update_integration(api_addr, username, password, intg_id, fields, links=links)
    if success:
        click.echo("Successfully updated Integration")
    else:
        error("Failed to update Integration")


@click.option("--api-addr", "-a", "api_addr", required=True, help="address with protocol & port")
@click.option("--username", "-u", required=True, help="OpenStack administrator username")
@click.option("--password", "-p", required=True, help="OpenStack administrator password")
@click.option("--add", "add_ids", multiple=True, help="link ID to add - repeatable")
@click.option("--delete", "delete_ids", multiple=True, help="link ID to remove - repeatable")
@click.argument("integration_id")
def get_integrations_group():
    """ Returns the integrations group """

    @click.group(name="integrations")
    def integrations_group():
        """ Integrate Arcus API with 3rd party tools """

    integrations_group.add_command(integrations_list_types)
    integrations_group.add_command(integrations_show_type)
    integrations_group.add_command(integrations_list)
    integrations_group.add_command(integrations_delete)
    integrations_group.add_command(integrations_create)
    integrations_group.add_command(integrations_update)
    return integrations_group
