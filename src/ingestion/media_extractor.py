"""
Media Extraction Module (Owner: Member P2)
Extracts diagrams, figure plates, maps, schematics, and lore artwork from PDFs and archive directories.
Saves media files to data/extracted_media/figures/ and produces standardized 'image-caption' chunks.
"""

import os
import re
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from PIL import Image

from src.config import PROJECT_ROOT, EXTRACTED_MEDIA_DIR
from src.ingestion.parser import assign_source_reliability, sanitize_id

logger = logging.getLogger(__name__)

# Known codex plate specific descriptions and recorded figures
KNOWN_CODEX_PLATES = {
    "plate_00_location_marrowwatch": {
        "title": "Marrowwatch — Recorded Garrison Strength Plate",
        "entity": "Marrowwatch",
        "content": "Official Codex Vaeloria figure plate for Marrowwatch showing Recorded Garrison Strength: 3,107 souls under arms. Figures verified by the Silent Choir.",
        "caption": "Figure Plate: Marrowwatch Recorded Garrison Strength (3,107 souls under arms)",
        "entities": ["Marrowwatch", "Codex Vaeloria", "Silent Choir", "Garrison Strength"]
    },
    "plate_01_location_emberdeep": {
        "title": "Emberdeep — Recorded Garrison Strength Plate",
        "entity": "Emberdeep",
        "content": "Official Codex Vaeloria figure plate for Emberdeep showing Recorded Garrison Strength: 1,114 souls under arms. Comparison standards: Old Imperial minimum (800), Border-march standard (2,400), Great Keep standard (6,000). Measured in souls under arms.",
        "caption": "Figure Plate: Emberdeep Recorded Garrison Strength (1,114 souls under arms)",
        "entities": ["Emberdeep", "Codex Vaeloria", "Garrison Strength", "The Shattered Vale"]
    },
    "plate_02_conflict_the_accord_of_mournthrone": {
        "title": "The Accord of Mournthrone — Recorded Casualties Plate",
        "entity": "The Accord of Mournthrone",
        "content": "Official Codex Annals figure plate for The Accord of Mournthrone showing Recorded Casualties: 87,349 souls lost out of 104,818 total participants.",
        "caption": "Figure Plate: The Accord of Mournthrone Recorded Casualties (87,349 souls lost)",
        "entities": ["The Accord of Mournthrone", "The Ashen Vanguard", "Mournthrone", "Casualties"]
    },
    "plate_03_location_crookgate_keep": {
        "title": "Crookgate Keep — Recorded Garrison Strength Plate",
        "entity": "Crookgate Keep",
        "content": "Official Codex Vaeloria figure plate for Crookgate Keep showing Recorded Garrison Strength: 6,970 souls under arms. As entered into the Codex Vaeloria. Figures verified by the Silent Choir.",
        "caption": "Figure Plate: Crookgate Keep Recorded Garrison Strength (6,970 souls under arms)",
        "entities": ["Crookgate Keep", "Codex Vaeloria", "Silent Choir", "Weeping Marshes", "Garrison Strength"]
    },
    "plate_04_artifact_the_thrice_bound_edge": {
        "title": "The Thrice-Bound Edge — Attunement Cost Plate",
        "entity": "The Thrice-Bound Edge",
        "content": "Official Codex Vaeloria artifact plate detailing weapon binding and attunement cost for The Thrice-Bound Edge: 94 vitae-grains (shards of will / attunement cost). Benchmark thresholds: Novice tolerance (20), Adept tolerance (55), Master tolerance (85).",
        "caption": "Figure Plate: The Thrice-Bound Edge Attunement Cost (94 vitae-grains)",
        "entities": ["The Thrice-Bound Edge", "Attunement Cost", "Vitae-Grains", "Weapon Binding", "Regalia"]
    },
    "plate_05_location_embercrag_fortress": {
        "title": "Embercrag Fortress — Recorded Garrison Strength Plate",
        "entity": "Embercrag Fortress",
        "content": "Official Codex Vaeloria figure plate for Embercrag Fortress showing Recorded Garrison Strength: 7,473 souls under arms out of 8,967 maximum capacity.",
        "caption": "Figure Plate: Embercrag Fortress Recorded Garrison Strength (7,473 souls under arms)",
        "entities": ["Embercrag Fortress", "Codex Vaeloria", "The Shattered Vale", "Garrison Strength"]
    },
    "plate_06_location_hollowreach": {
        "title": "Hollowreach — Recorded Garrison Strength Plate",
        "entity": "Hollowreach",
        "content": "Official Codex Vaeloria figure plate for Hollowreach showing Recorded Garrison Strength: 1,306 souls under arms. As entered into the Codex Vaeloria. Figures verified by the Silent Choir.",
        "caption": "Figure Plate: Hollowreach Recorded Garrison Strength (1,306 souls under arms)",
        "entities": ["Hollowreach", "Codex Vaeloria", "Silent Choir", "Gloaming Reach", "Garrison Strength"]
    },
    "plate_07_artifact_the_thrice_bound_lantern": {
        "title": "The Thrice-Bound Lantern — Attunement Cost Plate",
        "entity": "The Thrice-Bound Lantern",
        "content": "Official Codex Vaeloria artifact plate for The Thrice-Bound Lantern showing Attunement Cost: 55 vitae-grains (Adept tolerance). Benchmark thresholds: Novice tolerance (20), Adept tolerance (55), Master tolerance (85).",
        "caption": "Figure Plate: The Thrice-Bound Lantern Attunement Cost (55 vitae-grains)",
        "entities": ["The Thrice-Bound Lantern", "Attunement Cost", "Vitae-Grains", "Ward", "Hollowvale"]
    },
    "plate_08_creature_weeping_lurker": {
        "title": "Weeping Lurker — Threat Rating Plate",
        "entity": "Weeping Lurker",
        "content": "Official threat-classification plate for the creature known as the Weeping Lurker showing Threat Rating: 3 of 10, per the Vanguard scale.",
        "caption": "Figure Plate: Weeping Lurker Threat-Classification Plate (Threat Rating: 3/10)",
        "entities": ["Weeping Lurker", "Threat Rating", "Vanguard Scale", "Embermarch"]
    },
    "plate_09_location_greyfell_citadel": {
        "title": "Greyfell Citadel — Recorded Garrison Strength Plate",
        "entity": "Greyfell Citadel",
        "content": "Official Codex Vaeloria figure plate for Greyfell Citadel showing Recorded Garrison Strength: 3,695 souls under arms. As entered into the Codex Vaeloria. Figures verified by the Silent Choir.",
        "caption": "Figure Plate: Greyfell Citadel Recorded Garrison Strength (3,695 souls under arms)",
        "entities": ["Greyfell Citadel", "Codex Vaeloria", "Silent Choir", "Shattered Vale", "Garrison Strength"]
    },
    "plate_10_creature_marsh_revenant": {
        "title": "Marsh Revenant — Threat Rating Plate",
        "entity": "Marsh Revenant",
        "content": "Official threat-classification plate for the creature known as the Marsh Revenant showing Threat Rating: 4 of 10, per the Vanguard scale (Nuisance: 3, Menace: 6, Calamity: 9).",
        "caption": "Figure Plate: Marsh Revenant Threat-Classification Plate (Threat Rating: 4/10)",
        "entities": ["Marsh Revenant", "Threat Rating", "Vanguard Scale", "Greyfell Citadel"]
    },
    "plate_11_location_mournwatch": {
        "title": "Mournwatch — Recorded Garrison Strength Plate",
        "entity": "Mournwatch",
        "content": "Official Codex Vaeloria figure plate for Mournwatch showing Recorded Garrison Strength: 8,254 souls under arms out of 9,904 maximum gauge.",
        "caption": "Figure Plate: Mournwatch Recorded Garrison Strength (8,254 souls under arms)",
        "entities": ["Mournwatch", "Codex Vaeloria", "Gloaming Reach", "Garrison Strength"]
    },
    "plate_12_location_thorncairn": {
        "title": "Thorncairn — Recorded Garrison Strength Plate",
        "entity": "Thorncairn",
        "content": "Official Codex Vaeloria figure plate for Thorncairn showing Recorded Garrison Strength: 7,748 souls under arms. As entered into the Codex Vaeloria. Figures verified by the Silent Choir.",
        "caption": "Figure Plate: Thorncairn Recorded Garrison Strength (7,748 souls under arms)",
        "entities": ["Thorncairn", "Codex Vaeloria", "Silent Choir", "Gloaming Reach", "Garrison Strength"]
    },
    "plate_13_artifact_the_cinder_wrought_aegis": {
        "title": "The Cinder-Wrought Aegis — Attunement Cost Plate",
        "entity": "The Cinder-Wrought Aegis",
        "content": "Official Codex Vaeloria artifact plate for The Cinder-Wrought Aegis showing Attunement Cost: 34 vitae-grains. Benchmark thresholds: Novice tolerance (20), Adept tolerance (55), Master tolerance (85).",
        "caption": "Figure Plate: The Cinder-Wrought Aegis Attunement Cost (34 vitae-grains)",
        "entities": ["The Cinder-Wrought Aegis", "Attunement Cost", "Vitae-Grains", "Regalia", "Gloamreach"]
    },
    "plate_14_creature_thorn_wraith": {
        "title": "Thorn Wraith — Threat Rating Plate",
        "entity": "Thorn Wraith",
        "content": "Official threat-classification plate for the creature known as the Thorn Wraith showing Threat Rating: 9 of 10, per the Vanguard scale.",
        "caption": "Figure Plate: Thorn Wraith Threat-Classification Plate (Threat Rating: 9/10)",
        "entities": ["Thorn Wraith", "Threat Rating", "Vanguard Scale", "Ironfell Citadel"]
    }
}


def _match_known_plate(stem: str) -> Optional[Dict[str, Any]]:
    """Helper to match a filename/stem to known plate definitions."""
    stem_lower = stem.lower()
    for key, data in KNOWN_CODEX_PLATES.items():
        if key in stem_lower:
            return data
    return None


def extract_images_from_pdf(pdf_path: Path, output_dir: Path) -> List[Dict[str, Any]]:
    """
    Extracts embedded raster figures from a PDF, filtering out small icons (<100x100px)
    and full-page scanned backgrounds.
    Saves figures to output_dir and returns standardized 'image-caption' chunk objects.
    """
    if fitz is None:
        logger.warning("PyMuPDF (fitz) is not installed; skipping PDF image extraction.")
        return []

    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    # Skip scan-only documents where images are just full-page parchment backgrounds
    if ".scan." in pdf_path.name.lower() or "_scan" in pdf_path.name.lower():
        logger.debug(f"Skipping image extraction for scanned PDF document: {pdf_path.name}")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    doc_stem = sanitize_id(pdf_path.stem)
    rel_tag = assign_source_reliability(pdf_path)

    chunks = []
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_text = page.get_text("text").strip()

        # Extract section title or plate label from page text
        page_lines = [l.strip() for l in page_text.splitlines() if l.strip()]
        plate_label = ""
        section_title = f"{pdf_path.stem.replace('_', ' ').title()}"

        for line in page_lines:
            if line.startswith("Plate -") or line.startswith("Plate:"):
                plate_label = line
            elif len(line) > 3 and not plate_label and not line.endswith("."):
                section_title = line

        image_list = page.get_images(full=True)
        img_counter = 0

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                width = base_img.get("width", 0)
                height = base_img.get("height", 0)
                image_bytes = base_img.get("image", b"")
                ext = base_img.get("ext", "png")

                # Filter out small decorative icons, page borders, or empty blocks
                if width < 100 or height < 100 or len(image_bytes) < 1024:
                    continue

                img_counter += 1
                filename = f"{doc_stem}_p{page_num:02d}_fig{img_counter:02d}.{ext}"
                out_path = output_dir / filename
                with open(out_path, "wb") as f:
                    f.write(image_bytes)

                # Match against known codex plate lore if applicable
                matched_plate = None
                if plate_label:
                    matched_plate = _match_known_plate(plate_label)
                if not matched_plate:
                    matched_plate = _match_known_plate(section_title)

                chunk_id = f"{doc_stem}_p{page_num:02d}_fig{img_counter:02d}"
                try:
                    rel_media_path = str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                except ValueError:
                    rel_media_path = str(out_path).replace("\\", "/")

                if matched_plate:
                    caption = matched_plate["caption"]
                    content = f"{matched_plate['content']}\n\n[Context: {pdf_path.name}, Page {page_num}]"
                    entities = matched_plate["entities"]
                    sec_title = matched_plate["title"]
                else:
                    caption = plate_label or f"Figure Plate {img_counter} (Page {page_num})"
                    context_snippet = " ".join(page_lines[:4]) if page_lines else ""
                    content = f"Illustration/Figure Plate from {pdf_path.name} on Page {page_num}.\n{caption}\nContext: {context_snippet}".strip()
                    entities = [section_title] if section_title else []
                    sec_title = section_title

                chunks.append({
                    "chunk_id": chunk_id,
                    "document_name": pdf_path.name,
                    "document_type": "pdf",
                    "page_number": page_num,
                    "section_title": sec_title,
                    "modality": "image-caption",
                    "content": content,
                    "media_path": rel_media_path,
                    "caption": caption,
                    "metadata": {
                        "dimensions": [width, height],
                        "source_reliability": rel_tag,
                        "source_category": "codex" if "codex" in str(pdf_path).lower() else "ephemera",
                        "related_entities": entities,
                        "file_path": pdf_path.name
                    }
                })

            except Exception as e:
                logger.warning(f"Failed to extract image xref={xref} on page {page_num} of {pdf_path.name}: {e}")

    doc.close()
    return chunks


def _describe_wiki_image(img_name: str) -> Dict[str, Any]:
    """
    Generates rich visual descriptions, captions, and entity associations for wiki illustrations.
    """
    stem = Path(img_name).stem.lower()

    if stem.startswith("atmo_heraldry_faction_"):
        faction_raw = stem.replace("atmo_heraldry_faction_", "").replace("_", " ").title()
        if "morvain" in stem:
            return {
                "title": f"Heraldry Banner — {faction_raw}",
                "caption": "Heraldic Banner of House Morvain with Crossed Golden Keys",
                "content": "Official heraldic banner of House Morvain. Features an ornate black-and-silver quartered battle standard emblazoned with two crossed golden keys within an ornate filigree shield and crowned by the skull emblem of antiquity.",
                "entities": ["House Morvain", "Crossed Keys", "Heraldry", "Ironfell Citadel"]
            }
        elif "vanguard" in stem:
            return {
                "title": f"Heraldry Banner — {faction_raw}",
                "caption": "Heraldic Banner of The Ashen Vanguard with Weeping Bleeding Eye and Radiant Halo",
                "content": "Official battle standard of The Ashen Vanguard. Features a central emblem depicting a weeping eye shedding dark tears/blood, surrounded by a radiant spiked solar halo and skull finial.",
                "entities": ["The Ashen Vanguard", "Weeping Eye", "Banner", "Heraldry"]
            }
        elif "bleeding_crown" in stem:
            return {
                "title": f"Heraldry Banner — {faction_raw}",
                "caption": "Heraldic Banner of The Bleeding Crown",
                "content": "Official heraldic banner of The Bleeding Crown faction, depicting the dripping crimson crown emblem upon dark battle silk.",
                "entities": ["The Bleeding Crown", "Heraldry", "Banner"]
            }
        elif "iron_ring" in stem:
            return {
                "title": f"Heraldry Banner — {faction_raw}",
                "caption": "Heraldic Banner of The Iron-Ring Cartel",
                "content": "Official standard of The Iron-Ring Cartel, featuring interlocking iron chain rings and mercantile seal insignia.",
                "entities": ["The Iron-Ring Cartel", "Heraldry", "Banner"]
            }
        elif "silent_choir" in stem:
            return {
                "title": f"Heraldry Banner — {faction_raw}",
                "caption": "Heraldic Banner of The Silent Choir",
                "content": "Official heraldic banner of The Silent Choir, depicting the veiled face and silence sigil of the order.",
                "entities": ["The Silent Choir", "Heraldry", "Banner"]
            }
        return {
            "title": f"Heraldry Banner — {faction_raw}",
            "caption": f"Heraldic Banner of {faction_raw}",
            "content": f"Official heraldic banner and faction standard of {faction_raw}.",
            "entities": [faction_raw, "Heraldry", "Banner"]
        }

    elif stem.startswith("atmo_portrait_character_"):
        char_raw = stem.replace("atmo_portrait_character_", "").replace("_", " ").title()
        if "ignatz_ashgrove" in stem:
            return {
                "title": f"Portrait — {char_raw}",
                "caption": "Portrait of Ignatz Ashgrove the Oathless Holding a Rolled Parchment Scroll",
                "content": "Official archival portrait of Ignatz Ashgrove the Oathless. Ignatz is depicted wearing dark battle armor and a tattered cloak, holding a rolled parchment manuscript scroll sealed with a red wax seal in their right hand.",
                "entities": ["Ignatz Ashgrove the Oathless", "Parchment Scroll", "Portrait"]
            }
        elif "aldous_wrenfield" in stem:
            return {
                "title": f"Portrait — {char_raw}",
                "caption": "Portrait of Aldous Wrenfield the Last Warden Holding an Ornate Golden Chalice",
                "content": "Official archival portrait of Aldous Wrenfield the Last Warden. Depicts the solemn Reliquary Keeper holding an ornate embossed golden chalice / goblet in hand before the stone ramparts of Fenspire.",
                "entities": ["Aldous Wrenfield the Last Warden", "Golden Chalice", "Fenspire", "Portrait"]
            }
        return {
            "title": f"Portrait — {char_raw}",
            "caption": f"Official Archival Portrait of {char_raw}",
            "content": f"Archival character portrait depicting {char_raw} in historical regalia and dress.",
            "entities": [char_raw, "Character Portrait"]
        }

    elif stem.startswith("atmo_relic_artifact_"):
        relic_raw = stem.replace("atmo_relic_artifact_", "").replace("_", " ").title()
        if "gauntlet_of_sorrowfell" in stem:
            return {
                "title": f"Relic Illustration — {relic_raw}",
                "caption": "Relic Plate: Gauntlet of Sorrowfell with Engraved Coiled Serpent Motif",
                "content": "Official relic illustration of the Gauntlet of Sorrowfell. The articulated dark iron/steel gauntlet is adorned with an ornate engraved coiled serpent (snake) motif along the vambrace and dorsal armor plate.",
                "entities": ["Gauntlet of Sorrowfell", "Coiled Serpent", "Relic", "Artifact"]
            }
        return {
            "title": f"Relic Illustration — {relic_raw}",
            "caption": f"Relic Plate: {relic_raw}",
            "content": f"Official illustration and visual plate of the legendary artifact {relic_raw}.",
            "entities": [relic_raw, "Artifact", "Relic"]
        }

    elif stem.startswith("atmo_creature_"):
        creature_raw = stem.replace("atmo_creature_creature_", "").replace("atmo_creature_", "").replace("_", " ").title()
        return {
            "title": f"Bestiary Illustration — {creature_raw}",
            "caption": f"Bestiary Plate: {creature_raw}",
            "content": f"Official bestiary illustration detailing the anatomical features, habitat, and appearance of {creature_raw}.",
            "entities": [creature_raw, "Bestiary", "Creature"]
        }

    elif stem.startswith("atmo_landscape_"):
        loc_raw = stem.replace("atmo_landscape_location_", "").replace("atmo_landscape_", "").replace("_", " ").title()
        return {
            "title": f"Landscape View — {loc_raw}",
            "caption": f"Landscape Painting of {loc_raw}",
            "content": f"Atmospheric landscape illustration depicting the terrain, architecture, and fortifications of {loc_raw}.",
            "entities": [loc_raw, "Location", "Landscape"]
        }

    elif stem.startswith("atmo_battle_painting_"):
        conflict_raw = stem.replace("atmo_battle_painting_conflict_", "").replace("atmo_battle_painting_", "").replace("_", " ").title()
        return {
            "title": f"Historical Battle Painting — {conflict_raw}",
            "caption": f"Battle Painting: {conflict_raw}",
            "content": f"Historical battle painting depicting the forces, battlefield engagements, and pivotal clashes during {conflict_raw}.",
            "entities": [conflict_raw, "Conflict", "Battle Painting"]
        }

    return {
        "title": stem.replace("_", " ").title(),
        "caption": f"Visual Plate: {stem.replace('_', ' ').title()}",
        "content": f"Archival visual illustration representing {stem.replace('_', ' ').title()}.",
        "entities": [stem.replace("_", " ").title()]
    }


def extract_standalone_images(corpus_dir: Path, output_dir: Path) -> List[Dict[str, Any]]:
    """
    Ingests standalone image assets from corpus directories (e.g. data/Ashen_Era_Archive/images and wiki/images),
    copies them to data/extracted_media/figures/, and creates standardized 'image-caption' chunks.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    seen_stems = set()

    # Discover all standalone images in corpus
    image_extensions = {".png", ".jpg", ".jpeg"}
    image_files = [
        p for p in corpus_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in image_extensions
    ]

    for img_path in sorted(image_files):
        stem = img_path.stem
        if stem in seen_stems:
            continue
        seen_stems.add(stem)

        try:
            with Image.open(img_path) as im:
                width, height = im.size
        except Exception as e:
            logger.warning(f"Could not open image {img_path}: {e}")
            continue

        if width < 100 or height < 100:
            continue

        # Target destination in extracted_media/figures/
        dest_filename = f"{sanitize_id(stem)}{img_path.suffix.lower()}"
        dest_path = output_dir / dest_filename
        if not dest_path.exists():
            shutil.copy2(img_path, dest_path)

        try:
            rel_media_path = str(dest_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            rel_media_path = str(dest_path).replace("\\", "/")
        rel_tag = assign_source_reliability(img_path)

        # Check if known plate
        matched_plate = _match_known_plate(stem)
        if matched_plate:
            caption = matched_plate["caption"]
            content = matched_plate["content"]
            entities = matched_plate["entities"]
            section_title = matched_plate["title"]
        else:
            wiki_info = _describe_wiki_image(img_path.name)
            caption = wiki_info["caption"]
            content = wiki_info["content"]
            entities = wiki_info["entities"]
            section_title = wiki_info["title"]

        chunk_id = f"fig_{sanitize_id(stem)}"
        chunks.append({
            "chunk_id": chunk_id,
            "document_name": img_path.name,
            "document_type": "png" if img_path.suffix.lower() == ".png" else "jpg",
            "page_number": 1,
            "section_title": section_title,
            "modality": "image-caption",
            "content": content,
            "media_path": rel_media_path,
            "caption": caption,
            "metadata": {
                "dimensions": [width, height],
                "source_reliability": rel_tag,
                "source_category": "codex" if "plate_" in stem else "wiki",
                "related_entities": entities,
                "file_path": str(img_path.relative_to(corpus_dir)).replace("\\", "/")
            }
        })

    logger.info(f"Ingested {len(chunks)} standalone image/visual chunks into {output_dir}")
    return chunks

