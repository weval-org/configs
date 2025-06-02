import json
import sys
import os

def validate_blueprint(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"::error file={file_path}::Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"::error file={file_path}::Could not read file: {e}")
        return False

    errors = []
    
    # Check top-level required fields
    if not isinstance(data.get('id'), str) or not data.get('id'):
        errors.append(f"Missing or invalid 'id' (must be a non-empty string).")
    if not isinstance(data.get('title'), str) or not data.get('title'):
        errors.append(f"Missing or invalid 'title' (must be a non-empty string).")
    if not isinstance(data.get('description'), str) or not data.get('description'): # Description is optional in README, but user requested it as required.
        errors.append(f"Missing or invalid 'description' (must be a non-empty string).")

    # Check 'prompts' array
    prompts = data.get('prompts')
    if not isinstance(prompts, list) or not prompts:
        errors.append(f"Missing or empty 'prompts' array (must be a non-empty list).")
    else:
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                errors.append(f"Prompt at index {i} is not a valid object.")
                continue

            prompt_id_text = f" (prompt id: {prompt.get('id', 'N/A')})" if isinstance(prompt.get('id'), str) else f" (prompt index: {i})"

            if not isinstance(prompt.get('promptText'), str) or not prompt.get('promptText'):
                errors.append(f"Missing or invalid 'promptText' in prompt{prompt_id_text} (must be a non-empty string).")
            if not isinstance(prompt.get('idealResponse'), str) or not prompt.get('idealResponse'):
                errors.append(f"Missing or invalid 'idealResponse' in prompt{prompt_id_text} (must be a non-empty string).")
            
            points = prompt.get('points')
            if not isinstance(points, list) or not points:
                errors.append(f"Missing or empty 'points' array in prompt{prompt_id_text} (must be a non-empty list of strings).")
            else:
                for j, point_entry in enumerate(points):
                    if not isinstance(point_entry, str) or not point_entry:
                        errors.append(f"Point at index {j} in prompt{prompt_id_text} is not a non-empty string.")
                        
    if errors:
        for error in errors:
            print(f"::error file={file_path}::{error}")
        return False
    
    print(f"::notice file={file_path}::Validation passed for {os.path.basename(file_path)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_blueprints.py <file_path1> [<file_path2> ...]")
        sys.exit(1)
    
    all_valid = True
    for file_path_arg in sys.argv[1:]:
        if not os.path.exists(file_path_arg):
            print(f"::error file={file_path_arg}::File not found.")
            all_valid = False
            continue
        if not validate_blueprint(file_path_arg):
            all_valid = False
            
    if not all_valid:
        sys.exit(1) 