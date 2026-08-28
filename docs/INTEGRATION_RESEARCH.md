# Integration Research

## RapidAPI credential workflow

Source: [RapidAPI API Keys / Key Rotation](https://docs.rapidapi.com/docs/keys-and-key-rotation)

RapidAPI’s official documentation states that a user creates or rotates a key from the Developer Dashboard by selecting an app, opening the Authorization page, and selecting Add authorization. The resulting key is tested from the selected API’s Endpoints tab and is sent using the `X-RapidAPI-Key` header. RapidAPI also notes that some APIs require an external provider key or access token obtained from the API provider’s own website; the API listing’s About page identifies that requirement. The exact property API, host header, endpoint paths, and any provider-specific key are not defined by the SCALEESTATE AI project files and must be selected explicitly before implementation.

Retrieved August 28, 2026.

## BatchData credential workflow

Sources: [BatchData property-search portal guide](https://batchdata.io/blog/how-to-build-a-property-search-portal-with-batchdatas-api) and [BatchData API documentation](https://developer.batchdata.com/docs/batchdata/welcome-to-batchdata)

BatchData’s official guide says developers sign up at `app.batchdata.com`, find the API key in account settings, and send it in the `Authorization: Bearer <API_KEY>` header with `Accept: application/json` and `Content-Type: application/json`. The guide documents property search via `POST https://api.batchdata.com/api/v1/property/search`, filters including location, property type, bedrooms, square feet, and listing-price ranges, and pagination via a `next_token`. It also describes a property lookup endpoint and reports that plan access can affect datasets. The exact endpoint fields and entitlement for the SCALEESTATE AI account must be verified against the developer portal before activation.

The project’s approved architecture lists BatchData as an allowed provider. No BatchData credential has been supplied or configured in this task.

Retrieved August 28, 2026.

## Realtor.io / RealtyAPI identity check

The requested name `realtor.io` does not resolve in the available official API search as a clearly identifiable property-data provider. The official-looking service found is **RealtyAPI.io** (`https://www.realtyapi.io/`), which advertises Realtor US, property details, listing search by location/address/coordinates/polygon/postal code, autocomplete, and an API-key signup flow. It also exposes an MCP URL, but this project request is for a server-side API integration, not MCP access. The official page did not provide enough stable endpoint/authentication detail in the retrieved page to implement safely. The service identity must be confirmed as RealtyAPI.io versus Realtor.com or another provider before requesting a secret or writing an adapter.

Retrieved August 28, 2026.

## RealtyAPI.io Realtor US API

Source: [RealtyAPI.io Realtor API](https://www.realtyapi.io/api/realtor)

The official RealtyAPI.io Realtor page identifies the base host as `https://realtor.realtyapi.io`, the key header as `x-realtyapi-key`, and the property-details endpoint `GET /details/byaddress`. Its minimal read-only example uses the `address` query parameter. The page also lists `/details/byid`, `/details/byurl`, `/autocomplete`, `/search/bylocation`, `/search/byzip`, `/search/bycoordinates`, `/search/bypolygon`, and `/search/byurl`. It describes the API as an unofficial Realtor API, so live usage must comply with RealtyAPI.io’s terms and the project’s approved data-provenance requirements.

Retrieved August 28, 2026.
