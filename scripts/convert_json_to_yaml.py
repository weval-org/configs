#!/usr/bin/env python
import json
import yaml
import argparse
import os
from pathlib import Path

# --- Field Name Mappings ---
HEADER_MAPPING = {
    "configId": "id",
    "configTitle": "title"
}

PROMPT_MAPPING = {
    "promptText": "prompt",
    "idealResponse": "ideal",
    "points": "should",
    "expect": "should",
    "expects": "should",
    "expectations": "should"
}

POINT_FN_MAPPING = {
    "fnArgs": "arg",
    "multiplier": "weight"
}

# --- Transformation Logic ---

def transform_point(point):
    """Transforms a single point from the old JSON format to the new YAML structure."""
    if isinstance(point, str):
        return point
    
    if isinstance(point, list) and len(point) == 2:
        # Handles ["fnName", "fnArg"] format
        return {point[0]: point[1]}
        
    if isinstance(point, dict):
        # Handles full point objects
        new_point = {}
        for key, value in point.items():
            new_key = POINT_FN_MAPPING.get(key, key)
            new_point[new_key] = value
        return new_point
        
    return point

def transform_prompt(prompt_data):
    """Transforms a single prompt object."""
    new_prompt = {}
    for key, value in prompt_data.items():
        new_key = PROMPT_MAPPING.get(key, key)
        if new_key == 'should' and isinstance(value, list):
            new_prompt[new_key] = [transform_point(p) for p in value]
        else:
            new_prompt[new_key] = value
    return new_prompt

def represent_multiline_string(dumper, data):
    """Use literal block scalar for multiline strings."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def convert_json_to_yaml(json_data):
    """Converts a loaded JSON blueprint object to the YAML multi-document format string."""
    header = {}
    prompts = json_data.pop("prompts", [])

    # All remaining keys are considered part of the header
    for key, value in json_data.items():
        new_key = HEADER_MAPPING.get(key, key)
        header[new_key] = value

    # Ensure our custom representer for multiline strings is active
    yaml.add_representer(str, represent_multiline_string)

    # Transform all prompts
    transformed_prompts = [transform_prompt(p) for p in prompts]
    
    # Dump each prompt as its own YAML document
    prompt_documents = [yaml.dump(p, sort_keys=False, width=1000) for p in transformed_prompts]
    
    # Join the prompt documents into a single stream string
    prompts_stream = ""
    if prompt_documents:
        # We trim the trailing newline from each doc before joining
        # to prevent extra blank lines between documents.
        prompts_stream = "\n---\n".join([doc.strip() for doc in prompt_documents])

    # If there's a header, prepend it to the prompts stream
    if header:
        header_yaml = yaml.dump(header, sort_keys=False, width=1000).strip()
        # Handle case where there are no prompts but there is a header
        if not prompts_stream:
            return header_yaml
        return f"{header_yaml}\n---\n{prompts_stream}"
    else:
        # Otherwise, just return the stream of prompts
        return prompts_stream

# --- File Handling ---

def process_file(input_path, output_path):
    """Reads a JSON file, converts it, and writes to a YAML file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        yaml_output = convert_json_to_yaml(json_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_output)
            
        print(f"✅ Converted '{input_path}' -> '{output_path}'")

    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in '{input_path}'. Skipping.")
    except Exception as e:
        print(f"❌ Error processing '{input_path}': {e}")


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert CivicEval JSON blueprints to the new YAML format.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="blueprints/",
        help="Path to a specific JSON file or a directory containing JSON files. Defaults to 'blueprints/'."
    )
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Delete the original JSON file after a successful conversion."
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.path)
    
    if not input_path.exists():
        print(f"❌ Error: Path '{input_path}' does not exist.")
        return

    if input_path.is_dir():
        print(f"Searching for .json files in '{input_path}'...")
        json_files = list(input_path.glob("*.json"))
        if not json_files:
            print("No JSON files found to convert.")
            return
            
        for json_file in json_files:
            output_file = json_file.with_suffix(".yml")
            process_file(json_file, output_file)
            if args.delete_originals:
                os.remove(json_file)
                print(f"🗑️ Deleted original file: '{json_file}'")

    elif input_path.is_file():
        if input_path.suffix.lower() != ".json":
            print(f"❌ Error: Expected a .json file, but got '{input_papearanceath}'.")
            return
            
        output_file = input_path.with_suffix(".yml")
        process_file(input_path, output_file)
        if args.delete_originals:
            os.remove(input_path)
            print(f"🗑️ Deleted original file: '{input_path}'")

    else:
        print(f"❌ Error: Path '{input_path}' is not a valid file or directory.")


if __name__ == "__main__":
    main() 