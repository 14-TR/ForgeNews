import shutil


def enrich_summary_file(input_path: str, output_path: str):
    """
    Read a summary JSON, geocode locations, aggregate metrics by event type,
    and write the enriched summary to a new JSON file.
    """
    # Temporary stub: copy input summary to output until spatial enrichment is implemented
    shutil.copy(input_path, output_path) 