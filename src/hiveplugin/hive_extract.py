import json
import re
from datetime import datetime


def extract(raw_data):
    """Extract data from the input raw data."""
    p = re.compile("#.*Diagnostics$")
    ep = re.compile("#.*Thermocouples.*")
    nep = re.compile("#.*Campaign Description.*")
    to_start_from = 0
    to_stop_on = 0
    dictionary_to_be_converted = {}
    dictionary_to_be_converted_for_thermocouple = {}
    sub_fields_of_thermocouple = []

    # Find the start index for the diagnostics data
    for index, d in enumerate(raw_data):
        found = p.match(d)
        if found:
            to_start_from = index + 4
            break

    # Find the stop index for the diagnostics data
    for index, d in enumerate(raw_data):
        end_found = ep.match(d)
        if end_found:
            to_stop_on = index
            break

    # Find the stop index for the Thermocouple data
    for index, d in enumerate(raw_data):
        end_found_thermocouple = nep.match(d)
        if end_found_thermocouple:
            to_stop_on_for_thermocouple = index
            break

    # Check if a valid start index was found for Diagnostics
    if to_start_from == 0:
        print("No Matching Data Found for Diagnostics Block")
    else:
        print(
            "****************** Started scanning for Diagnostics **********************"
        )
        print(f"Our Data scanning has to be start from: {to_start_from}")
        print(f"Our Data scanning has to be stop on: {to_stop_on}")

        # Extract key-value pairs from the specified lines
        for i in range(to_start_from, to_stop_on):
            if len(raw_data[i].strip()) > 0:
                key, value = raw_data[i].strip().split(":")
                if " x " in value:
                    e1, e2 = (
                        value.split(" x ")[0],
                        value.split(" x ")[1].split(" ")[0],
                    )
                    dictionary_to_be_converted[key] = [e1, e2]
                else:
                    dictionary_to_be_converted[key] = value

    # Check if a valid start index was found for Thermocouple
    if to_stop_on == 0:
        print("No Matching data for Thermocouple Block")
    else:
        print(
            "****************** Started scanning for Thermocouple **********************"
        )
        print(f"Our Data scanning has to be start from: {to_stop_on + 4}")
        print(f"Our Data scanning has to be stop on: {to_stop_on_for_thermocouple}")

        try:
            for i in range(to_stop_on + 2, to_stop_on_for_thermocouple):
                if raw_data[i].startswith("#"):
                    sub_fields_of_thermocouple.append(i)
            sub_fields_of_thermocouple.append(to_stop_on_for_thermocouple)

            # Extract key-value pairs from the specified lines
            for driver in range(len(sub_fields_of_thermocouple) - 1):
                temp = dict()
                for i in range(
                    sub_fields_of_thermocouple[driver] + 1,
                    sub_fields_of_thermocouple[driver + 1],
                ):
                    if len(raw_data[i].strip()) > 0:
                        key, value = raw_data[i].strip().split(":")[:2]
                        if "[" in value and "]" in value:
                            mid_value = re.sub(
                                r"[^0-9.,]",
                                "",
                                value.split("=")[1].strip().split("mm")[0],
                            )
                            c1, c2, c3 = mid_value.split(",")
                            temp[key] = [c1, c2, c3]
                        else:
                            temp[key] = value
                dictionary_to_be_converted_for_thermocouple[
                    raw_data[sub_fields_of_thermocouple[driver]]
                    .strip()
                    .replace("#", "")
                    .replace(" ", "")
                ] = temp
        except Exception as e:
            print("Error: ", str(e))
    # Generating expected result
    
    extracted_data = {
        "diagnostics_properties": dictionary_to_be_converted,
        "thermocouple_properties": dictionary_to_be_converted_for_thermocouple,
    }

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
                                "pulseStart": datetime.now().isoformat(),
                                "pulseDuration": 300,
                                "dataCaptureStart": datetime.now().isoformat(),
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
