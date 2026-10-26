def user_role_context(request):
    """Context processor providing quick role shortcuts to all templates."""
    if not request.user.is_authenticated:
        return {
            'is_reporter': False,
            'is_investigator': False,
            'is_safety_manager': False,
            'is_administrator': False,
            'user_role': None,
        }
    
    return {
        'is_reporter': request.user.is_reporter,
        'is_investigator': request.user.is_investigator,
        'is_safety_manager': request.user.is_safety_manager,
        'is_administrator': request.user.is_administrator,
        'user_role': request.user.role,
        'user_role_display': request.user.get_role_display(),
    }
