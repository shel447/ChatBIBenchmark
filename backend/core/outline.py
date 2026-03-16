from .normalization import _normalize_string


def _flatten_node(node, path, paths):
    if not isinstance(node, dict):
        return
    title = _normalize_string(node.get("title") or node.get("name") or "")
    if title:
        next_path = path + [title]
        paths.add(tuple(next_path))
    else:
        next_path = path
    for child in node.get("sections", []) or []:
        _flatten_node(child, next_path, paths)


def flatten_outline_paths(outline):
    paths = set()
    if outline is None:
        return paths
    if isinstance(outline, list):
        for item in outline:
            _flatten_node(item, [], paths)
        return paths
    _flatten_node(outline, [], paths)
    return paths
