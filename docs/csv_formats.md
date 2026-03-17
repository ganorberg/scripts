# CSV Column Mappings

Each lead source uses different CSV column headers. The `--source` flag tells the ingestion which mapping to use.

## Prospeo (`--source prospeo`)

| Our Field      | CSV Column     |
|----------------|----------------|
| email          | Email          |
| first_name     | First Name     |
| last_name      | Last Name      |
| company_name   | Company Name   |
| title          | Title          |
| company_size   | Company Size   |

## Ocean (`--source ocean`)

| Our Field      | CSV Column     |
|----------------|----------------|
| email          | email          |
| first_name     | first_name     |
| last_name      | last_name      |
| company_name   | company        |
| title          | job_title      |
| company_size   | company_size   |

## DiscoLike (`--source discolike`)

| Our Field      | CSV Column     |
|----------------|----------------|
| email          | Email Address  |
| first_name     | First Name     |
| last_name      | Last Name      |
| company_name   | Company        |
| title          | Job Title      |
| company_size   | Employees      |

## Generic (`--source generic`)

| Our Field      | CSV Column     |
|----------------|----------------|
| email          | email          |
| first_name     | first_name     |
| last_name      | last_name      |
| company_name   | company_name   |
| title          | title          |
| company_size   | company_size   |

## Custom Mapping

For one-off imports with non-standard columns:

```bash
coldmail ingest --file leads.csv --source generic --campaign-id abc \
  --mapping '{"email": "E-Mail", "first_name": "Name", "company_name": "Org"}'
```

The `--mapping` flag accepts a JSON object mapping our canonical field names to your CSV column headers.
