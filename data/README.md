# Data Directory

This directory is used to store the Guru Granth Sahib data files:

1. `guru_granth_sahib.pdf` - The English translation of the Guru Granth Sahib in PDF format
2. `gurbani_english_enhanced_chunks.csv` - Processed chunks of text extracted from the PDF

## Obtaining the PDF

To obtain the English translation of the Guru Granth Sahib in PDF format, you can:

1. Download it from SikhNet: https://www.sikhnet.com/pages/guru-granth-sahib
2. Or download it from GurbaniFiles: https://www.gurbanifiles.org/

Place the downloaded PDF file in this directory and rename it to `guru_granth_sahib.pdf`.

## Processing the Data

Once you have the PDF, you can process it by running:

```bash
python -m app.process_data
```

This will:
1. Read the PDF
2. Extract and clean the text
3. Split the text into manageable chunks
4. Generate embeddings for each chunk
5. Store the chunks in ChromaDB
6. Save a copy of the processed data as `gurbani_english_enhanced_chunks.csv`

## Using Pre-processed Data

If you already have the `gurbani_english_enhanced_chunks.csv` file, place it in this directory and run:

```bash
python -m app.process_data
```

The application will detect the CSV file and load it directly into ChromaDB without needing to process the PDF again.

## Notes on Data Processing

- The application extracts English translations only, filtering out Gurmukhi script and transliterations
- The text is cleaned and structured into chunks of approximately 200 words each
- Metadata such as Ang (page) numbers, sections, and Raags are extracted and stored with each chunk
- Embedding vectors are generated for semantic search capabilities