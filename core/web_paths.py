import base64


def _d(s: str) -> str:
    """Decodes a selector at runtime."""
    return base64.b64decode(s).decode("utf-8")


class WebPaths:

    # --- FIRST PAGE
    HEADER_DASHBOARD    = _d("ZGl2LmRhc2hib2FyZC1pdGVtLWhlYWRlcg==")
    BTN_EXPAND_FILTER   = _d("ZGl2LmZpbHRyb3MudmNlbnRlci5wYS01")
    INPUT_RECORD_NR     = _d("aW5wdXQjaXROclByb2Nlc3Nv")
    BTN_SEARCH          = _d("YnV0dG9uLmJ0bi5idG4tcHJpbWFyeQ==")
    TASK_LIST_ITEM      = _d("ZGl2LmRldGFsaGVUYXJlZmFzUXVhbnRpZGFkZQ==")
    HEADER_TASKS        = _d("Zm9sbG93aW5nLXNpYmxpbmc6OnRhcmVmYXNbMV0=")

    # --- SECOND PAGE
    BTN_PROCESS         = _d("ZGl2LnNlbGVjaW9uYXJQcm9jZXNzbyBidXR0b24uYm90YW8tc2VsZWNpb25hcg==")
    BTN_LINK            = _d("YnV0dG9uW3RpdGxlPSdWaW5jdWxhciBldGlxdWV0YSddLCBidXR0b25bZGF0YS10YXJnZXQ9JyNtb2RhbEV0aXF1ZXRhckxvdGUnXQ==")
    INPUT_SEARCH        = _d("aW5wdXQjaXRQZXNxdWlzYXJFdGlxdWV0YXM=")
    CHK_LABEL           = _d("YnV0dG9uLmJvdGFvLXNlbGVjaW9uYXIuY2hlY2stZXRpcXVldGEsIGJ1dHRvbi5jaGVjay1ldGlxdWV0YS5ib3Rhby1zZWxlY2lvbmFy")

    # --- STATIC XPATH
    BTN_CONFIRM_LINK    = _d("Ly9idXR0b25bY29udGFpbnMoQGNsYXNzLCdidG4tZGVmYXVsdCcpXVsuLy9zcGFuW2NvbnRhaW5zKC4sJ1ZpbmN1bGFyIGV0aXF1ZXRhJyldXQ==")

    # --- DYNAMIC XPATH
    SUGGESTION_TEMPLATES: tuple = tuple(_d(t) for t in (
        "Ly9kaXZbY29udGFpbnMoQGNsYXNzLCAnc3VnZ2VzdGlvbicpIG9yIGNvbnRhaW5zKEBjbGFzcywgJ3JpY2gtc3VnZ2VzdGlvbi1lbnRyeScpXS8vKltjb250YWlucyh0cmFuc2xhdGUoLiwnYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXonLCdBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWicpLCAne30nKV0=",
        "Ly9zcGFuW2NvbnRhaW5zKHRyYW5zbGF0ZSguLCdhYmNkZWZnaGlqa2xtbm9wcXJzdHV2d3h5eicsJ0FCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaJyksICd7fScpXQ==",
        "Ly9saVtjb250YWlucyh0cmFuc2xhdGUoLiwnYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXonLCdBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWicpLCAne30nKV0=",
    ))