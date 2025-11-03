# Contract Generator Setup Guide

## Overview

The Contract Generator feature allows lawyers to:
1. Select a contract template
2. Fill in smart form fields
3. Generate a finalized PDF contract instantly

## Backend Setup

### Database Tables

The following tables are automatically created on startup:
- `contract_templates` - Stores template definitions
- `contracts` - Stores generated contracts

### Optional Dependencies

For full functionality, install these optional packages:

```bash
# For DOCX template rendering (recommended)
pip install docxtpl

# For HTML to PDF conversion (recommended)
pip install weasyprint

# LibreOffice for DOCX to PDF conversion (system-level, optional)
# Install via system package manager:
# Ubuntu/Debian: sudo apt-get install libreoffice
# macOS: brew install libreoffice
# Windows: Download from https://www.libreoffice.org/
```

**Note:** The service includes fallbacks:
- Without `docxtpl`: Uses basic python-docx for simple text replacement
- Without `weasyprint`: Generates HTML files instead of PDFs
- Without LibreOffice: Returns DOCX files instead of converting to PDF

### Environment Variables

Add to your `.env` file:

```env
# Contract storage path (default: ./storage/generated)
CONTRACT_STORAGE_PATH=./storage/generated

# Backend URL for generating PDF download links
BACKEND_URL=http://localhost:8000
# Or in production:
BACKEND_URL=https://api.fastestfranchise.net
```

### Creating Templates

To add a template, insert into `contract_templates` table:

```sql
INSERT INTO contract_templates (
    id, title, description, category, file_path, format, variables, is_active
) VALUES (
    'uuid-here',
    'Employment Agreement',
    'Standard employment contract template',
    'Employment',
    '/path/to/template.docx',
    'docx',
    '[
        {
            "name": "partyA_name",
            "label": "Party A Name",
            "type": "text",
            "required": true,
            "placeholder": "Enter company name"
        },
        {
            "name": "partyB_name",
            "label": "Party B Name",
            "type": "text",
            "required": true
        },
        {
            "name": "start_date",
            "label": "Start Date",
            "type": "date",
            "required": true
        },
        {
            "name": "amount",
            "label": "Contract Amount",
            "type": "number",
            "required": false
        }
    ]',
    true
);
```

### Template Formats

#### DOCX Templates

Use `{{variable_name}}` syntax in your DOCX file:
```
This agreement is between {{partyA_name}} and {{partyB_name}}.
Effective date: {{start_date}}.
```

#### HTML Templates

Use Jinja2 syntax:
```html
<h1>Contract Agreement</h1>
<p>This agreement is between {{ partyA_name }} and {{ partyB_name }}.</p>
<p>Effective date: {{ start_date }}.</p>
```

## Frontend

The frontend is already integrated. Users can:
1. Browse templates at `/dashboard/templates`
2. Click "Use" on any template
3. Fill the dynamic form at `/dashboard/templates/[id]/use`
4. Generate and download the PDF

## API Endpoints

- `GET /api/v1/templates/{template_id}/variables` - Get template variables
- `POST /api/v1/templates/{template_id}/generate` - Generate contract
- `GET /api/v1/templates/contracts/{contract_id}/download` - Download generated contract

## Testing

1. Start the backend server
2. Create a test template in the database
3. Navigate to `/dashboard/templates`
4. Click "Use" on a template
5. Fill the form and generate

## Troubleshooting

### PDF generation fails
- Check if LibreOffice is installed (for DOCX conversion)
- Check file permissions on storage directory
- Review logs for specific error messages

### Template variables not loading
- Verify template exists and is active
- Check JSON format of variables field
- Ensure template_id is correct UUID

### Download fails
- Verify contract exists
- Check user owns the contract
- Verify file path exists on server

