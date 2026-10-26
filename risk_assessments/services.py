from .models import RiskThresholdConfig

def calculate_score_and_level(likelihood, severity):
    """
    Computes score and looks up level from configuration.
    Guarantees client inputs cannot override server logic.
    """
    l = max(1, min(5, int(likelihood)))
    s = max(1, min(5, int(severity)))
    score = l * s

    try:
        config = RiskThresholdConfig.objects.filter(
            min_score__lte=score,
            max_score__gte=score
        ).first()
        if config:
            level = config.band_name
            color = config.color_code
        else:
            level, color = _default_level_and_color(score)
    except Exception:
        level, color = _default_level_and_color(score)

    return {
        'likelihood': l,
        'severity': s,
        'score': score,
        'level': level,
        'color': color,
    }

def _default_level_and_color(score):
    if score <= 4:
        return 'LOW', '#198754'
    elif score <= 9:
        return 'MODERATE', '#ffc107'
    elif score <= 15:
        return 'HIGH', '#fd7e14'
    else:
        return 'CRITICAL', '#dc3545'

def get_risk_matrix():
    """
    Returns 5x5 grid structured from top (Likelihood 5) to bottom (Likelihood 1),
    and left (Severity 1) to right (Severity 5).
    """
    likelihood_labels = {
        5: '5 - Frequent',
        4: '4 - Occasional',
        3: '3 - Remote',
        2: '2 - Improbable',
        1: '1 - Extremely Improbable',
    }
    severity_labels = {
        1: '1 - Negligible',
        2: '2 - Minor',
        3: '3 - Moderate',
        4: '4 - Major',
        5: '5 - Catastrophic',
    }

    matrix = []
    for l in [5, 4, 3, 2, 1]:
        row = {
            'likelihood': l,
            'likelihood_label': likelihood_labels[l],
            'cells': []
        }
        for s in [1, 2, 3, 4, 5]:
            calc = calculate_score_and_level(l, s)
            row['cells'].append({
                'likelihood': l,
                'severity': s,
                'score': calc['score'],
                'level': calc['level'],
                'color': calc['color'],
            })
        matrix.append(row)

    return {
        'matrix': matrix,
        'severity_labels': [severity_labels[s] for s in [1, 2, 3, 4, 5]],
    }
