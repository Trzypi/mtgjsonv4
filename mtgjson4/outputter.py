"""
Functions used to generate outputs and write out
"""
import contextvars
import datetime
import json
import logging
from typing import Any, Dict, List

import mtgjson4
from mtgjson4 import util
from mtgjson4.mtgjson_card import MTGJSONCard
from mtgjson4.provider import gamepedia, magic_precons, scryfall, wizards

DECKS_URL: str = "https://raw.githubusercontent.com/taw/magic-preconstructed-decks-data/master/decks.json"
STANDARD_API_URL: str = "https://whatsinstandard.com/api/v5/sets.json"

LOGGER = logging.getLogger(__name__)
SESSION: contextvars.ContextVar = contextvars.ContextVar("SESSION")


def write_referral_url_information(data: Dict[str, str]) -> None:
    """
    Write out the URL redirection keys to file
    :param data: content
    """
    mtgjson4.COMPILED_OUTPUT_DIR.mkdir(exist_ok=True)
    with mtgjson4.COMPILED_OUTPUT_DIR.joinpath(
        mtgjson4.REFERRAL_DB_OUTPUT + ".json"
    ).open("a", encoding="utf-8") as f:
        for key, value in data.items():
            f.write(f"{key}\t{value}\n")


def write_deck_to_file(file_name: str, file_contents: Any) -> None:
    """
    Write out the precons to the file system
    :param file_name: Name to give the deck
    :param file_contents: Contents of the deck
    """
    mtgjson4.COMPILED_OUTPUT_DIR.mkdir(exist_ok=True)
    mtgjson4.COMPILED_OUTPUT_DIR.joinpath("decks").mkdir(exist_ok=True)
    with mtgjson4.COMPILED_OUTPUT_DIR.joinpath("decks", file_name + ".json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(file_contents, f, sort_keys=True, ensure_ascii=False)


def write_to_file(set_name: str, file_contents: Any, set_file: bool = False) -> None:
    """
    Write the compiled data to a file with the set's code
    Will ensure the output directory exists first
    """
    mtgjson4.COMPILED_OUTPUT_DIR.mkdir(exist_ok=True)
    with mtgjson4.COMPILED_OUTPUT_DIR.joinpath(
        util.win_os_fix(set_name) + ".json"
    ).open("w", encoding="utf-8") as f:
        # Only do this for set files, not everything
        if set_file:
            file_contents["tokens"] = mtgjson_to_dict(file_contents.get("tokens", []))
            file_contents["cards"] = mtgjson_to_dict(file_contents.get("cards", []))
        json.dump(file_contents, f, sort_keys=True, ensure_ascii=False)


def mtgjson_to_dict(cards: List[MTGJSONCard]) -> List[Dict[str, Any]]:
    """
    Convert MTGJSON cards into standard dicts
    :param cards: List of MTGJSON cards
    :return: List of MTGJSON cards as dicts
    """
    return [c.get_all() for c in cards]


def create_all_sets(files_to_ignore: List[str]) -> Dict[str, Any]:
    """
    This will create the AllSets.json file
    by pulling the compile data from the
    compiled sets and combining them into
    one conglomerate file.
    """
    all_sets_data: Dict[str, Any] = {}

    for set_file in mtgjson4.COMPILED_OUTPUT_DIR.glob("*.json"):
        if set_file.stem in files_to_ignore:
            continue

        with set_file.open(encoding="utf-8") as f:
            file_content = json.load(f)
            set_name = get_set_name_from_file_name(set_file.name.split(".")[0])
            all_sets_data[set_name] = file_content

    return all_sets_data


def create_all_cards(files_to_ignore: List[str]) -> Dict[str, Any]:
    """
    This will create the AllCards.json file
    by pulling the compile data from the
    compiled sets and combining them into
    one conglomerate file.
    """
    all_cards_data: Dict[str, Any] = {}

    for set_file in mtgjson4.COMPILED_OUTPUT_DIR.glob("*.json"):
        if set_file.stem in files_to_ignore:
            continue

        with set_file.open(encoding="utf-8") as f:
            file_content = json.load(f)

            for card in file_content["cards"]:
                # Since these can vary from printing to printing, we do not include them in the output
                card.pop("artist", None)
                card.pop("borderColor", None)
                card.pop("duelDeck", None)
                card.pop("flavorText", None)
                card.pop("frameEffect", None)
                card.pop("frameVersion", None)
                card.pop("hasFoil", None)
                card.pop("hasNonFoil", None)
                card.pop("isAlternative", None)
                card.pop("isOnlineOnly", None)
                card.pop("isOversized", None)
                card.pop("isStarter", None)
                card.pop("isTimeshifted", None)
                card.pop("mcmId", None)
                card.pop("mcmMetaId", None)
                card.pop("mcmName", None)
                card.pop("multiverseId", None)
                card.pop("number", None)
                card.pop("originalText", None)
                card.pop("originalType", None)
                card.pop("prices", None)
                card.pop("rarity", None)
                card.pop("scryfallId", None)
                card.pop("scryfallIllustrationId", None)
                card.pop("tcgplayerProductId", None)
                card.pop("variations", None)
                card.pop("watermark", None)
                card.pop("isFullArt", None)
                card.pop("isTextless", None)
                card.pop("isStorySpotlight", None)
                card.pop("isReprint", None)
                card.pop("isPromo", None)
                card.pop("isPaper", None)
                card.pop("isMtgo", None)
                card.pop("isArena", None)

                for foreign in card["foreignData"]:
                    foreign.pop("multiverseId", None)

                all_cards_data[card["name"]] = card

    return all_cards_data


def get_all_set_names(files_to_ignore: List[str]) -> List[str]:
    """
    This will create the SetCodes.json file
    by getting the name of all the files in
    the set_outputs folder and combining
    them into a list.
    :param files_to_ignore: Files to ignore in set_outputs folder
    :return: List of all set names
    """
    all_sets_data: List[str] = []

    for set_file in mtgjson4.COMPILED_OUTPUT_DIR.glob("*.json"):
        if set_file.stem in files_to_ignore:
            continue
        all_sets_data.append(
            get_set_name_from_file_name(set_file.name.split(".")[0].upper())
        )

    return sorted(all_sets_data)


def get_set_name_from_file_name(set_name: str) -> str:
    """
    Some files on Windows break down, such as CON. This is our reverse mapping.
    :param set_name: File name to convert to MTG format
    :return: Real MTG set code
    """
    if set_name.endswith("_"):
        return set_name[:-1]

    if set_name in mtgjson4.BANNED_FILE_NAMES:
        return set_name[:-1]

    return set_name


def get_all_set_list(files_to_ignore: List[str]) -> List[Dict[str, str]]:
    """
    This will create the SetList.json file
    by getting the info from all the files in
    the set_outputs folder and combining
    them into the old v3 structure.
    :param files_to_ignore: Files to ignore in set_outputs folder
    :return: List of all set dicts
    """
    all_sets_data: List[Dict[str, str]] = []

    for set_file in mtgjson4.COMPILED_OUTPUT_DIR.glob("*.json"):
        if set_file.stem in files_to_ignore:
            continue

        with set_file.open(encoding="utf-8") as f:
            file_content = json.load(f)

            set_data = {
                "baseSetSize": file_content.get("baseSetSize"),
                "code": file_content.get("code"),
                "meta": file_content.get("meta"),
                "name": file_content.get("name"),
                "releaseDate": file_content.get("releaseDate"),
                "totalSetSize": file_content.get("totalSetSize"),
                "type": file_content.get("type"),
            }

            if "parentCode" in file_content.keys():
                set_data["parentCode"] = file_content["parentCode"]

            all_sets_data.append(set_data)

    return sorted(all_sets_data, key=lambda set_info: set_info["name"])


def get_version_info() -> Dict[str, str]:
    """
    Create a version file for updating purposes
    :return: Version file
    """
    return {
        "version": mtgjson4.__VERSION__,
        "date": mtgjson4.__VERSION_DATE__,
        "pricesDate": mtgjson4.__PRICE_UPDATE_DATE__,
    }


def create_standard_only_output() -> Dict[str, Any]:
    """
    Use whatsinstandard to determine all sets that are legal in
    the standard format. Return an AllSets version that only
    has Standard legal sets.
    :return: AllSets for Standard only
    """
    # Get all sets currently in standard
    standard_url_content = util.get_generic_session().get(STANDARD_API_URL)
    standard_json = [
        set_obj["code"].upper()
        for set_obj in json.loads(standard_url_content.text)["sets"]
        if str(set_obj["enter_date"])
        < datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        < str(set_obj["exit_date"])
    ]

    return __handle_compiling_sets(standard_json, "Standard")


def create_modern_only_output() -> Dict[str, Any]:
    """
    Use gamepedia to determine all sets that are legal in
    the modern format. Return an AllSets version that only
    has Modern legal sets.
    :return: AllSets for Modern only
    """
    return __handle_compiling_sets(gamepedia.get_modern_sets(), "Modern")


def get_funny_sets() -> List[str]:
    """
    This will determine all of the "joke" sets and give
    back a list of their set codes
    :return: List of joke set codes
    """
    return [
        x["code"].upper()
        for x in scryfall.download(scryfall.SCRYFALL_API_SETS)["data"]
        if str(x["set_type"]) in ["funny", "memorabilia"]
    ]


def create_vintage_only_output(files_to_ignore: List[str]) -> Dict[str, Any]:
    """
    Create all sets, but ignore additional sets
    :param files_to_ignore: Files to default ignore in the output
    :return: AllSets without funny
    """
    return create_all_sets(files_to_ignore + get_funny_sets())


def create_deck_compiled_list(decks_to_add: List[Dict[str, str]]) -> Dict[str, Any]:
    """

    :param decks_to_add:
    :return:
    """
    return {
        "decks": decks_to_add,
        "meta": {
            "version": mtgjson4.__VERSION__,
            "date": mtgjson4.__VERSION_DATE__,
            "pricesDate": mtgjson4.__PRICE_UPDATE_DATE__,
        },
    }


def create_compiled_list(files_to_add: List[str]) -> Dict[str, Any]:
    """
    Create the compiled list output file
    :param files_to_add: Files to include in output
    :return: Dict to write
    """
    return {
        "files": sorted(files_to_add),
        "meta": {
            "version": mtgjson4.__VERSION__,
            "date": mtgjson4.__VERSION_DATE__,
            "pricesDate": mtgjson4.__PRICE_UPDATE_DATE__,
        },
    }


def create_and_write_compiled_outputs() -> None:
    """
    This method class will create the combined output files
    (ex: AllSets.json, AllCards.json, Standard.json)
    """
    # Compiled output files

    # CompiledList.json -- do not include ReferralMap
    write_to_file(
        mtgjson4.COMPILED_LIST_OUTPUT,
        create_compiled_list(
            list(set(mtgjson4.OUTPUT_FILES) - {mtgjson4.REFERRAL_DB_OUTPUT})
        ),
    )

    # Keywords.json
    key_words = wizards.compile_comp_output()
    write_to_file(mtgjson4.KEY_WORDS_OUTPUT, key_words)

    # CardTypes.json
    compiled_types = wizards.compile_comp_types_output()
    write_to_file(mtgjson4.CARD_TYPES_OUTPUT, compiled_types)

    # version.json
    version_info = get_version_info()
    write_to_file(mtgjson4.VERSION_OUTPUT, version_info)

    # SetList.json
    set_list_info = get_all_set_list(mtgjson4.OUTPUT_FILES)
    write_to_file(mtgjson4.SET_LIST_OUTPUT, set_list_info)

    # AllSets.json
    all_sets = create_all_sets(mtgjson4.OUTPUT_FILES)
    write_to_file(mtgjson4.ALL_SETS_OUTPUT, all_sets)

    # AllCards.json
    all_cards = create_all_cards(mtgjson4.OUTPUT_FILES)
    write_to_file(mtgjson4.ALL_CARDS_OUTPUT, all_cards)

    # Standard.json
    write_to_file(mtgjson4.STANDARD_OUTPUT, create_standard_only_output())

    # Modern.json
    write_to_file(mtgjson4.MODERN_OUTPUT, create_modern_only_output())

    # Vintage.json
    write_to_file(
        mtgjson4.VINTAGE_OUTPUT, create_vintage_only_output(mtgjson4.OUTPUT_FILES)
    )

    # decks/*.json
    deck_names = []
    for deck in magic_precons.build_and_write_decks(DECKS_URL):
        deck_name = util.capital_case_without_symbols(deck["name"])
        write_deck_to_file(f"{deck_name}_{deck['code']}", deck)
        deck_names.append(
            {
                "code": deck["code"],
                "fileName": deck_name,
                "name": deck["name"],
                "releaseDate": deck["releaseDate"],
            }
        )

    # DeckLists.json
    write_to_file(
        mtgjson4.DECK_LISTS_OUTPUT,
        create_deck_compiled_list(
            sorted(deck_names, key=lambda deck_obj: deck_obj["name"])
        ),
    )


def __handle_compiling_sets(set_codes: List[str], build_type: str) -> Dict[str, Any]:
    """
    Given a list of sets, compile them into an output file
    (Modern.json, Standard.json, etc)
    :param set_codes: List of sets to include
    :param build_type: String to show on display
    :return: Compiled output
    """
    return_data = {}
    for set_code in set_codes:
        set_file = mtgjson4.COMPILED_OUTPUT_DIR.joinpath(
            util.win_os_fix(set_code) + ".json"
        )

        if not set_file.is_file():
            LOGGER.warning(
                f"Set {set_code} not found in compiled outputs ({build_type})"
            )
            continue

        with set_file.open(encoding="utf-8") as f:
            file_content = json.load(f)
            return_data[set_code] = file_content

    return return_data
