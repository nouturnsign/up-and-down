#!/usr/bin/env python3

import os
import re
import argparse

# The exact sequence of the 44 works as they appear in the PG100 Table of Contents.
# By forcing the script to expect these in strict chronological order, we completely 
# eliminate false positives. 
# Format: (Normalized Title, Is Play (Boolean), Output Filename)
EXPECTED_WORKS_SEQUENCE = [
    ("THESONNETS", False, "the_sonnets"),
    ("ALLSWELLTHATENDSWELL", True, "alls_well_that_ends_well"),
    ("THETRAGEDYOFANTONYANDCLEOPATRA", True, "antony_and_cleopatra"),
    ("ASYOULIKEIT", True, "as_you_like_it"),
    ("THECOMEDYOFERRORS", True, "the_comedy_of_errors"),
    ("THETRAGEDYOFCORIOLANUS", True, "coriolanus"),
    ("CYMBELINE", True, "cymbeline"),
    ("THETRAGEDYOFHAMLETPRINCEOFDENMARK", True, "hamlet"),
    ("THEFIRSTPARTOFKINGHENRYTHEFOURTH", True, "king_henry_iv_part_1"),
    ("THESECONDPARTOFKINGHENRYTHEFOURTH", True, "king_henry_iv_part_2"),
    ("THELIFEOFKINGHENRYTHEFIFTH", True, "king_henry_v"),
    ("THEFIRSTPARTOFHENRYTHESIXTH", True, "king_henry_vi_part_1"),
    ("THESECONDPARTOFKINGHENRYTHESIXTH", True, "king_henry_vi_part_2"),
    ("THETHIRDPARTOFKINGHENRYTHESIXTH", True, "king_henry_vi_part_3"),
    ("KINGHENRYTHEEIGHTH", True, "king_henry_viii"),
    ("THELIFEANDDEATHOFKINGJOHN", True, "king_john"),
    ("THETRAGEDYOFJULIUSCAESAR", True, "julius_caesar"),
    ("THETRAGEDYOFKINGLEAR", True, "king_lear"),
    ("LOVESLABOURSLOST", True, "loves_labours_lost"),
    ("THETRAGEDYOFMACBETH", True, "macbeth"),
    ("MEASUREFORMEASURE", True, "measure_for_measure"),
    ("THEMERCHANTOFVENICE", True, "the_merchant_of_venice"),
    ("THEMERRYWIVESOFWINDSOR", True, "the_merry_wives_of_windsor"),
    ("AMIDSUMMERNIGHTSDREAM", True, "a_midsummer_nights_dream"),
    ("MUCHADOABOUTNOTHING", True, "much_ado_about_nothing"),
    ("THETRAGEDYOFOTHELLOTHEMOOROFVENICE", True, "othello"),
    ("PERICLESPRINCEOFTYRE", True, "pericles"),
    ("KINGRICHARDTHESECOND", True, "king_richard_ii"),
    ("KINGRICHARDTHETHIRD", True, "king_richard_iii"),
    ("THETRAGEDYOFROMEOANDJULIET", True, "romeo_and_juliet"),
    ("THETAMINGOFTHESHREW", True, "the_taming_of_the_shrew"),
    ("THETEMPEST", True, "the_tempest"),
    ("THELIFEOFTIMONOFATHENS", True, "timon_of_athens"),
    ("THETRAGEDYOFTITUSANDRONICUS", True, "titus_andronicus"),
    ("TROILUSANDCRESSIDA", True, "troilus_and_cressida"),
    ("TWELFTHNIGHTORWHATYOUWILL", True, "twelfth_night"),
    ("THETWOGENTLEMENOFVERONA", True, "the_two_gentlemen_of_verona"),
    ("THETWONOBLEKINSMEN", True, "the_two_noble_kinsmen"),
    ("THEWINTERSTALE", True, "the_winters_tale"),
    ("ALOVERSCOMPLAINT", False, "a_lovers_complaint"),
    ("THEPASSIONATEPILGRIM", False, "the_passionate_pilgrim"),
    ("THEPHOENIXANDTHETURTLE", False, "the_phoenix_and_the_turtle"),
    ("THERAPEOFLUCRECE", False, "the_rape_of_lucrece"),
    ("VENUSANDADONIS", False, "venus_and_adonis"),
]

def flush_preamble(buffer, preamble_buffer):
    """
    Searches backwards through the buffered start of a play to find the true first act.
    Everything before it (Dramatis Personae, Table of Contents) is permanently discarded.
    """
    start_pattern = re.compile(r"^(ACT\s+I|PROLOGUE|SCENE\s+I|INDUCTION)[\.\s]*$", re.IGNORECASE)
    start_idx = 0
    for i in range(len(preamble_buffer) - 1, -1, -1):
        if start_pattern.match(preamble_buffer[i].strip()):
            start_idx = i
            break
            
    # Append only the lines from the true start of the play onwards
    buffer.extend(preamble_buffer[start_idx:])
    preamble_buffer.clear()

def split_complete_works(filepath, output_dir="shakespeare_plays"):
    if not os.path.exists(filepath):
        print(f"ERROR: Cannot find '{filepath}'.")
        return

    os.makedirs(output_dir, exist_ok=True)

    state = "WAIT_FOR_TOC"
    current_work_idx = 0
    
    current_file = None
    current_filename = None
    saved_count = 0

    buffer = []
    BUFFER_LIMIT = 1000
    
    in_preamble = False
    preamble_buffer = []

    print(f"Streaming and splitting '{filepath}' by strict sequence...")

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            clean_line = line.strip()

            # State 1: Wait for the top-level PG100 Contents header
            if state == "WAIT_FOR_TOC":
                if "Contents" in clean_line:
                    state = "SKIP_TOC"
                continue

            # State 2: Stream past the TOC so we don't accidentally split using it
            if state == "SKIP_TOC":
                # Wait until we see the final item in the TOC
                if re.sub(r"[^A-Z]", "", clean_line.upper()) == "VENUSANDADONIS":
                    state = "EXTRACT_WORKS"
                continue

            # State 3: Extract the 44 works sequentially
            if state == "EXTRACT_WORKS":
                
                # Check if we hit the boundary for the NEXT expected work
                if current_work_idx < len(EXPECTED_WORKS_SEQUENCE) and clean_line.isupper():
                    expected_normalized, is_play, safe_title = EXPECTED_WORKS_SEQUENCE[current_work_idx]
                    line_normalized = re.sub(r"[^A-Z]", "", clean_line.upper())
                    
                    if line_normalized == expected_normalized:
                        # 1. Close the previous file gracefully
                        if current_file:
                            if in_preamble:
                                flush_preamble(buffer, preamble_buffer)
                                in_preamble = False
                                
                            if buffer:
                                current_file.writelines(buffer)
                                buffer.clear()
                                
                            current_file.close()
                            print(f"  -> Saved: {current_filename}")
                            saved_count += 1

                        # 2. Advance to the next sequence item
                        current_work_idx += 1

                        # 3. Setup for the new work
                        if is_play:
                            current_filename = f"{safe_title}.txt"
                            current_filepath = os.path.join(output_dir, current_filename)
                            current_file = open(current_filepath, "w", encoding="utf-8")
                            
                            # Write the clean title to the top of the file
                            current_file.write(line)
                            
                            in_preamble = True
                            preamble_buffer.clear()
                        else:
                            # If it's a poem/sonnet, keep current_file as None so it is discarded
                            current_file = None
                            in_preamble = False
                            
                        continue # Move to the next line

                # General Line Writing
                if current_file:
                    if in_preamble:
                        preamble_buffer.append(line)
                        # 1000 lines safely encompasses any Cast List or Preamble length
                        if len(preamble_buffer) >= 1000:
                            flush_preamble(buffer, preamble_buffer)
                            in_preamble = False
                    else:
                        buffer.append(line)
                        if len(buffer) >= BUFFER_LIMIT:
                            current_file.writelines(buffer)
                            buffer.clear()

    # Final cleanup (Handles closing "The Winter's Tale" or any final buffer writes)
    if current_file:
        if in_preamble:
            flush_preamble(buffer, preamble_buffer)
        if buffer:
            current_file.writelines(buffer)
        current_file.close()
        print(f"  -> Saved: {current_filename}")
        saved_count += 1

    print(f"\nSuccess! Separated {saved_count} plays into the '{output_dir}/' directory.")
    print("Sonnets, poems, and cast lists were automatically discarded.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split Project Gutenberg's Complete Works of Shakespeare into individual files."
    )
    parser.add_argument(
        "--input",
        default="pg100.txt",
        help="Path to the Complete Works text file (e.g., pg100.txt)",
    )
    parser.add_argument(
        "--output", default="shakespeare_plays", help="Output directory folder name"
    )

    args = parser.parse_args()
    split_complete_works(args.input, args.output)
