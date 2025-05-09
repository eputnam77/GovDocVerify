"""Configuration file for terminology rules and mappings."""

# Common replacements from patterns.json terminology section
TERM_REPLACEMENTS = {
    'and/or': 'written sentence breaking up and/or (per AGC)',
    'although': 'though (per DOT OGC Style Guide)',
    'additionally': 'in addition',
    'pursuant to': 'under or following (per Document Drafting Handbook)',
    'in accordance with': 'under or following',
    'in compliance with': 'under or following',
    'cockpit': 'flight deck (per AIR-600 Quick Reference Guide)',
    'flight crew': 'flightcrew (per AIR-600 Quick Reference Guide)',
    'shall': 'must (per FAA Order 1320.46)',
    'cancelled': 'canceled (per the GPO Style Manual)',
    'RGL': 'DRS',
    'Regulatory and Guidance Library': 'Dynamic Regulatory System',
    'chairman': 'chair (per AIR-600 Quick Reference Guide)',
    'flagman': 'flagperson (per AIR-600 Quick Reference Guide)',
    'manmade': 'personmade (per AIR-600 Quick Reference Guide)',
    'manpower': 'labor force (per AIR-600 Quick Reference Guide)'
}

# Terms to avoid (with explanations)
FORBIDDEN_TERMS = {
    'clearly': "Avoid using 'clearly' as it's subjective",
    'obviously': "Avoid using 'obviously' as it's subjective",
    'above': "Avoid using 'above' for references",
    'below': "Avoid using 'below' for references",
    'aforementioned': "Avoid using 'aforementioned' as it can be unclear",
    'latter': "Avoid using 'latter'; specify the item explicitly",
    'former': "Avoid using 'former'; specify the item explicitly",
    'respectively': "Avoid using 'respectively' as it can be confusing",
    'herein': "Avoid archaic terms; use modern, plain language",
    'therein': "Avoid archaic terms; use modern, plain language",
    'thereof': "Avoid archaic terms; use modern, plain language",
    'heretofore': "Avoid archaic terms; use modern, plain language"
}

# Terminology variants to check for consistency
TERMINOLOGY_VARIANTS = {
    'website': ['web site', 'web-site'],
    'online': ['on-line', 'on line'],
    'email': ['e-mail', 'Email'],
    'U.S.C.': ['USC', 'U.S.C'],
    'CFR': ['C.F.R.'],
    'D.C.': ['DC'],
    'U.S.': ['US'],
    'S.E.': ['SE'],
    'E.O.': ['EO']
}
