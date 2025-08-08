import yaml

# Optional: filter None values from lists
def clean_list(lst):
    return [x for x in lst if x is not None]

def export_workspace_to_yaml(filepath, transformer_data, wire_data, circuit_data=None, core_info=None, repo_info=None, result_data=None):
    export_dict = {
        "transformer": transformer_data,
        "wire": wire_data,
        "circuit": circuit_data
    }

    # if core_info:
    #     export_dict["core"] = core_info
    # if repo_info:
    #     export_dict["repo"] = repo_info
    # if result_data:
    #     export_dict["result"] = result_data

    with open(filepath, "w") as f:
        yaml.dump(export_dict, f, sort_keys=False)
    print(f"[INFO] Exported full workspace to {filepath}")


def import_workspace_from_yaml(filepath):
    with open(filepath, "r") as f:
        return yaml.safe_load(f)