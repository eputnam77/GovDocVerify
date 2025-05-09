"""Configuration file for terminology rules and mappings."""

# Common replacements (specific word/phrase replacements only)
TERM_REPLACEMENTS = {
    'and/or': 'written sentence breaking up and/or (per AGC)',
    'although': 'though (per DOT OGC Style Guide)',
    'additionally': 'in addition',
    'cockpit': 'flight deck (per AIR-600 Quick Reference Guide)',
    'flight crew': 'flightcrew (per 14 CFR)',
    'shall': 'must (per FAA Order 1320.46)',
    'cancelled': 'canceled (per the GPO Style Manual)',
    'RGL': 'DRS',
    'Regulatory and Guidance Library': 'Dynamic Regulatory System',
    'chairman': 'chair (per AIR-600 Quick Reference Guide)',
    'flagman': 'flagperson (per AIR-600 Quick Reference Guide)',
    'manmade': 'personmade (per AIR-600 Quick Reference Guide)',
    'manpower': 'labor force (per AIR-600 Quick Reference Guide)',
    'European Aviation Safety Agency': 'European Union Aviation Safety Agency (EASA)',
    'commence': 'begin or start (per Plain Language Guidelines)',
    'terminate': 'end or stop (per Plain Language Guidelines)',
    'transmit': 'send (per Plain Language Guidelines)',
    'demonstrate': 'show or prove (per Plain Language Guidelines)',
    'facilitate': 'help or assist (per Plain Language Guidelines)',
    'utilize': 'use (per Plain Language Guidelines)'
}

# Terms to avoid (only subjective/style terms, not formatting issues)
FORBIDDEN_TERMS = {
    'clearly': "Avoid using 'clearly' as it's subjective",
    'obviously': "Avoid using 'obviously' as it's subjective",
    'aforementioned': "Avoid using 'aforementioned' as it can be unclear",
    'latter': "Avoid using 'latter'; specify the item explicitly",
    'former': "Avoid using 'former'; specify the item explicitly",
    'respectively': "Avoid using 'respectively' as it can be confusing"
}

# Multiple accepted forms - only for terms where either form is acceptable at any point
MULTIPLE_ACCEPTED_FORMS = {
    'Federal Register': ['Fed. Reg.'],  # Both forms equally acceptable
    'Administrator': ['Admin.'],  # Both forms acceptable in headings/text
    'Section': ['§'],  # Both forms acceptable except at start of sentence
    'percent': ['%']  # Both forms acceptable except at start of sentence
}

# Terminology variants to check for consistency (only abbreviation/spelling variants)
TERMINOLOGY_VARIANTS = {
    'website': ['web site', 'web-site'],
    'online': ['on-line', 'on line'],
    'email': ['e-mail', 'Email'],
    # Federal agencies - only checking format variants, not first use
    'FAA': ['F.A.A.', 'Federal Aviation Admin'],  # Not checking first use
    'NASA': ['N.A.S.A.'],
    'DOT': ['D.O.T.', 'Dept. of Transportation'],
    'EPA': ['E.P.A.'],
    'DOD': ['D.O.D.', 'Dept. of Defense'],
    # Other acronym format variants
    'NPRM': ['N.P.R.M.'],
    'TSO': ['T.S.O.'],
    'AD': ['A.D.'],
    'TC': ['T.C.'],
    'STC': ['S.T.C.']
}
