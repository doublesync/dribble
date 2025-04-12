import os
import json
import pymem

from ..models import Player
from ..utils import HasValidCharacters, ConvertToReadableValue, BitLengthToByteLength
from ..models import GetStringFromCode, ConvertTeamType

# Initialize offsets variable
offsets = None


# Function to fetch offsets from a JSON file
def FetchOffsets(file_path):
    offsets_file = open(file_path, "r")
    offsets_dict = json.load(offsets_file)
    return offsets_dict


# Function to format the offsets to hexadecimal
def FormatOffsets(offsets_dict):
    try:
        formatted_offsets = {}

        # Traverse through the dictionary
        for category, data in offsets_dict.items():
            # Check if data is a dictionary (category like "Base")
            if isinstance(data, dict):
                formatted_offsets[category] = {}
                for key, value in data.items():
                    # If the value is a hex string starting with '0x'
                    if isinstance(value, str) and value.startswith("0x"):
                        try:
                            formatted_offsets[category][key] = int(value, 16)
                        except ValueError:
                            print(f"Error converting {key}: {value}")
                            formatted_offsets[category][key] = value
            else:
                # The rest of the categories are lists of dictionaries
                formatted_offsets[category] = []
                for offset in data:
                    offset_value = offset.get("offset", "")
                    if isinstance(offset_value, str) and offset_value.startswith("0x"):
                        try:
                            offset["offset"] = int(offset_value, 16)
                        except ValueError:
                            print(f"Error converting Offset: {offset_value}")
                            offset["offset"] = (
                                offset_value  # Keep original if conversion fails
                            )
                    formatted_offsets[category].append(offset)

        return formatted_offsets

    except Exception as e:
        print(f"Unexpected error formatting offsets: {e}")
        return None


# Function to get a specific offset by category and key
def GetOffset(category, key):
    """
    Get a specific offset by category and key.

    :param category: The category of the offset (e.g., "Attributes").
    :param key: The key of the offset (e.g., "Driving Layup").
    """
    # Check if the offsets dictionary is initialized
    category = offsets.get(category, None)
    if category:
        for offset in category:
            if offset["name"] == key:
                return offset
    # If the category is a dictionary (like "Base"), handle it differently
    return None


# Function to initialize offset
def InitializeOffsets(file_path):
    """
    Initialize offsets by fetching and formatting them from the JSON file.
    """
    global offsets
    # Check if a file path is provided; if not, use the default path
    offsets = FetchOffsets(file_path)
    # Format the offsets to hexadecimal
    if offsets:
        offsets = FormatOffsets(offsets)
        if not offsets:
            raise ValueError("Failed to format offsets.")
    else:
        raise ValueError("Failed to fetch offsets.")


# Read UTF-16 strings from memory
def ReadUTF16String(game, address, length):
    """
    Reads a UTF-16 string from memory and returns it as a Python string.

    game: The game interface object with a `memory.read_bytes` method.
    address: The memory address where the UTF-16 string begins.
    length: The number of bytes to read from memory (should be an even number, since UTF-16 uses 2 bytes per character).
    return: The decoded and cleaned string, truncated at the first null terminator.
    """
    raw = game.memory.read_bytes(address, length)  # Raw bytes from memory
    decoded = raw.decode("utf-16-le", errors="ignore")  # Decode to Python string
    cleaned = decoded.split("\x00")[0]  # Truncate at first null character
    return cleaned


# Read the integer value from memory and format it if needed
def ReadInteger(game, address, length, return_readable=False, start_bit=0):
    """
    Reads an integer from memory, optionally extracting a specific bit range.

    :param game: The game memory reader instance.
    :param address: The memory address to read from.
    :param length: The number of bits to read.
    :param return_readable: Whether to format the value for readability.
    :param startBit: The starting bit position (default is 0, meaning full integer).
    :return: The extracted integer value.

    "num_bytes" Explanation:
        - Calculate the number of bytes needed to fully cover the requested bit range.
        - We add startBit because the value might not start at a byte boundary.
        - We add 7 before integer division to round up, ensuring we read enough bytes.
        - Example: For startBit=6 and length=8, we need (6 + 8 + 7) // 8 = 2 bytes,
        because the 8 bits start in the middle of the byte and span two bytes.
    """
    # Calculate the number of bytes needed to store the value
    num_bytes = BitLengthToByteLength(length, start_bit)
    raw_bytes = game.memory.read_bytes(address, num_bytes)
    integer_value = int.from_bytes(raw_bytes, byteorder="little")

    # Apply the start bit and mask to extract the correct value
    mask = (1 << length) - 1  # Create a mask for the bit length
    integer_value = (
        integer_value >> start_bit
    ) & mask  # Extract the bits based on startBit and length

    # Format the result if needed
    if return_readable:
        integer_value = ConvertToReadableValue(integer_value)

    # Return the extracted integer value
    return integer_value


# Get the data for a specific team
def GetTeamAddress(game, player_address):
    """
    Gets the memory address of the team data for a given player address.

    :param game: The game memory reader instance.
    :param player_address: The memory address of the player data.
    :return: The memory address of the team data or None if not found.
    """
    # Find the team address for a player by reading the memory at the specified offset
    team_address = game.memory.read_bytes(
        player_address + offsets["Base"]["Offset Player Team"], 8
    )  # Dereference the pointer to get the actual team address
    team_address = int.from_bytes(team_address, byteorder="little")
    # Return the team address if it was successfully read, otherwise return None
    return team_address if team_address else None


# Get the data for the team of a player
def GetTeamData(game, team_address):
    """
    Get the team data for a given team address in memory.

    :param game: The game memory reader instance.
    :param team_address: The memory address of the team data.
    :return: A dictionary containing the team data.
    """
    if not team_address:
        return None

    # Assuming we have a predefined offset for team data, read the team details
    # FYI: "read_bytes" takes byte-size for length, while "ReadInteger" takes bit-size for length
    team_name = (
        game.memory.read_bytes(
            team_address + offsets["Base"]["Offset Player Team Name"], 40
        )
        .decode("utf-16-le", errors="ignore")
        .rstrip("\x00")
    )
    team_short_name = (
        game.memory.read_bytes(
            team_address + offsets["Base"]["Offset Player Team Short Name"], 8
        )
        .decode("utf-16-le", errors="ignore")
        .rstrip("\x00")
    )
    team_year = ReadInteger(
        game,
        team_address + offsets["Base"]["Offset Player Team Year"],
        7,
        return_readable=False,
        start_bit=3,
    )
    team_type = ReadInteger(
        game,
        team_address + offsets["Base"]["Offset Player Team Type"],
        5,
        return_readable=False,
        start_bit=2,
    )
    team_data = {
        "Key": "",
        "Name": team_name,
        "Short Name": team_short_name,
        "Year": f"{team_year - 1}-{team_year}" if team_year > 0 else "Current",
        "Type": ConvertTeamType(team_type),
    }
    # Set a "key" for the team based on type/year and short name
    if team_data["Type"] == "Normal":
        team_data["Key"] = f"{team_data['Year']} {team_short_name}"
    else:
        team_data["Key"] = f"{team_data['Type']} {team_short_name}"
    # Validate that the team names exists & are valid characters
    if not team_name or not team_short_name:
        return None  # Skip teams with missing names
    if (
        HasValidCharacters(team_name) == False
        or HasValidCharacters(team_short_name) == False
    ):
        return None  # Skip teams with invalid characters

    return team_data


# Get player data from memory and create a Player object
def BuildPlayer(game, player_id, explicit_player_address=None):
    """
    Builds player data from memory and creates a Player object."

    :param game: The game memory reader instance.
    :param player_base_address: The base address of the player data.
    :param player_id: The ID of the player to retrieve data for.
    :param explicit_player_address: Optional explicit address for the player data.
    :return: A Player object containing the player's data.
    """
    try:
        # Calculate Player Base Address: Read 8-bytes because this will be a 64-bit pointer to the player data
        # Note: This should probably only be done once and stored, but for simplicity and centralization, it's done here
        player_base_address = game.memory.read_bytes(
            game.base_address + offsets["Base"]["Player Base Address"], 8
        )  # Dereference the pointer to get the actual player base address
        player_base_address = int.from_bytes(player_base_address, byteorder="little")

        # Calculate the specific player address
        if explicit_player_address:
            player_address = explicit_player_address
        else:
            player_address = (
                player_base_address
                + offsets["Base"]["Player Offset Length"] * player_id
            )

        # Read player team data (address points to team address, where we can then get team details)
        team_address = GetTeamAddress(game, player_address)
        team_data = GetTeamData(game, team_address) or {}

        # Read player vitals data
        first_name_address = player_address + offsets["Base"]["Offset First Name"]
        last_name_address = player_address + offsets["Base"]["Offset Last Name"]

        # Read the names (assuming they are stored as UTF-16 strings)
        player_vitals = {
            "First Name": ReadUTF16String(game, first_name_address, 40),
            "Last Name": ReadUTF16String(game, last_name_address, 40),
        }

        # TODO: Remove this print statement once we have a better way to show player data
        # print(f"\n[cyan]Sync2K is reading Player #{player_id}...[/cyan]\n")
        # print(f"[yellow]First Name: {player_vitals['First Name']}[/yellow]")
        # print(f"[yellow]Last Name: {player_vitals['Last Name']}[/yellow]")

        # Check if the first and last names are valid characters
        if (
            HasValidCharacters(player_vitals["First Name"]) == False
            or HasValidCharacters(player_vitals["Last Name"]) == False
        ):
            return None  # Skip invalid characters

        # Initialize dictionaries for player attributes, badges, and tendencies
        player_skill_categories = {
            "Vitals": offsets["Vitals"],
            "Attributes": offsets["Attributes"],
            "Badges": offsets["Badges"],
            "Tendencies": offsets["Tendencies"],
            "Hotzones": offsets["Hotzones"],
            "Signatures": offsets["Signatures"],
            "Gear": offsets["Gear"],
            "Accessories": offsets["Accessories"],
        }
        player_skills = {
            "Vitals": player_vitals,
            "Attributes": {},
            "Badges": {},
            "Tendencies": {},
            "Hotzones": {},
            "Signatures": {},
            "Gear": {},
            "Accessories": {},
        }

        # Iterate over each skill category and read the data
        for skill_category, category_data in player_skill_categories.items():
            return_readable = True if skill_category == "Attributes" else False
            for item in category_data:
                name = item["name"]
                length = item["length"]
                address = player_address + item["offset"]
                start_bit = item.get("startBit", 0)  # Default to 0 if not specified
                value = ReadInteger(
                    game,
                    address,
                    length,
                    start_bit=start_bit,
                    return_readable=return_readable,
                )
                string_repr = None
                # Set the value in the player_skills dictionary, using the string representation if available
                # This is so we can show string representations instead of integer codes in memory exports
                # Attributes, badges, and tendencies are always in integer form, so we don't need to check for them
                if skill_category not in ["Attributes", "Badges", "Tendencies"]:
                    string_repr = GetStringFromCode(name, value)
                player_skills[skill_category][name] = (
                    string_repr if string_repr else value
                )

        # Create a Player object
        player_object = Player(
            address=player_address,
            team=team_data,
            vitals=player_skills["Vitals"],
            attributes=player_skills["Attributes"],
            badges=player_skills["Badges"],
            tendencies=player_skills["Tendencies"],
            hotzones=player_skills["Hotzones"],
            signatures=player_skills["Signatures"],
            gear=player_skills["Gear"],
            accessories=player_skills["Accessories"],
        )

        # Return the Player object
        return player_object

    except pymem.exception.MemoryReadError:
        return None
