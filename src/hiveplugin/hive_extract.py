import json
import re
from datetime import datetime


def extract(raw_data):
    """Extract data from the input raw data."""
    p = re.compile("#.*Diagnostics$")
    ep = re.compile("#.*Thermocouples.*")

    start_index = 0
    end_index = 0

    extracted_data = {}

    for index, line in enumerate(raw_data):
        if p.match(line) and start_index == 0:
            start_index = index + 4
        elif ep.match(line):
            end_index = index
            break

    if start_index == 0:
        return None

    for line in raw_data[start_index:end_index]:
        line = line.strip()
        if line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if " x " in value:
                e1, e2 = value.split(" x ")
                e2 = e2.split()[0]
                extracted_data[key] = [e1.strip(), e2.strip()]
            else:
                extracted_data[key] = value

    return extracted_data


def build(extracted_data):
    """Build the final JSON structure with the extracted data."""

    built_data = {
        "owner": "Jane Doe",
        "contactEmail": "jane.doe@ukaea.uk",
        "creationTime": datetime.now().isoformat(),
        "type": "raw",
        "sourceFolder": "/path/to/data",
        "ownerGroup": "UKAEA",
        "principalInvestigator": "Jane Doe",
        "creationLocation": "Culham",
        "scientificMetadata": {
            "ukaea": {
                "identifier": "UKAEA-123",
                "creator": "Jane Doe",
                "workflowType": "facility",
                "isPublished": "false",
                "quality": "unchecked",
                "facility": {
                    "facility_id": "HIVE",
                    "location": "Culham",
                    "HIVE": {
                        "campaign": {
                            "campaignID": "HIVE-123",
                            "campaignStart": datetime.now().isoformat(),
                        },
                        "experiment": {
                            "campaignID": "HIVE-123",
                            "experimentID": "HIVE-E-123",
                            "leadInvestigator": "Jane Doe",
                            "testType": "Diagnostics",
                            "sampleCooling": "false",
                            "pulse": {
                                "pulseID": "123e4567-e89b-12d3-a456-426614174000",
                                "operator1": "Jane Doe",
                                "operator2": "John Smith",
                                "pulseStart": "2024-09-03T10:00:00Z",
                                "pulseDuration": 300,
                                "dataCaptureStart": "2024-09-03T09:59:55Z",
                                "pulseQuality": "Success",
                                "currentHeatingInformation": {},
                                "coolantInformation": {
                                    "coolantType": "Water",
                                    "coolantFlow": {
                                        "rate": "High",
                                        "setpoint": 100,
                                        "value": 98.5,
                                        "variance": 1.5
                                    },
                                    "coolantTemperature": {
                                        "setpoint": 20,
                                        "in": 19.5,
                                        "inVariance": 0.5,
                                        "out": 22,
                                        "outVariance": 0.5,
                                        "delta": 2.5
                                    },
                                    "coolantPressure": {
                                        "in": 2.5,
                                        "out": 2.3,
                                        "delta": 0.2
                                    }
                                }
                            },
                        },
                    }
                },
                "diagnostics": extracted_data,
            }
        }
    }

    return built_data


def save(built_data, output_file):
    """Save JSON content to the output file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(built_data, f, indent=2)
    except Exception as e:
        raise Exception(f"Error during data saving: {str(e)}")


def run_extraction(input_file, output_file, schema):
    """Run the extraction process and return the final JSON."""
    try:
        with open(input_file, "r") as f:
            raw_data = f.readlines()

        extracted_data = extract(raw_data)

        if extracted_data:
            built_data = build(extracted_data)

            if output_file:
                save(built_data, output_file)

            return built_data
        else:
            print("No data extracted")
            return None
    except Exception as e:
        print(f"Error during extraction process: {str(e)}")
        return None
