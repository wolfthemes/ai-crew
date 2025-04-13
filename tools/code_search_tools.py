def search_function(function_name: str, repo_path: str):
    """Searches for a PHP function in the codebase and returns its location."""
    matches = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.php'):
                with open(os.path.join(root, file)) as f:
                    for i, line in enumerate(f):
                        if f"function {function_name}" in line:
                            matches.append((file, i+1, line.strip()))
    return matches
