Title: API Documentation - v1 | Lobbying Disclosure

URL Source: <https://lda.senate.gov/api/redoc/v1/>

Markdown Content:
API Documentation - v1 | Lobbying Disclosure

===============

[Skip to main content](https://lda.senate.gov/api/redoc/v1/#content)[![Image 1: Senate Eagle](https://lda.senate.gov/static/shared/images/eagle-white.png)United States Senate U.S. Senate Lobbying Disclosure LDA](https://lda.senate.gov/system/public/)
 
* [**Registrations &Quarterly Activity**](https://lda.senate.gov/filings/public/filing/search/)
* [**Contributions**](https://lda.senate.gov/filings/public/contribution/search/)
* [**Download API**](https://lda.senate.gov/api/)
* [**Lookup Registrant & Client ID s**](https://lda.senate.gov/registrants/public/registrant-client/lookup/)

1. [Download API](https://lda.senate.gov/api/)
2. Documentation

API Documentation
=================

* * *

[![Image 2: logo](https://lda.senate.gov/static/shared/images/us-congress-seal.png)](https://www.senate.gov/legislative/opr.htm)

* About the REST API
  * Introduction
  * Terms of Service
  * Changes
  * Schema
  * Root Endpoint
  * Browsable API
  * Constants

* Authentication
  * Register and Obtain an API Key
  * Reset Forgotten Password

* Implementation Details
  * Request Throttling
  * Pagination
  * Ordering
  * Advanced Text Searching
  * Limitations / Caveats

* Common Errors
  * Invalid API Key
  * Request Throttled
  * Invalid Query String Parameter Values
  * Unsupported HTTP Method
  * Query String Filters Required for Pagination

* Lobbying Data
  * Filings
    * get listFilings
    * get retrieveFiling

  * Contribution Reports
    * get listContributionReports
    * get retrieveContributionReport

  * Registrants
    * get listRegistrants
    * get retrieveRegistrant

  * Clients
    * get listClients
    * get retrieveClient

  * Lobbyists
    * get listLobbyists
    * get retrieveLobbyist

* Constants
  * Constants
    * get listFilingTypes
    * get listLobbyingActivityGeneralIssues
    * get listGovernmentEntities
    * get listCountries
    * get listStates
    * get listLobbyistPrefixes
    * get listLobbyistSuffixes
    * get listContributionItemTypes

[![Image 3: redocly logo](https://cdn.redoc.ly/redoc/logo-mini.svg)API docs by Redocly](https://redocly.com/redoc/)

Lobbying Disclosure
===================

Download OpenAPI specification:[Download](https://lda.senate.gov/api/openapi/v1/)

Senate Office of Public Records (OPR): [lobby@sec.senate.gov](mailto:lobby@sec.senate.gov)URL: [https://www.senate.gov/legislative/opr.htm](https://www.senate.gov/legislative/opr.htm)[Terms of Service](https://lda.senate.gov/api/tos/)

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API)About the REST API
=====================================================================================

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Introduction)Introduction
--------------------------------------------------------------------------------------------

This document describes the resources that make up the official Lobbying Disclosure REST API v1. If you have any issues, please contact the Senate Office of Public Records (OPR) at [lobby@sec.senate.gov](mailto:lobby@sec.senate.gov). OPR does not offer development advice and does not provide language specific guides. The REST API is programming language agnostic. Any programming language can be used to make REST API requests to retrieve data.

The REST API is documented in the **OpenAPI format** which can be found by clicking the "Download" button at the top of the page. In addition to the standard OpenAPI syntax, we use a few [vendor extensions](https://github.com/Redocly/redoc/blob/master/docs/redoc-vendor-extensions.md). There are a variety of open source and proprietary tools that can read OpenAPI specifications and interact with the API by reading the published specification. OPR does not recommend any specific OpenAPI tools.

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Terms-of-Service)Terms of Service
----------------------------------------------------------------------------------------------------

REST API is governed by a [Terms of Service](https://lda.senate.gov/api/tos/).

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Changes)Changes
----------------------------------------------------------------------------------

| Date | Description |
| --- | --- |
| 05/09/2024 | Clarified documentation on: date format when filtering results (yyyy-mm-dd) and constants information. |
| 01/18/2024 | Added limitations / caveats section |
| 08/08/2023 | Change request throttle rates from by hour to by minute to reduce burstable requests. New request throttles: unauthenticated (anon): 15/minute (900/hour), API key (registered): 120/minute (7,200/hour) |
| 04/05/2023 | Added requirements to use at least one query string parameter value when paginating results for `Filings` and `Contribution Reports`. See warnings in [Pagination](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Pagination) for more information. |
| 04/05/2023 | Removed ordering filters for performance reasons. Filing: `id`; Contribution Report: `id`; Client: `registrant_name`; Lobbyist: all but `id` |
| 12/14/2022 | Added registrant address fields as indicated on the latest LD1 / LD2 filing to the filing endpoint. |
| 03/28/2022 | Fixed an issue where LD2 filings posted from 2/15/2022 to 3/28/2022 did not display income or expenses. |
| 01/24/2022 | Added Advanced Text Searching in Filing endpoint on fields: `filing_specific_lobbying_issues`, `lobbyist_conviction_disclosure`, and `lobbyist_covered_position`. |
| 01/13/2022 | Fixed an issue where the list of Contribution Items in Contribution Reports (LD-203) endpoint did not match the filed Contribution Report document. |
| 07/30/2021 | Added Lobbyist endpoint |
| 03/10/2021 | Decreased pagination to 25. Increased request throttle rates: unauthenticated (anon): 1,000/hour, API key (registered): 20,000/hour |

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Schema)Schema
--------------------------------------------------------------------------------

All REST API access is over HTTPS, and accessed from `https://lda.senate.gov/api/v1/`. All data is sent and received as JSON. Testing can be done through [human browseable API interface](https://lda.senate.gov/api/v1/) where it is possible to make requests with filtering/ordering and pagination.

Blank fields are included as `null` instead of being omitted.

All timestamps return in ISO 8601 format:

```text
YYYY-MM-DDTHH:MM:SSZ
```

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Root-Endpoint)Root Endpoint
----------------------------------------------------------------------------------------------

Sending a request with `GET` to the root endpoint will return all the endpoint categories that the REST API v1 supports:

**Request:**

```http
GET https://lda.senate.gov/api/v1/
```

**Reponse:**

```http
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "filings": "https://lda.senate.gov/api/v1/filings/",
    "contributions": "https://lda.senate.gov/api/v1/contributions/",
    "registrants": "https://lda.senate.gov/api/v1/registrants/",
    "clients": "https://lda.senate.gov/api/v1/clients/",
    "lobbyists": "https://lda.senate.gov/api/v1/lobbyists/",
    "constants/filing/filingtypes": "https://lda.senate.gov/api/v1/constants/filing/filingtypes/",
    "constants/filing/lobbyingactivityissues": "https://lda.senate.gov/api/v1/constants/filing/lobbyingactivityissues/",
    "constants/filing/governmententities": "https://lda.senate.gov/api/v1/constants/filing/governmententities/",
    "constants/general/countries": "https://lda.senate.gov/api/v1/constants/general/countries/",
    "constants/general/states": "https://lda.senate.gov/api/v1/constants/general/states/",
    "constants/lobbyist/prefixes": "https://lda.senate.gov/api/v1/constants/lobbyist/prefixes/",
    "constants/lobbyist/suffixes": "https://lda.senate.gov/api/v1/constants/lobbyist/suffixes/"
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Browsable-API)Browsable API
----------------------------------------------------------------------------------------------

APIs may be for machines to access, but humans have to be able to read APIS as well. We support a human-friendly HTML output when `HTML` format is requested where it is possible to make requests with filtering/ordering and pagination.

[View the HTML API output](https://lda.senate.gov/api/v1/).

[](https://lda.senate.gov/api/redoc/v1/#section/About-the-REST-API/Constants)Constants
--------------------------------------------------------------------------------------

Lists of key / value constants are published for the following fields:

* Filing Types
* Lobbying Activity Issues
* Government Entities
* Countries
* States (US States)
* Prefixes (e.g. Mr., Ms., Mx., Dr., etc.)
* Suffixes (e.g. Sr., Jr., II, etc.)

These endpoints are periodically updated when new key / values are added. Please see the API [Constants](https://lda.senate.gov/api/redoc/v1/#tag/Constants) section section of this documenation for more information.

[](https://lda.senate.gov/api/redoc/v1/#section/Authentication)Authentication
=============================================================================

There are two ways to authenticate through the REST API. Our API offers two types of authentication:

* API Key (Registered)
* Unauthenticated (Anonymous)

For clients to authenticate using an API Key, the token key must be included in the `Authorization` HTTP header and **must** be prefixed by the string literal "Token", with whitespace separating the two strings. For example:

```http
Authorization: Token z944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

For clients without an API Key, no special authentication is required, however anonymous clients are subject to more strict request throttling.

[](https://lda.senate.gov/api/redoc/v1/#section/Authentication/Register-and-Obtain-an-API-Key)Register and Obtain an API Key
----------------------------------------------------------------------------------------------------------------------------

[Register](https://lda.senate.gov/api/register/) by using our automated system. After registering, you can obtain an API key using one of these methods:

* Via a [web form](https://lda.senate.gov/api/auth/login/)
* Via an API call (Make a `POST` with your `username` and `password` login credentials as form data or JSON.)

The response will contain your API key if properly authenticated.

**Request:**

```http
POST https://lda.senate.gov/api/auth/login/

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**

```http
HTTP 200 OK
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "key": "z944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Authentication/Reset-Forgotten-Password)Reset Forgotten Password
----------------------------------------------------------------------------------------------------------------

If you have forgotten your password or need to change it, you can reset your password using one of these methods:

* Via a [web form](https://lda.senate.gov/api/auth/password/reset/)
* Via an API call (Make a `POST` with your `email` as form data or JSON.)

**Request:**

```http
POST https://lda.senate.gov/api/auth/password/reset/

{
    "email": "your_email_address"
}
```

**Response:**

```http
HTTP 200 OK
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "detail": "Password reset e-mail has been sent."
}
```

If successful, you will receive email with a `uid` and `token` to reset your password which can be done using one of these methods:

* Via a [web form](https://lda.senate.gov/api/auth/password/reset/confirm/%3Cuidb64%3E/%3Ctoken%3E/)
* Via an API call (Make a `POST` with you `new_password1` and `new_password2` with the `uid`, and `token` from your email as form data or JSON.)

**Request:**

```http
POST https://lda.senate.govapi/auth/password/reset/confirm/<uidb64>/<token>/

{
    "new_password1": "new_password",
    "new_password2": "new_password",
    "uid": "UID from your email",
    "token": "Token from your email"
}
```

**Response:**

```http
HTTP 200 OK
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "detail": "Password reset e-mail has been sent."
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details)Implementation Details
=============================================================================================

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Request-Throttling)Request Throttling
------------------------------------------------------------------------------------------------------------

All REST API requests are throttled to prevent abuse and to ensure stability. Our API is rate limited depending the type of authentication option you choose:

* API Key (Registered): 120/minute
* Unauthenticated (Anonymous): 15/minute

Unauthenticated requests are rate limited by the originating IP address and not the user making requests. Authenticated requests share the same user quota regardless of whether multiple API keys are used.

Requests made for the following items do not count towards rate limits:

* Original HTML and PDF documents at:
  * `https://lda.senate.gov/filings/public/filing/{filing_uuid}/print/`
  * `https://lda.senate.gov/filings/public/contribution/{filing_uuid}/print/`

* Constants at all URLs starting with `https://lda.senate.gov/api/v1/constants/*`

Requests that exceed the throttling rate for your authentication type will received an HTTP 429 `Too Many Requests` response. The `Retry-After` header in the response will indicate the number of seconds to wait.

**Response:**

```http
HTTP 429 Too Many Requests
Allow: GET
Content-Type: application/json
Retry-After: 1596
Vary: Accept

{
    "detail": "Request was throttled. Expected available in 1596 seconds."
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Pagination)Pagination
--------------------------------------------------------------------------------------------

Large result sets are split into individual pages of data. The pagination links are provided as part of the content of the response via the `next` and `previous` keys in the response. You can control which page to request by using the `page` query string parameter.

**Request:**

```http
GET https://lda.senate.gov/api/v1/filings/?page=2
```

**Response:**

```http
HTTP 200 OK

{
    "count": 1023
    "next": "https://lda.senate.gov/api/v1/filings/?page=1",
    "previous": "https://lda.senate.gov/api/v1/filings/?page=3",
    "results": [
       …
    ]
}
```

By default, each page is limited to 25 results per page. You may set the page size by setting `page_size` as a query string parameter up to 25.

**Warning**

The `Filings` and `Contribution Reports` endpoints require at least one queryset parameter to be passed in order to paginate results beyond the first page. This is for performance reasons.

If you would like to paginate through all `Filings`, we recommend paginating through the results by filing year. Below shows an example of getting page 2 of results for filing year 2023 for `Filings`.

**Request:**

```http
GET https://lda.senate.gov/api/v1/filings/?filing_year=2023&page=2
```

**Response:**

```http
HTTP 200 OK

{
    "count": 1023
    "next": "https://lda.senate.gov/api/v1/filings/?filing_year=2023&page=1",
    "previous": "https://lda.senate.gov/api/v1/filings/?filing_year=2023&page=3",
    "results": [
       …
    ]
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Ordering)Ordering
----------------------------------------------------------------------------------------

Result sets can be ordered by using the `ordering` query string parameter. Each endpoint has its own set of fields you can order by so see the available ordering in the [browseable API interface](https://lda.senate.gov/api/v1/) under the "Filters" button in the upper right corner of the interface.

For example, to order filings by `dt_posted`:

```http
GET https://lda.senate.gov/api/v1/filings/?ordering=dt_posted
```

The client may also specify reverse orderings by prefixing the field name with `-`, like so:

```http
GET https://lda.senate.gov/api/v1/filings/?ordering=-dt_posted
```

Multiple orderings may also be specified:

```http
GET https://lda.senate.gov/api/v1/filings/?ordering=dt_posted,registrant__name
```

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Advanced-Text-Searching)Advanced Text Searching
----------------------------------------------------------------------------------------------------------------------

* **Unquoted Text** - Text not inside quote marks will not be treated as a phrase. Text separated by a space is treated as an OR operator between them. _Estate Tax_ will match _estate_ OR _tax_ even if they do appear next to each other.
* **"Quoted Text"** - Text inside double quote marks will be treated as a phrase. _Estate Tax_ will match the phrase _estate tax_ but will not match the words _estate_ or _tax_ if they appear separately.
* **OR** - The word _OR_ will be treated as a true OR operator. _"Estate Tax" OR "Estate Taxes"_ will match the phrases _estate tax_or _estate taxes_ but will not match the words _estate_ or _tax_ if they appear separately.
* **-** The dash character _-_ will be treated as a NOT EQUALS operator. _"Estate Tax" -"Payroll Taxes"_ will match the phrase _estate tax_ but not _payroll taxes_ if they appear in the same field.

[](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Limitations-Caveats)Limitations / Caveats
----------------------------------------------------------------------------------------------------------------

* **Government Entities** - Filings that posted before 2/14/2021 do not have government entities broken down by each individual lobbying activity area. Instead, the government entities listed on these filings is a list of entities that appear on the filing as a whole. This limitation is due to data imported from a legacy system. Filings that posted after 2/14/2021 will have government entities broken down by each individual lobbying activity area.

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors)Common Errors
===========================================================================

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors/Invalid-API-Key)Invalid API Key
---------------------------------------------------------------------------------------------

If you supply an invalid API Key, you will receive an HTTP 401 `Unauthorized` response:

**Response:**

```http
HTTP 401 UNAUTHORIZED

{
    "detail": "Invalid token."
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors/Request-Throttled)Request Throttled
-------------------------------------------------------------------------------------------------

If you exceed your rate limit for your authentication type, you will receive an HTTP 429 `Too Many Requests` response. See the [Request Throttling](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Request-Throttling) section for more information.

**Response:**

```http
HTTP 429 Too Many Requests
Allow: GET
Content-Type: application/json
Retry-After: 1596
Vary: Accept

{
    "detail": "Request was throttled. Expected available in 1596 seconds."
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors/Invalid-Query-String-Parameter-Values)Invalid Query String Parameter Values
-----------------------------------------------------------------------------------------------------------------------------------------

If you pass invalid query string parameter values, you will likely receive an HTTP 404 `Not Found` or HTTP 400 `Bad Request` response with a detailed error message.

For example, passing a non-integer for the page number:

**Request:**

```http
GET https://lda.senate.gov/api/v1/filings/?page=a
```

**Response:**

```http
HTTP 404 Not Found
Allow: GET
Content-Type: application/json
Vary: Accept

{
    "detail": "Invalid page."
}
```

For example, passing an invalid value for the Registrant ID:

**Request:**

```http
GET https://lda.senate.gov/api/v1/filings/?registrant_id=a
```

**Response:**

```http
HTTP 400 Bad Request
Allow: GET
Content-Type: application/json
Vary: Accept

{
    "registrant_id": [
        "Enter a number."
    ]
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors/Unsupported-HTTP-Method)Unsupported HTTP Method
-------------------------------------------------------------------------------------------------------------

If you use an unsupported HTTP method, you will receive an HTTP 405 `Method Not Allowed` response:

```http
DELETE https://lda.senate.gov/api/v1/filings/
Accept: application/json
```

**Response:**

```http
HTTP 405 Method Not Allowed
Content-Type: application/json
Content-Length: 42

{
    "detail": "Method \"DELETE\" not allowed."
}
```

[](https://lda.senate.gov/api/redoc/v1/#section/Common-Errors/Query-String-Filters-Required-for-Pagination)Query String Filters Required for Pagination
-------------------------------------------------------------------------------------------------------------------------------------------------------

If you use paginated results and do not include at least one query string parameter filter, you will receive an HTTP 400 `Bad Request` response:

```http
GET https://lda.senate.gov/api/v1/filings/?page=2
```

**Response:**

```http
HTTP 400 Bad Request
Allow: GET
Content-Type: application/json
Vary: Accept

{
   "detail": "You must pass at least one query string parameter to filter the results and be able to paginate the results."
}
```

See warnings in [Pagination](https://lda.senate.gov/api/redoc/v1/#section/Implementation-Details/Pagination) for more information.

[](https://lda.senate.gov/api/redoc/v1/#tag/Filings)Filings
===========================================================

Access LD1 / LD2 filings.

[](https://lda.senate.gov/api/redoc/v1/#tag/Filings/operation/listFilings)listFilings
-------------------------------------------------------------------------------------

get/api/v1/filings/

<https://lda.senate.gov/api/v1/filings/>

##### Authorizations

_ApiKeyAuth_

##### query Parameters

affiliated_organization_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Affiliated Organization Country
affiliated_organization_listed_indicator boolean

Any Affiliated Organizations Listed
affiliated_organization_name string

Affiliated Organization Name
client_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Client Country
client_id integer

Client ID
client_name string

Client Name
client_ppb_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Client PPB Country
client_ppb_state any

 Enum:"AL""AK""AS""AZ""AR""AA""AE""AP""CA""CO"… 49 more

Client PPB State
client_state any

 Enum:"AL""AK""AS""AZ""AR""AA""AE""AP""CA""CO"… 49 more

Client State
filing_amount_reported_max string<float>

Filing Amount Reported Range (Min / Max)
filing_amount_reported_min string<float>

Filing Amount Reported Range (Min / Max)
filing_dt_posted_after string<date-time>

Filing Date Posted Range (Before / After): yyyy-mm-dd
filing_dt_posted_before string<date-time>

Filing Date Posted Range (Before / After): yyyy-mm-dd
filing_period any

 Enum:"first_quarter""second_quarter""third_quarter""fourth_quarter""mid_year""year_end"

Filing Period
filing_specific_lobbying_issues string

Filing Specific Lobbying Issues (Supports Advanced Text Searching)
filing_type any

 Enum:"RR""RA""Q1""Q1Y""1T""1TY""1A""1AY""1@""1@Y"… 40 more

Filing Type
filing_uuid string<uuid>

filing_uuid
filing_year any

 Enum:2025 2024 2023 2022 2021 2020 2019 2018 2017 2016… 17 more

Filing Year
foreign_entity_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Foreign Entity Country
foreign_entity_listed_indicator boolean

Any Foreign Entities Listed
foreign_entity_name string

Foreign Entity Name
foreign_entity_ownership_percentage_max string

Foreign Entity Ownership Percentage
foreign_entity_ownership_percentage_min string

Foreign Entity Ownership Percentage
foreign_entity_ppb_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Foreign Entity PPB Country
lobbyist_conviction_date_range_after string<date>

Lobbyist Conviction Date Range (Before / After): yyyy-mm-dd
lobbyist_conviction_date_range_before string<date>

Lobbyist Conviction Date Range (Before / After): yyyy-mm-dd
lobbyist_conviction_disclosure string

Lobbyist Conviction Description (Supports Advanced Text Searching)
lobbyist_conviction_disclosure_indicator boolean

Lobbyist Any Disclosed Conviction(s)
lobbyist_covered_position string

Lobbyist Covered Position (Supports Advanced Text Searching)
lobbyist_covered_position_indicator boolean

Any Covered Government Position(s)
lobbyist_id integer

Lobbyist ID
lobbyist_name string

Lobbyist Name
ordering string

Which field to use when ordering the results.
page integer

A page number within the paginated result set.
page_size integer

Number of results to return per page.
registrant_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Registrant Country
registrant_id integer

Registrant ID
registrant_name string

Registrant Name
registrant_ppb_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Registrant PPB Country

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"count": 123,"next": "/api/v1/{operation}/?page=2","previous": null,"results": [{"url": "http://example.com","filing_uuid": "62b1778e-e2e3-443d-a795-ca3813b6cee5","filing_type": "RR","filing_type_display": "string","filing_year": 2025,"filing_period": "first_quarter","filing_period_display": "string","filing_document_url": "string","filing_document_content_type": "string","income": "string","expenses": "string","expenses_method": "a","expenses_method_display": "string","posted_by_name": "string","dt_posted": "2019-08-24T14:15:22Z","termination_date": "2019-08-24","registrant_country": "string","registrant_ppb_country": "string","registrant_address_1": "string","registrant_address_2": "string","registrant_different_address": true,"registrant_city": "string","registrant_state": "AL","registrant_zip": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"},"client": {"id": 0,"url": "http://example.com","client_id": "string","name": "string","general_description": "string","client_government_entity": true,"client_self_select": true,"state": "AL","state_display": "string","country": "US","country_display": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string","effective_date": "2019-08-24"},"lobbying_activities": [{"general_issue_code": "ACC","general_issue_code_display": "string","description": "string","foreign_entity_issues": "string","lobbyists": [{"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"covered_position": "string","new": true}],"government_entities": [{"id": 0,"name": "string"}]}],"conviction_disclosures": [{"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"date": "2019-08-24","description": "string"}],"foreign_entities": [{"name": "string","contribution": "string","ownership_percentage": "string","address": "string","city": "string","state": "AL","state_display": "string","country": "US","country_display": "string","ppb_city": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string"}],"affiliated_organizations": [{"name": "string","url": "http://example.com","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_city": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string"}]}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Filings/operation/retrieveFiling)retrieveFiling
-------------------------------------------------------------------------------------------

get/api/v1/filings/{filing_uuid}/

<https://lda.senate.gov/api/v1/filings/{filing_uuid}/>

Returns all filings matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### path Parameters

filing_uuid

required string<uuid>

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"url": "http://example.com","filing_uuid": "62b1778e-e2e3-443d-a795-ca3813b6cee5","filing_type": "RR","filing_type_display": "string","filing_year": 2025,"filing_period": "first_quarter","filing_period_display": "string","filing_document_url": "string","filing_document_content_type": "string","income": "string","expenses": "string","expenses_method": "a","expenses_method_display": "string","posted_by_name": "string","dt_posted": "2019-08-24T14:15:22Z","termination_date": "2019-08-24","registrant_country": "string","registrant_ppb_country": "string","registrant_address_1": "string","registrant_address_2": "string","registrant_different_address": true,"registrant_city": "string","registrant_state": "AL","registrant_zip": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"},"client": {"id": 0,"url": "http://example.com","client_id": "string","name": "string","general_description": "string","client_government_entity": true,"client_self_select": true,"state": "AL","state_display": "string","country": "US","country_display": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string","effective_date": "2019-08-24"},"lobbying_activities": [{"general_issue_code": "ACC","general_issue_code_display": "string","description": "string","foreign_entity_issues": "string","lobbyists": [{"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"covered_position": "string","new": true}],"government_entities": [{"id": 0,"name": "string"}]}],"conviction_disclosures": [{"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"date": "2019-08-24","description": "string"}],"foreign_entities": [{"name": "string","contribution": "string","ownership_percentage": "string","address": "string","city": "string","state": "AL","state_display": "string","country": "US","country_display": "string","ppb_city": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string"}],"affiliated_organizations": [{"name": "string","url": "http://example.com","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_city": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string"}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Contribution-Reports)Contribution Reports
=====================================================================================

Access LD203 filings.

[](https://lda.senate.gov/api/redoc/v1/#tag/Contribution-Reports/operation/listContributionReports)listContributionReports
--------------------------------------------------------------------------------------------------------------------------

get/api/v1/contributions/

<https://lda.senate.gov/api/v1/contributions/>

##### Authorizations

_ApiKeyAuth_

##### query Parameters

contribution_amount_max string<float>

Contribution Amount Range
contribution_amount_min string<float>

Contribution Amount Range
contribution_contributor string

Contribution Contributor Name
contribution_date_after string<date>

Contribution Date Range (Before / After): yyyy-mm-dd
contribution_date_before string<date>

Contribution Date Range (Before / After): yyyy-mm-dd
contribution_honoree string

Contribution Honoree Name
contribution_payee string

Contribution Payee Name
contribution_type any

 Enum:"feca""he""me""ple""pic"

Contribution Type
filing_dt_posted_after string<date-time>

Filing Date Posted Range (Before / After): yyyy-mm-dd
filing_dt_posted_before string<date-time>

Filing Date Posted Range (Before / After): yyyy-mm-dd
filing_period any

 Enum:"mid_year""year_end"

Filing Period
filing_type any

 Enum:"MM""MA""YY""YA"

Filing Type
filing_uuid string<uuid>

filing_uuid
filing_year any

 Enum:2025 2024 2023 2022 2021 2020 2019 2018 2017 2016… 8 more

Filing Year
lobbyist_exclude boolean

Exclude reports filed by the lobbyists.
lobbyist_id integer

Lobbyist ID
lobbyist_name string

Lobbyist Name
ordering string

Which field to use when ordering the results.
page integer

A page number within the paginated result set.
page_size integer

Number of results to return per page.
registrant_id integer

Registrant ID
registrant_name string

Registrant Name

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"count": 123,"next": "/api/v1/{operation}/?page=2","previous": null,"results": [{"url": "http://example.com","filing_uuid": "62b1778e-e2e3-443d-a795-ca3813b6cee5","filing_type": "MM","filing_type_display": "string","filing_year": 2025,"filing_period": "mid_year","filing_period_display": "string","filing_document_url": "string","filing_document_content_type": "string","filer_type": "lobbyist","filer_type_display": "string","dt_posted": "2019-08-24T14:15:22Z","contact_name": "string","comments": "string","address_1": "string","address_2": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"},"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"no_contributions": true,"pacs": ["string"],"contribution_items": [{"contribution_type": "feca","contribution_type_display": "string","contributor_name": "string","payee_name": "string","honoree_name": "string","amount": "string","date": "2019-08-24"}]}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Contribution-Reports/operation/retrieveContributionReport)retrieveContributionReport
--------------------------------------------------------------------------------------------------------------------------------

get/api/v1/contributions/{filing_uuid}/

<https://lda.senate.gov/api/v1/contributions/{filing_uuid}/>

Returns all contributions matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### path Parameters

filing_uuid

required string<uuid>

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"url": "http://example.com","filing_uuid": "62b1778e-e2e3-443d-a795-ca3813b6cee5","filing_type": "MM","filing_type_display": "string","filing_year": 2025,"filing_period": "mid_year","filing_period_display": "string","filing_document_url": "string","filing_document_content_type": "string","filer_type": "lobbyist","filer_type_display": "string","dt_posted": "2019-08-24T14:15:22Z","contact_name": "string","comments": "string","address_1": "string","address_2": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"},"lobbyist": {"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string"},"no_contributions": true,"pacs": ["string"],"contribution_items": [{"contribution_type": "feca","contribution_type_display": "string","contributor_name": "string","payee_name": "string","honoree_name": "string","amount": "string","date": "2019-08-24"}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Registrants)Registrants
===================================================================

Access Registrant information.

[](https://lda.senate.gov/api/redoc/v1/#tag/Registrants/operation/listRegistrants)listRegistrants
-------------------------------------------------------------------------------------------------

get/api/v1/registrants/

<https://lda.senate.gov/api/v1/registrants/>

Returns all registrants matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### query Parameters

country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Country
dt_updated_after string<date-time>

Date Update Range (Before / After): yyyy-mm-dd
dt_updated_before string<date-time>

Date Update Range (Before / After): yyyy-mm-dd
id integer

ID
ordering string

Which field to use when ordering the results.
page integer

A page number within the paginated result set.
page_size integer

Number of results to return per page.
ppb_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

PPB Country
registrant_name string

Name
state any

 Enum:"AL""AK""AS""AZ""AR""AA""AE""AP""CA""CO"… 49 more

State

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"count": 123,"next": "/api/v1/{operation}/?page=2","previous": null,"results": [{"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Registrants/operation/retrieveRegistrant)retrieveRegistrant
-------------------------------------------------------------------------------------------------------

get/api/v1/registrants/{id}/

<https://lda.senate.gov/api/v1/registrants/{id}/>

Returns all registrants matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### path Parameters

id

required integer

A unique integer value identifying this Registrant.

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

`{"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Clients)Clients
===========================================================

Access Client information.

[](https://lda.senate.gov/api/redoc/v1/#tag/Clients/operation/listClients)listClients
-------------------------------------------------------------------------------------

get/api/v1/clients/

<https://lda.senate.gov/api/v1/clients/>

Returns all clients matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### query Parameters

client_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Client Country
client_name string

Client Name
client_ppb_country any

 Enum:"US""CA""""00""AF""AX""AL""DZ""AS""AD"… 244 more

Client PPB Country
client_ppb_state any

 Enum:"AL""AK""AS""AZ""AR""AA""AE""AP""CA""CO"… 49 more

Client PPB State
client_state any

 Enum:"AL""AK""AS""AZ""AR""AA""AE""AP""CA""CO"… 49 more

Client State
id integer

ID
ordering string

Which field to use when ordering the results.
page integer

A page number within the paginated result set.
page_size integer

Number of results to return per page.
registrant_id integer

Registrant ID
registrant_name string

Registrant Name

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"count": 123,"next": "/api/v1/{operation}/?page=2","previous": null,"results": [{"id": 0,"url": "http://example.com","client_id": "string","name": "string","general_description": "string","client_government_entity": true,"client_self_select": true,"state": "AL","state_display": "string","country": "US","country_display": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string","effective_date": "2019-08-24","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Clients/operation/retrieveClient)retrieveClient
-------------------------------------------------------------------------------------------

get/api/v1/clients/{id}/

<https://lda.senate.gov/api/v1/clients/{id}/>

Returns all clients matching the provided filters.

##### Authorizations

_ApiKeyAuth_

##### path Parameters

id

required integer

A unique integer value identifying this Client.

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"id": 0,"url": "http://example.com","client_id": "string","name": "string","general_description": "string","client_government_entity": true,"client_self_select": true,"state": "AL","state_display": "string","country": "US","country_display": "string","ppb_state": "AL","ppb_state_display": "string","ppb_country": "US","ppb_country_display": "string","effective_date": "2019-08-24","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Lobbyists)Lobbyists
===============================================================

Access Lobbyist information.

[](https://lda.senate.gov/api/redoc/v1/#tag/Lobbyists/operation/listLobbyists)listLobbyists
-------------------------------------------------------------------------------------------

get/api/v1/lobbyists/

<https://lda.senate.gov/api/v1/lobbyists/>

Returns all lobbyists matching the provided filters. The ID is a unique integer value identifying this Lobbyist Name as reported by this Registrant.

##### Authorizations

_ApiKeyAuth_

##### query Parameters

id integer

ID
lobbyist_name string

Lobbyist Name
ordering string

Which field to use when ordering the results.
page integer

A page number within the paginated result set.
page_size integer

Number of results to return per page.
registrant_id integer

Registrant ID
registrant_name string

Registrant Name

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"count": 123,"next": "/api/v1/{operation}/?page=2","previous": null,"results": [{"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}}]}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Lobbyists/operation/retrieveLobbyist)retrieveLobbyist
-------------------------------------------------------------------------------------------------

get/api/v1/lobbyists/{id}/

<https://lda.senate.gov/api/v1/lobbyists/{id}/>

Returns all lobbyists matching the provided filters. The ID is a unique integer value identifying this Lobbyist Name as reported by this Registrant.

##### Authorizations

_ApiKeyAuth_

##### path Parameters

id

required integer

A unique integer value identifying this Lobbyist.

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`{"id": 0,"prefix": "dr","prefix_display": "string","first_name": "string","nickname": "string","middle_name": "string","last_name": "string","suffix": "jr","suffix_display": "string","registrant": {"id": 0,"url": "http://example.com","house_registrant_id": 0,"name": "string","description": "string","address_1": "string","address_2": "string","address_3": "string","address_4": "string","city": "string","state": "AL","state_display": "string","zip": "string","country": "US","country_display": "string","ppb_country": "US","ppb_country_display": "string","contact_name": "string","contact_telephone": "string","dt_updated": "2019-08-24T14:15:22Z"}}`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants)Constants
===============================================================

An assorted list of constants found in the LDA REST API.

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listFilingTypes)listFilingTypes
-----------------------------------------------------------------------------------------------

get/api/v1/constants/filing/filingtypes/

<https://lda.senate.gov/api/v1/constants/filing/filingtypes/>

Returns all FilingTypes.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listLobbyingActivityGeneralIssues)listLobbyingActivityGeneralIssues
-----------------------------------------------------------------------------------------------------------------------------------

get/api/v1/constants/filing/lobbyingactivityissues/

<https://lda.senate.gov/api/v1/constants/filing/lobbyingactivityissues/>

Returns all LobbyingActivityGeneralIssues.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listGovernmentEntities)listGovernmentEntities
-------------------------------------------------------------------------------------------------------------

get/api/v1/constants/filing/governmententities/

<https://lda.senate.gov/api/v1/constants/filing/governmententities/>

Returns all GovernmentEntities.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"id": 0,"name": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listCountries)listCountries
-------------------------------------------------------------------------------------------

get/api/v1/constants/general/countries/

<https://lda.senate.gov/api/v1/constants/general/countries/>

Returns all Countries.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listStates)listStates
-------------------------------------------------------------------------------------

get/api/v1/constants/general/states/

<https://lda.senate.gov/api/v1/constants/general/states/>

Returns all States.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listLobbyistPrefixes)listLobbyistPrefixes
---------------------------------------------------------------------------------------------------------

get/api/v1/constants/lobbyist/prefixes/

<https://lda.senate.gov/api/v1/constants/lobbyist/prefixes/>

Returns all LobbyistPrefixes.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listLobbyistSuffixes)listLobbyistSuffixes
---------------------------------------------------------------------------------------------------------

get/api/v1/constants/lobbyist/suffixes/

<https://lda.senate.gov/api/v1/constants/lobbyist/suffixes/>

Returns all LobbyistSuffixes.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[](https://lda.senate.gov/api/redoc/v1/#tag/Constants/operation/listContributionItemTypes)listContributionItemTypes
-------------------------------------------------------------------------------------------------------------------

get/api/v1/constants/contribution/itemtypes/

<https://lda.senate.gov/api/v1/constants/contribution/itemtypes/>

Returns all ContributionItemTypes.

##### Authorizations

_ApiKeyAuth_

### Responses

**200**

**400**
Bad Request

**401**
Unauthorized

**404**
Not Found

**405**
Method Not Allowed

**429**
Too Many Requests - Throttled

### Response samples

* 200
* 400
* 401
* 404
* 405
* 429

Content type

application/json

Copy

 Expand all  Collapse all

`[{"name": "string","value": "string"}]`

[Back to Top](https://lda.senate.gov/api/redoc/v1/#)

**For information on the Lobbying Disclosure Act (LDA):**

* Visit [disclosure.senate.gov](https://disclosure.senate.gov/)

* Call the Lobby Line (202) 224-0758

* Email [lobby@sec.senate.gov](mailto:lobby@sec.senate.gov)

* [Download API](https://lda.senate.gov/api/)
