import httpx

URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"


def fetch_declarations(state_fips, county_fips, start, end):
    filter_text = (
        f"fipsStateCode eq '{state_fips}'"
        f" and fipsCountyCode eq '{county_fips}'"
        f" and declarationDate ge '{start}T00:00:00.000Z'"
        f" and declarationDate le '{end}T23:59:59.999Z'"
    )
    params = {"$filter": filter_text, "$top": 1000}
    response = httpx.get(URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def parse_declarations(data):
    rows = []
    for record in data["DisasterDeclarationsSummaries"]:
        rows.append(
            (
                record["disasterNumber"],
                record["incidentType"],
                record["declarationDate"][:10],
                record["declarationTitle"],
                record["designatedArea"],
                record["declarationType"],
            )
        )
    return rows
