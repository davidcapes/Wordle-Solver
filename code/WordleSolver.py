import json
import itertools

from numba import njit, prange
from wordfreq import word_frequency
from english_words import get_english_words_set

from BasicStructures import *

# Macros / Global Constants
WORD_LENGTH = 5
ALPHABET_LENGTH = 26

NULL_INTEGER = -1
NULL_WORD = NULL_CHAR * WORD_LENGTH


# Conversion Functions
def char_to_int(input_char):
    return ord(input_char) - ord('a')


def int_to_char(input_int):
    return chr(ord('a') + input_int)


# Constraint Storage Structures
extra_words = ["manly", "mucky", "latte", "imply", "daily", "lover", "rerun", "unfit"]
fake_words = {'brady', 'turin', 'dylan', 'dolan', 'lanka', 'milan', 'cathy', "alton", 'mckee', 'mcgee', 'poole',
              'della', 'dinah', 'syria', 'akron'}


@njit
def enc_is_word_consistent(encoded_word, chars_not_present, char_placements, char_nonplacements,
                           word_length=WORD_LENGTH, alphabet_length=ALPHABET_LENGTH):
    """
    :param encoded_word: A 1-D integer array with size=WORD_LENGTH. This array represents a word, each element
                         corresponds to an alphabetical letter (a=0, b=1, ..., z=25).
    :param chars_not_present: A 1-D boolean Array size=ALPHABET_LENGTH. The index of the array corresponds to letter of
                              alphabet (a=0, b=1, ...), the value at that index is a boolean representing whether that
                              letter is not in the underlying word (True=letter definitely not present,
                              False=letter may be present).
    :param char_placements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                            letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the indexes
                            of the underlying word that must contain that corresponding letter. NULL_INTEGER is used
                            to initialize empty values.
    :param char_nonplacements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                               letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the
                               indexes of the underlying word that must not contain that corresponding letter.
                               NULL_INTEGER is used to initialize empty values.
    :param word_length: Same value as the macro WORD_LENGTH. Inputted to avoid drawing upon global variables.
    :param alphabet_length: Same value as the macro ALPHABET_LENGTH. Inputted to avoid drawing upon global variables.

    :return: A boolean value corresponding to whether or not the encoded word is consistent with the constraints;
             chars_not_present, char_placements, and char_nonplacements.
    """

    # Ensure consistency with word_length
    if len(encoded_word) != word_length:
        return False

    # Ensure consistency with chars not present
    for c in encoded_word:
        if chars_not_present[c]:
            return False

    # Ensure consistency with placements.
    for c in range(alphabet_length):
        for position in char_placements[c]:
            if position == NULL_INTEGER:
                break
            elif encoded_word[position] != c:
                return False

    # Ensure consistency with nonplacements.
    for c in range(alphabet_length):
        if char_nonplacements[c][0] != NULL_INTEGER:
            if c not in encoded_word:
                return False
            for position in char_nonplacements[c]:
                if position == NULL_INTEGER:
                    break
                elif encoded_word[position] == c:
                    return False

    return True


@njit
def enc_get_consistent_words(encoded_words, chars_not_present, char_placements, char_nonplacements,
                             word_length=WORD_LENGTH, alphabet_length=ALPHABET_LENGTH, null_integer=NULL_INTEGER):
    """
    :param encoded_words: A 2-D integer array with size=(len(words), WORD_LENGTH). Each element of this array represents
                          a word, each element of those elements corresponds to an alphabetical letter (a=0, b=1, ...,
                          z=25).
    :param chars_not_present: A 1-D boolean Array size=ALPHABET_LENGTH. The index of the array corresponds to letter of
                              alphabet (a=0, b=1, ...), the value at that index is a boolean representing whether that
                              letter is not in the underlying word (True=letter definitely not present,
                              False=letter may be present).
    :param char_placements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                            letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the indexes
                            of the underlying word that must contain that corresponding letter. NULL_INTEGER is used
                            to initialize empty values.
    :param char_nonplacements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                               letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the
                               indexes of the underlying word that must not contain that corresponding letter.
                               NULL_INTEGER is used to initialize empty values.
    :param word_length: Same value as the macro WORD_LENGTH. Inputted to avoid drawing upon global variables.
    :param alphabet_length: Same value as the macro ALPHABET_LENGTH. Inputted to avoid drawing upon global variables.
    :param null_integer: Same value as the macro NULL_INTEGER. Inputted to avoid drawing upon global variables.

    :return: A 2-D integer array size=(unknown, WORD_LENGTH). This array represents a list of words, each element of
             the first axis corresponds to an encoded word. Each element of this word (second axis) corresponds to an
             alphabetical letter (a=0, b=1, ..., z=25). This array only contains words that were consistent with the
             constraints; chars_not_present, char_placements, and char_nonplacements.
    """

    # Static variables to consistency.
    consistent = 1
    inconsistent = 0

    # Determine amount of consistent words, and record the indexes of which ones are consistent.
    indexes = np.full(len(encoded_words), inconsistent, dtype=np.int8)
    consistent_words_count = 0
    for i, word in enumerate(encoded_words):
        if enc_is_word_consistent(word, chars_not_present, char_placements, char_nonplacements, word_length,
                                  alphabet_length):
            indexes[i] = consistent
            consistent_words_count += 1

    # Create and fill a new array based on the amount and indexes of consistent words found above.
    consistent_words = np.full((consistent_words_count, word_length), null_integer, dtype=np.int8)
    k = 0
    for i, word in enumerate(encoded_words):
        if indexes[i] == consistent:
            for j in range(word_length):
                consistent_words[k][j] = encoded_words[i][j]
            k += 1

    return consistent_words


@njit
def enc_update_constraints(encoded_guess_word, encoded_underlying_word, chars_not_present, char_placements,
                           char_nonplacements, word_length=WORD_LENGTH):
    """
    :param encoded_guess_word: A 1-D integer array size=WORD_LENGTH. This array represents a word, each element
                               corresponds to an alphabetical letter (a=0, b=1, ..., z=25).
    :param encoded_underlying_word: A 1-D integer array size=WORD_LENGTH. This array represents a word, each
                                    element corresponds to an alphabetical letter (a=0, b=1, ..., z=25).
    :param chars_not_present: A 1-D boolean Array size=ALPHABET_LENGTH. The index of the array corresponds to letter of
                              alphabet (a=0, b=1, ...), the value at that index is a boolean representing whether that
                              letter is not in the underlying word (True=letter definitely not present,
                              False=letter may be present).
    :param char_placements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                            letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the indexes
                            of the underlying word that must contain that corresponding letter. NULL_INTEGER is used
                            to initialize empty values.
    :param char_nonplacements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                               letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the
                               indexes of the underlying word that must not contain that corresponding letter.
                               NULL_INTEGER is used to initialize empty values.
    :param word_length: Same value as the macro WORD_LENGTH. Inputted to avoid drawing upon global variables.

    :return: None

    This function determines what additional constraint information would be provided from the given guess word if
    the underlying word is known. Thus, chars_not_present, char_placements, and char_nonplacements are updated
    accordingly with this information.
    """

    for i, guess_char in enumerate(encoded_guess_word):
        char_not_present = True
        for j, underlying_char in enumerate(encoded_underlying_word):
            if guess_char == underlying_char:
                char_not_present = False

                # Update char_placements.
                if i == j:
                    for k in range(word_length):
                        if char_placements[guess_char][k] == i:
                            break
                        elif char_placements[guess_char][k] == NULL_INTEGER:
                            char_placements[guess_char][k] = i
                            break

                # Update char_nonplacements.
                else:
                    for k in range(word_length):
                        if char_nonplacements[guess_char][k] == i:
                            break
                        elif char_nonplacements[guess_char][k] == NULL_INTEGER:
                            char_nonplacements[guess_char][k] = i
                            break

        # Update chars_not_present.
        if char_not_present:
            chars_not_present[guess_char] = True

    return


@njit(parallel=True)
def enc_get_scores(encoded_words, chars_not_present, char_placements, char_nonplacements, word_length=WORD_LENGTH,
                   alphabet_length=ALPHABET_LENGTH, null_integer=NULL_INTEGER):
    """
    :param encoded_words: A 2-D integer array size=(unknown, WORD_LENGTH). This array represents a list of words, each
                         element of the first axis corresponds to an encoded word. Each element of this word (second
                         axis) corresponds to an alphabetical letter (a=0, b=1, ..., z=25).
    :param chars_not_present: A 1-D boolean Array size=ALPHABET_LENGTH. The index of the array corresponds to letter of
                              alphabet (a=0, b=1, ...), the value at that index is a boolean representing whether that
                              letter is not in the underlying word (True=letter definitely not present,
                              False=letter may be present).
    :param char_placements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                            letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the indexes
                            of the underlying word that must contain that corresponding letter. NULL_INTEGER is used
                            to initialize empty values.
    :param char_nonplacements: A 2-D integer Array size=(ALPHABET_LENGTH, WORD_LENGTH). The first index corresponds to
                               letter of alphabet (a=0, b=1, ...). The value of this index is an array listing the
                               indexes of the underlying word that must not contain that corresponding letter.
                               NULL_INTEGER is used to initialize empty values.
    :param word_length: Same value as the macro WORD_LENGTH. Inputted to avoid drawing upon global variables.
    :param alphabet_length: Same value as the macro ALPHABET_LENGTH. Inputted to avoid drawing upon global variables.
    :param null_integer: Same value as the macro NULL_INTEGER. Inputted to avoid drawing upon global variables.

    :return: A 1-D integer Array size=len(encoded_words). Each index of the array contains a score which corresponds to
             the score associated with the encoded_word obtained by indexing encoded_words at that location. This score
             corresponds to how good of a choice that word is in Wordle for narrowing down the overall pool of words,
             thus smaller scores are considered better.
    """

    # Create relevant dats structures.
    consistent_words = enc_get_consistent_words(encoded_words, chars_not_present, char_placements, char_nonplacements,
                                                word_length, alphabet_length, null_integer)
    scores = np.full(len(encoded_words), null_integer, dtype=np.int32)

    # Iterate through guess_words
    for i in prange(len(encoded_words)):
        guess_word = encoded_words[i]
        score = 0

        for underlying_word in consistent_words:

            # Calculate updated constraints.
            new_chars_not_present = np.copy(chars_not_present)
            new_char_placements = np.copy(char_placements)
            new_char_nonplacements = np.copy(char_nonplacements)
            enc_update_constraints(guess_word, underlying_word, new_chars_not_present, new_char_placements,
                                   new_char_nonplacements, word_length)

            # Calculate score increment.
            score_increment = 0
            for new_word in consistent_words:
                if enc_is_word_consistent(new_word, new_chars_not_present, new_char_placements, new_char_nonplacements,
                                          word_length, alphabet_length):
                    score_increment += 1
            score_increment = max(0, score_increment - 1)
            score += score_increment

        # Slightly bias the score to favour consistant guess words.
        if not enc_is_word_consistent(guess_word, chars_not_present, char_placements, char_nonplacements,
                                      word_length, alphabet_length):
            score += 1
        scores[i] = score

    return scores


def choose_word(constraints, opening_book_directory="../files/opening_book.json", words_to_exclude=None):
    """
    :param constraints: An object of type Constraints, as defined in BasicStructures. This stores the constraints that
                        possible underlying words for the wordle must follow.
    :param opening_book_directory: A string representing the pathway to a json file. This file constraints directions
           for what words are the best choice for certain constraints.
    :param words_to_exclude: A set containing words that are not allowed to be guessed.
    :return: A word string, corresponding to the best word choice given the inputted constraints.
    """

    # Return result in opening book if present.
    if words_to_exclude is None:
        words_to_exclude = set()
    if not words_to_exclude:
        try:
            with open(opening_book_directory, 'r') as openfile:
                opening_book = dict(json.load(openfile))
            if str(constraints) in opening_book:
                return opening_book[str(constraints)]
        except json.decoder.JSONDecodeError or FileNotFoundError:
            pass

    # Convert constraints into relevant data structures.
    chars_not_present = np.full(ALPHABET_LENGTH, False, dtype=np.int8)
    char_placements = np.full((ALPHABET_LENGTH, WORD_LENGTH), NULL_INTEGER, dtype=np.int8)
    char_nonplacements = np.full((ALPHABET_LENGTH, WORD_LENGTH), NULL_INTEGER, dtype=np.int8)

    for r in range(ROWS):
        for c in range(COLUMNS):
            if constraints.grid[r][c].char != NULL_CHAR:
                color = constraints.grid[r][c].color
                char_int = char_to_int(constraints.grid[r][c].char)

                if color == Color.GREY:
                    if char_placements[char_int][0] != NULL_INTEGER:
                        color = Color.YELLOW
                    else:
                        chars_not_present[char_int] = True

                if color == Color.GREEN:
                    for i in range(WORD_LENGTH):
                        if char_placements[char_int][i] == NULL_INTEGER:
                            char_placements[char_int][i] = c
                            break

                if color == Color.YELLOW:
                    for i in range(WORD_LENGTH):
                        if char_nonplacements[char_int][i] == NULL_INTEGER:
                            char_nonplacements[char_int][i] = c
                            break

    # Calculate scores and choose best word.
    words = np.array([word for word in sorted(list(get_english_words_set(['web2'], lower=True)) + list(extra_words))
                      if word not in fake_words and len(word) == WORD_LENGTH and word.isalpha() and
                      word not in words_to_exclude])
    int_words = np.array([[char_to_int(c) for c in word] for word in words], dtype=np.int8)
    options = enc_get_consistent_words(int_words, chars_not_present, char_placements, char_nonplacements)
    if len(options) == 0:
        return NULL_WORD
    word_scores_array = enc_get_scores(int_words, chars_not_present, char_placements, char_nonplacements)
    word_score_dict = {words[i]: word_scores_array[i] - word_frequency(words[i], lang='en') for i in range(len(words))}
    return min(words, key=word_score_dict.get)


def construct_opening_book(opening_book_directory="../files/opening_book.json"):
    """
    :param opening_book_directory: A directory on where to save the opening book file
    :return: None

    This void function constructs a json file in the inputted directory that corresponds to an opening book for wordle
    at depth 2.
    """

    # Open opening book file and setup data structures.
    opening_book = {}
    try:
        with open(opening_book_directory, 'r') as f:
            json_object = json.load(f)
            opening_book = dict(json_object)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        pass
    constraints = Constraints()

    # Determine first word choice.
    first_word = choose_word(constraints, opening_book_directory)
    opening_book[str(constraints)] = first_word
    for i in range(WORD_LENGTH):
        constraints.grid[0][i].char = first_word[i]

    # Determine second word choice given first word choice.
    color_possibilities = [iter(Color) for _ in range(WORD_LENGTH)]
    for color_choice in itertools.product(*color_possibilities):
        for i, c in enumerate(color_choice):
            constraints.grid[0][i].color = c
        choice_word = choose_word(constraints)
        if choice_word != NULL_WORD and choice_word != first_word:
            opening_book[str(constraints)] = choice_word
        for i, c in enumerate(color_choice):
            constraints.grid[0][i].color = Color.GREY

    # Add obtained information to json files.
    with open(opening_book_directory, 'w') as f:
        json_object = json.dumps(opening_book, indent=2)
        f.write(json_object)
