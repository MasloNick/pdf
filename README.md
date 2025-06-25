# pdf

A simple utility to extract tables from PDF files and export them as CSV.

## Example

```
python process_pdf.py input.pdf output.csv "Column1,Column2,Column3"
```

This command extracts tables from `input.pdf` and writes them to `output.csv`. If no rows are found, the script creates an empty CSV with the specified header row.
