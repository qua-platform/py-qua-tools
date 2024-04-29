def _extract_elements(d: dict) -> list[str]:
    if 'qe' in d:
        if isinstance(d['qe'], str):
            return [d['qe']]
        elif isinstance(d['qe'], list):
            return [qe['name'] for qe in d['qe']]
        elif isinstance(d['qe'], dict):
            return [d['qe']['name']]
        else:
            raise NotImplementedError()
    else:
        elements = []

    return elements
