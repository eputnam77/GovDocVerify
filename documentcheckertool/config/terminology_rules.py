"""Configuration file for terminology rules and mappings."""


# Message templates for terminology checks
class TerminologyMessages:
    """Message templates for terminology checks."""

    # Consistency messages
    INCONSISTENT_TERMINOLOGY = "Found terminology issue. Use '{standard}' instead of '{variant}'."

    # Split infinitive messages
    SPLIT_INFINITIVE_INFO = (
        "Found split infinitive. Although the rule against splitting infinitives is widely "
        "considered obsolete, DOT OGC might flag it."
    )

    # Special case messages
    ADDITIONALLY_REPLACEMENT = "Found 'Additionally'. Replace with 'In addition' (per DOT OGC)."

    # Proposed wording messages
    PROPOSED_WORDING_INFO = "Found 'proposed' wording—remove draft phrasing for final documents."

    # USC/CFR formatting messages
    USC_FORMAT_WARNING = "USC should be U.S.C."
    USC_PERIOD_WARNING = "U.S.C should have a final period"
    CFR_FORMAT_WARNING = "C.F.R. should be CFR"
    CFR_PART_WARNING = (
        "CFR Part should be CFR part (if your document must be reviewed by DOT OGC, "
        "they might request CFR Part)."
    )

    # Gendered terms messages
    GENDERED_TERM_WARNING = "Found gendered term. Use {replacement} instead of {term}."

    # Plain language messages
    LEGALESE_SIMPLE_WARNING = "Use simpler alternatives like 'under' or 'following'."
    LEGALESE_AVOID_WARNING = "Avoid archaic or legalese terms"

    # Aviation terminology messages
    AVIATION_TERM_WARNING = "Found incorrect term. Use {replacement} instead of {term}."

    # Qualifier messages
    QUALIFIER_WARNING = "Avoid unnecessary qualifiers."

    # Plural usage messages
    PLURAL_USAGE_WARNING = "Ensure consistent singular/plural usage."

    # Authority citation messages
    OBSOLETE_CITATION_WARNING = "Found invalid citation. Confirm or remove {citation}."


# Common replacements (specific word/phrase replacements only)
TERM_REPLACEMENTS = {
    "and/or": "written sentence breaking up and/or (per AGC)",
    "although": "though (per DOT OGC Style Guide)",
    "additionally": "in addition (per DOT OGC Style Guide)",
    "cockpit": "flight deck (per AIR-600 Quick Reference Guide)",
    "flight crew": "flightcrew (per 14 CFR part 1)",
    "shall": "must (per FAA Order 1320.46)",
    "cancelled": "canceled (per the GPO Style Manual)",
    "RGL": "DRS",
    "Regulatory and Guidance Library": "Dynamic Regulatory System",
    "chairman": "chair (per AIR-600 Quick Reference Guide)",
    "flagman": "flagperson (per AIR-600 Quick Reference Guide)",
    "manmade": "personmade (per AIR-600 Quick Reference Guide)",
    "manpower": "labor force (per AIR-600 Quick Reference Guide)",
    "European Aviation Safety Agency": "European Union Aviation Safety Agency (EASA)",
    "commence": "begin or start (per Plain Language Guidelines)",
    "terminate": "end or stop (per Plain Language Guidelines)",
    "transmit": "send (per Plain Language Guidelines)",
    "demonstrate": "show or prove (per Plain Language Guidelines)",
    "facilitate": "help or assist (per Plain Language Guidelines)",
    "utilize": "use (per Plain Language Guidelines)",
    "ACO": "Certification Branch (as of 2023 AIR Reorganization)",
    "CFR Part": (
        "CFR part (per Document Drafting Handbook & FAA Order 1320.46). However, "
        "if your document is being reviewed by DOT OGC, use CFR Part"
    ),
    "U.S.C": "U.S.C. (per the GPO Style Manual)",
    "USC": "U.S.C. (per the GPO Style Manual)",
    "in accordance with": "under (per FAA Order 1320.46)",
    "in compliance with": "under (per FAA Order 1320.46)",
}

# Terms to avoid (only subjective/style terms, not formatting issues)
FORBIDDEN_TERMS = {
    "clearly": "Avoid using 'clearly' as it's subjective",
    "obviously": "Avoid using 'obviously' as it's subjective",
    "aforementioned": "Avoid using 'aforementioned' as it can be unclear",
    "latter": "Avoid using 'latter'; specify the item explicitly",
    "former": "Avoid using 'former'; specify the item explicitly",
    "respectively": "Avoid using 'respectively' as it can be confusing",
    "above": "Avoid using 'above'",
    "below": "Avoid using 'below'",
}

# Multiple accepted forms - only for terms where either form is acceptable at any point
MULTIPLE_ACCEPTED_FORMS = {
    "Federal Register": ["Fed. Reg."],  # Both forms equally acceptable
    "Administrator": ["Admin."],  # Both forms acceptable in headings/text
    "Section": ["§"],  # Both forms acceptable except at start of sentence
    "percent": ["%"],  # Both forms acceptable except at start of sentence
}

# Terminology variants to check for consistency (only abbreviation/spelling variants)
TERMINOLOGY_VARIANTS = {
    "website": ["web site", "web-site"],
    "online": ["on-line", "on line"],
    "email": ["e-mail", "Email"],
    # Federal agencies - only checking format variants, not first use
    "FAA": ["F.A.A.", "Federal Aviation Admin"],  # Not checking first use
    "NASA": ["N.A.S.A."],
    "DOT": ["D.O.T.", "Dept. of Transportation"],
    "EPA": ["E.P.A."],
    "DOD": ["D.O.D.", "Dept. of Defense"],
    # Other acronym format variants
    "NPRM": ["N.P.R.M."],
    "TSO": ["T.S.O."],
    "AD": ["A.D."],
    "TC": ["T.C."],
    "STC": ["S.T.C."],
}
