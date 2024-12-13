"""Custom Location Import Job."""

from csv import DictReader
from nautobot.apps.jobs import Job, TextVar, register_jobs
from nautobot.extras.models import (
    Status,
)
from nautobot.dcim.models import (
    Location,
    LocationType,
)

name = "Import Locations"

REQUIRED_HEADERS = ["name", "city", "state"]


class ImportLocationsCSV(Job):
    """Create objects from only one of three methods: CSV file, CSV text, or manual input fields."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta object for Import Locations Job"""

        name = "Perform Location Import from CSV"
        description = "Import locations from CSV text"
        has_sensitive_variables = False

    input_csv = TextVar(
        label="Location CSV Data",
        description="Headers: name,city,state",
        required=True,
    )

    def run(self, *args, **data):
        """Process CSV data to import locations."""

        input_csv = data.get("input_csv")
        loc_csv_data = self.validate_data(input_csv)
        self.create_locations(loc_csv_data)

    def validate_data(self, input_csv):
        """
        The purpose of this function is to ensure that the input data has the required headers and that none of the values are empty.
        """
        loc_csv_data = list(DictReader(input_csv.splitlines()))
        self.logger.info("Validating data...")
        if not loc_csv_data:
            msg = "Only one row detected, please provide data to import."
            self.logger.exception(msg)
            raise ValueError(msg)
        if (
            not all(header in loc_csv_data[0] for header in REQUIRED_HEADERS)
            or len(loc_csv_data[0]) != 3
        ):
            msg = "Missing or extra header. Please ensure that the headers are correct."
            self.logger.exception(msg)
            raise ValueError(msg)
        if not all(
            value not in (None, "") for item in loc_csv_data for value in item.values()
        ):
            msg = "None or empty value detected"
            self.logger.exception(msg)
            raise ValueError(msg)
        return loc_csv_data

    def create_locations(self, loc_csv_data):
        """
        The purpose of this function is to create the locations if they don't already exist.
        """
        self.logger.info("Importing locations: %s", loc_csv_data)

        state_type = LocationType.objects.get(name="State")
        city_type = LocationType.objects.get(name="City")
        active_status = Status.objects.get(name="Active")

        for loc_data in loc_csv_data:
            # Create state location
            state_loc, state_created = Location.objects.get_or_create(
                name=loc_data["state"],
                location_type=state_type,
                defaults={"status": active_status},
            )
            if state_created:
                self.logger.info("State location %s created", state_loc)

            # Create city location
            city_loc, city_created = Location.objects.get_or_create(
                name=loc_data["city"],
                location_type=city_type,
                parent=state_loc,
                defaults={"status": active_status},
            )
            if city_created:
                self.logger.info("City location %s created", city_loc)

            # Determine site type based on name
            site_type = LocationType.objects.get(
                name="Data Center" if "DC" in loc_data["name"] else "Branch"
            )

            # Create final location
            location, created = Location.objects.get_or_create(
                name=loc_data["name"],
                location_type=site_type,
                parent=city_loc,
                defaults={"status": active_status},
            )
            if created:
                self.logger.info("Location %s created", location)

register_jobs(ImportLocationsCSV)
