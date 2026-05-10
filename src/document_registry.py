"""
Maps relative PDF paths (from docs/) to document-level metadata.
Used to populate source_doc, authority, and category fields on every chunk.
"""

from pathlib import Path

# Keys are Path objects (OS-independent) relative to docs/
DOCUMENT_REGISTRY: dict[Path, dict] = {
    # BCA — Building & Construction Authority
    Path("BCA/approved_documents/Volume-1-Introduction.pdf"): {
        "source_doc": "BCA Approved Documents — Volume 1 Introduction",
        "authority": "BCA",
        "category": "approved_documents",
    },
    Path("BCA/approved_documents/Vol 2_FINAL.pdf"): {
        "source_doc": "BCA Approved Documents — Volume 2",
        "authority": "BCA",
        "category": "approved_documents",
    },
    Path("BCA/approved_documents/Vol 3_FINAL.pdf"): {
        "source_doc": "BCA Approved Documents — Volume 3",
        "authority": "BCA",
        "category": "approved_documents",
    },
    Path("BCA/approved_documents/Approveddocument.pdf"): {
        "source_doc": "BCA Approved Document",
        "authority": "BCA",
        "category": "approved_documents",
    },
    Path("BCA/accessibility/bca-coa2025.pdf"): {
        "source_doc": "BCA Code on Accessibility 2025",
        "authority": "BCA",
        "category": "accessibility",
    },
    Path("BCA/accessibility/bca-coaguide2025.pdf"): {
        "source_doc": "BCA Guide to the Code on Accessibility 2025",
        "authority": "BCA",
        "category": "accessibility",
    },
    Path("BCA/buildability/cop2017.pdf"): {
        "source_doc": "BCA Code of Practice on Buildability 2017",
        "authority": "BCA",
        "category": "buildability",
    },
    Path("BCA/buildable_design/codeofpractice.pdf"): {
        "source_doc": "BCA Code of Practice on Buildable Design",
        "authority": "BCA",
        "category": "buildable_design",
    },
    # LTA — Land Transport Authority
    Path("LTA/railway/Code_of_Practice_for_Railway_Protection.pdf"): {
        "source_doc": "LTA Code of Practice for Railway Protection",
        "authority": "LTA",
        "category": "railway",
    },
    # NEA — National Environment Agency
    Path("NEA/environmental_health/copeh-2025.pdf"): {
        "source_doc": "NEA Code of Practice for Environmental Health 2025",
        "authority": "NEA",
        "category": "environmental_health",
    },
    # PUB — Public Utilities Board
    Path("PUB/drainage/Code-of-Practice-on-Surface-Water-Drainage.pdf"): {
        "source_doc": "PUB Code of Practice on Surface Water Drainage",
        "authority": "PUB",
        "category": "drainage",
    },
    Path("PUB/drainage/COP_Surface Water Drainage 2011.pdf"): {
        "source_doc": "PUB Code of Practice on Surface Water Drainage — 2011 Edition",
        "authority": "PUB",
        "category": "drainage",
    },
    Path("PUB/drainage/COP_Surface Water Drainage_7th Ed Add. 1 (1).pdf"): {
        "source_doc": "PUB Code of Practice on Surface Water Drainage — 7th Edition Addendum 1",
        "authority": "PUB",
        "category": "drainage",
    },
    # SCDF — Singapore Civil Defence Force
    Path("SCDF/fire_code/firecode-2023-111220241013.pdf"): {
        "source_doc": "SCDF Fire Code 2023",
        "authority": "SCDF",
        "category": "fire_code",
    },
    Path("SCDF/singapore_standards/SS_332/SS 332-2018 Spec for Fire Doors.pdf"): {
        "source_doc": "SS 332:2018 — Specification for Fire Doors",
        "authority": "SCDF",
        "category": "singapore_standards",
    },
    Path("SCDF/singapore_standards/SS_508/SS 508-2-2008_Graphical Symbols_Part2-Safety colours and safety signs.pdf"): {
        "source_doc": "SS 508-2:2008 — Safety Colours and Safety Signs",
        "authority": "SCDF",
        "category": "singapore_standards",
    },
    Path("SCDF/singapore_standards/SS_575/SS 575 2012_Fire Hydrant_ Rising Main and hosereel system.pdf"): {
        "source_doc": "SS 575:2012 — Fire Hydrant, Rising Mains and Hose Reels",
        "authority": "SCDF",
        "category": "singapore_standards",
    },
    Path("SCDF/singapore_standards/SS_578/SS 578_2012 COP for Use & maintenance of Portable Fire Extinguishers_able to search.pdf"): {
        "source_doc": "SS 578:2012 — Code of Practice for Portable Fire Extinguishers",
        "authority": "SCDF",
        "category": "singapore_standards",
    },
    Path("SCDF/singapore_standards/SS_578/SS 578-2019 - CP for Fire Extinguishers.pdf"): {
        "source_doc": "SS 578:2019 — Code of Practice for Portable Fire Extinguishers",
        "authority": "SCDF",
        "category": "singapore_standards",
    },
    # URA — Urban Redevelopment Authority
    Path("URA/conservation_guidelines.pdf"): {
        "source_doc": "URA Conservation Guidelines",
        "authority": "URA",
        "category": "planning",
    },
    Path("URA/guidelines-greenery-provision-tree-conservation-developments-version-5.pdf"): {
        "source_doc": "NParks/URA Greenery Provision and Tree Conservation Guidelines v5",
        "authority": "URA",
        "category": "planning",
    },
    Path("URA/handbooks/non-resi-handbook.pdf"): {
        "source_doc": "URA Non-Residential Development Handbook",
        "authority": "URA",
        "category": "handbooks",
    },
    Path("URA/handbooks/resi-handbook.pdf"): {
        "source_doc": "URA Residential Development Handbook",
        "authority": "URA",
        "category": "handbooks",
    },
    # Legal & Regulatory
    Path("legal_regulatory/Architects Act 1991.pdf"): {
        "source_doc": "Singapore Architects Act 1991",
        "authority": "Government of Singapore",
        "category": "legal_regulatory",
    },
    Path("legal_regulatory/Workplace Safety and Health (Construction) Regulat.pdf"): {
        "source_doc": "Workplace Safety and Health (Construction) Regulations",
        "authority": "MOM",
        "category": "legal_regulatory",
    },
    # Contracts
    Path("contracts/SIA_Lump Sum Contract_9th Edition.pdf"): {
        "source_doc": "SIA Lump Sum Contract — 9th Edition",
        "authority": "SIA",
        "category": "contracts",
    },
    # Miscellaneous
    Path("miscellaneous/General Guidelines on Letterboxes (Revised & Approved by IDA on 2 Oct 20...-1.pdf"): {
        "source_doc": "IMDA General Guidelines on Letterboxes",
        "authority": "IMDA",
        "category": "miscellaneous",
    },
    Path("miscellaneous/Potential Hazards of Solar Photovoltaic Feb 2020.pdf"): {
        "source_doc": "SCDF Guidance on Solar PV Fire Hazards",
        "authority": "SCDF",
        "category": "miscellaneous",
    },
}


def lookup(pdf_path_relative: Path) -> dict:
    """Return metadata for a given relative path, with a fallback."""
    meta = DOCUMENT_REGISTRY.get(pdf_path_relative)
    if meta:
        return meta
    # Fallback: infer from folder name
    parts = pdf_path_relative.parts
    authority = parts[0].upper() if parts else "UNKNOWN"
    return {
        "source_doc": pdf_path_relative.stem,
        "authority": authority,
        "category": parts[1] if len(parts) > 2 else "unknown",
    }
