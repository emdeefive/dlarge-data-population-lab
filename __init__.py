"""Import Jobs."""

from jobs.import_locations import ImportLocationsCSV
from nautobot.core.celery import register_jobs

register_jobs(ImportLocationsCSV)
