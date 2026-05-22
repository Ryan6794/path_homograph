"""
CSE 453 - Lab 05: Path Homograph Attack & Mitigation
======================================================
Team Members: Ryan, Emily, Raquel
 
WORK BREAKDOWN:
  - Person 1: Canonicalization core (C() function) + path symbol research
  - Person 2: Test cases (homographs & non-homographs) + test runner functions
  - Person 3: Homograph detection (H() function) + menu/UI + report writing
 
Theoretical Framework:
  e  = encoding       -> the raw string path entered by the user
  r  = rendition      -> a file handle (we do NOT actually open files here)
  R()= rendering func -> would be open(e, 'r'), but we avoid it per instructions
  c  = canon          -> the absolute, normalized path (our chosen canonical form)
  C()= canonicalization function -> converts e into c
  H()= homograph function        -> returns True if two encodings map to same c  [Person 3]
"""




# =============================================================================
# Canonicalization (C function) + Path Symbol Research
# =============================================================================
# TASK OVERVIEW:
#   Research all Linux path symbols: / .. . ~ (home), symlinks, trailing slashes,
#   double slashes (//), mixed slashes, etc.
#   Build C() to convert any raw path string into its canonical absolute form
#   WITHOUT using os.path or filesystem.canonical().
#
# SYMBOLS TO HANDLE:
#   /          -> root
#   ./         -> current directory (no-op)
#   ../        -> go up one level
#   //         -> treated same as / on Linux
#   trailing / -> strip it (usually)
#   ~          -> expand to home directory (hardcode or accept as input)

CURRENT_WORKING_DIRECTORY = "/home/user/cse453"  # Set agreed-upon CWD for test cases
HOME_DIRECTORY = "/home/user"                     # Used if ~ expansion is implemented


def canonicalize(path: str, cwd: str = CURRENT_WORKING_DIRECTORY) -> str:
    """
    C() — Convert a raw file path encoding into its canonical absolute form.

    Args:
        path: The raw input path string (the encoding 'e')
        cwd:  The current working directory (needed for relative paths)

    Returns:
        A canonical absolute path string (the canon 'c')

        1. Handle ~ expansion to HOME_DIRECTORY
        2. If path is relative (doesn't start with /), prepend cwd
        3. Split the path on '/'
        4. Iterate through each segment:
            - skip empty segments and '.' segments
            - on '..' pop the last element from the result stack (if stack is non-empty)
            - otherwise push the segment onto the result stack
        5. Reassemble with '/' and ensure it starts with '/'
        6. Return the canonical string
    """
    

    # Step 1: Remove leading and trailing whitespace
    path = path.strip()


    # Step 2: Expand the tilde (~) to the home directory.
    #   "~"        -> expand to HOME_DIRECTORY exactly
    #   "~/..."    -> replace ~ with HOME_DIRECTORY
    #   anything else starting with ~ is left alone (edge case)
    if path == "~":
        path = HOME_DIRECTORY
    elif path.startswith("~/"):
        # Replace only the leading ~ so the rest of the path is preserved
        path = HOME_DIRECTORY + path[1:]  # path[1:] keeps the '/' and everything after


    # Step 3: If the path is relative (doesn't start with '/'), prepend the cwd
    # Examples of relative paths:
    #   "secret/password.txt"       -> relative to cwd
    #   "../secret/password.txt"    -> relative to cwd, then up one level
    #   "./secret/password.txt"     -> relative to cwd (. = cwd itself)
    if not path.startswith("/"):
        path = cwd + "/" + path  # Prepend cwd and ensure there's a slash


    # Step 4: Split the full path string on the '/' separator.
    # Example:
        #   "/home/user/../secret/password.txt".split("/")
        #   -> ['', 'home', 'user', '..', 'secret', 'password.txt']
    segments = path.split("/")


    # Step 5: Walk through segments and resolve . and .. using a stack.
    stack = []  # Holds the resolved path components (no slashes stored here)

    for segment in segments:

        if segment == "" or segment == ".":
            # Empty string: result of splitting on '/' at the start, end,
            # or anywhere there are consecutive slashes (e.g. //).
            # Single dot: means "current directory" — nothing changes.
            # Either way, we skip and move on.
            continue

        elif segment == "..":
            # Double dot: move up one directory level.
            # If the stack is non-empty, remove the last component.
            # If the stack IS empty, we're already at root — stay there.
            # (You cannot go above / on Linux.)
            if stack:
                stack.pop()
            # If stack is empty, do nothing — we're at root already

        else:
            # Normal directory name or filename — add it to our path stack.
            stack.append(segment)

    # Step 6: Reassemble the canonical path with '/' and ensure it starts with '/'# Step 6: Reassemble the canonical path from the stack.
    # Join all components with '/' and prepend the root '/'.
    # Examples:
    #   stack = ['home', 'user', 'secret', 'password.txt']
    #   -> "/home/user/secret/password.txt"
    #
    #   stack = []  (path resolved to root)
    #   -> "/"
    canonical_path = "/" + "/".join(stack)

    return canonical_path


# =============================================================================
# PERSON 2 — Test Cases (Homographs & Non-Homographs) + Test Runner Functions
# =============================================================================
# TASK OVERVIEW:
#   Define the forbidden file path.
#   Build two lists of test cases with descriptions.
#   Write run_non_homograph_tests() and run_homograph_tests() functions.
#   Each function prints results and pass/fail for every test case.
#
# GOAL:
#   Cover every Linux path symbol with 2-3 test cases per construct (per instructions).

FORBIDDEN_FILE = "/home/user/secret/password.txt"

# Non-Homographs: paths that look similar but are DIFFERENT resources
# Format: (path_string, explanation)
NON_HOMOGRAPHS = [
    # Basic wrong directory / wrong file
    ("/home/user/password.txt", "Same filename but in different directory"),
    ("/home/user/secret/password.bak", "Different file extension"),

    # Double slash cases resolving to different files
    ("/home//user/secret/passwords.txt", "Extra slash in path, but different filename"),
    ("/home/user//secret2/password.txt", "Extra slash in path, different directory"),
    ("//home/user/secret/passwords.txt", "Extra leading slash, but different filename"),

    # Trailing slash testing on non-matching resources
    ("/home/user/secret2/", "Trailing slash on a completely different directory path"),
    ("/home/user/cse453////", "Multiple trailing slashes on a different directory path"),

    # Similar-looking directory names
    ("/home/user/secrets/password.txt", "Directory 'secrets' is not 'secret'"),
    ("/home/user/secret1/password.txt", "Directory name differs by one character"),
    ("/home/user/secret/passwords.txt", "Filename pluralized"),

    # Dots that change the resource completely
    ("/home/user/secret/password.txt.", "Linux treats trailing dot as a unique extension character"),
    ("../password.txt", "Resolves to /home/user/password.txt (wrong directory)"),
    ("./secret/../password.txt", "Resolves to /home/user/cse453/password.txt (wrong directory)"),

    # Hidden file / misleading name
    ("/home/user/secret/.password.txt", "Hidden file, not the forbidden file"),
    ("/home/user/secret/password.txt.bak", "Backup file, not the real one"),
]

# Homographs: paths that are DIFFERENT strings but refer to the SAME resource
# Format: (path_string, explanation)
HOMOGRAPHS = [
    # Trailing slashes targeting the target file)
    ("/home/user/secret/password.txt/", "Trailing slash is stripped by engine stack, resolving to forbidden file"),
    ("/home/user/secret/password.txt////", "Multiple trailing slashes collapse and resolve to forbidden file"),

    # Relative path navigation from CWD (/home/user/cse453)
    ("../../user/secret/password.txt", "Goes up to /home, then down into user/secret/password.txt"),
    ("../secret/password.txt", "Goes up to /home/user, then down into secret/password.txt"),
    
    # Absolute redundant directory traversal
    ("/home/user/secret/../secret/password.txt", "Absolute redundant directory traversal"),
    
    # Double slashes that still resolve to the same file
    ("/home//user/secret/password.txt", "Internal duplicate slashes are ignored by POSIX standard"),
    ("//home/user/secret/password.txt", "Double slash at root resolves to root in Linux"),
    ("/home/user//secret//password.txt", "Multiple internal double slashes normalize cleanly"),

    # Redundant current directory dots
    ("/home/user/secret/./password.txt", "Redundant single-dot current-directory reference is ignored"),
    ("/home/./user/./secret/./password.txt", "Multiple mid-path single dots cleanly normalize away"),
]

# Test runner functions 

def run_non_homograph_tests() -> None:
    """
    (Person 2):
        For each (path, explanation) in NON_HOMOGRAPHS:
        1. Call is_homograph(path, FORBIDDEN_FILE)
        2. Assert/check that the result is FALSE
        3. Print the path, explanation, canonical form, and PASS/FAIL result
    """
    print("\n=== NON-HOMOGRAPH TEST CASES ===")
    for path, explanation in NON_HOMOGRAPHS:
        result = is_homograph(path, FORBIDDEN_FILE)
        canon = canonicalize(path)
        passed = (result is False)
        status = "PASS" if passed else "FAIL"

        print(f"\nPath:      {path}")
        print(f"Explanation: {explanation}")
        print(f"Canonical:   {canon}")
        print(f"Expected:    False")
        print(f"Result:      {result}")
        print(f"Status:      {status}")
 
 
def run_homograph_tests() -> None:
    """
    (Person 2):
        For each (path, explanation) in HOMOGRAPHS:
        1. Call is_homograph(path, FORBIDDEN_FILE)
        2. Assert/check that the result is TRUE
        3. Print the path, explanation, canonical form, and PASS/FAIL result
    """
    print("\n=== HOMOGRAPH TEST CASES ===")
    for path, explanation in HOMOGRAPHS:
        result = is_homograph(path, FORBIDDEN_FILE)
        canon = canonicalize(path)
        passed = (result is True)
        status = "PASS" if passed else "FAIL"

        print(f"\nPath:      {path}")
        print(f"Explanation: {explanation}")
        print(f"Canonical:   {canon}")
        print(f"Expected:    True")
        print(f"Result:      {result}")
        print(f"Status:      {status}")
 
 
# =============================================================================
# PERSON 3 — Homograph Detection (H function) + Menu/User Interface
# =============================================================================
# TASK OVERVIEW:
#   Build is_homograph() using the canonicalize() function from Person 1.
#   Build the main menu loop so the user can:
#     (1) Run non-homograph test cases
#     (2) Run homograph test cases
#     (3) Manually enter two paths and compare them
#     (4) Quit
#
# NOTE: is_homograph() must call canonicalize() — do NOT compare raw strings.

def is_homograph(path1: str, path2: str, cwd: str = CURRENT_WORKING_DIRECTORY) -> bool:
    """
    H() — Determine if two path encodings refer to the same resource.

    Args:
        path1: First path encoding (e1)
        path2: Second path encoding (e2)
        cwd:   Current working directory for resolving relative paths

    Returns:
        True  if C(path1) == C(path2)  (they ARE homographs)
        False otherwise

    (Person 3):
        1. Call canonicalize(path1, cwd) -> canon1
        2. Call canonicalize(path2, cwd) -> canon2
        3. Return canon1 == canon2
    """
    canon1 = canonicalize(path1, cwd)
    canon2 = canonicalize(path2, cwd)

    # Seeing if they are the same
    return canon1 == canon2


def manual_comparison() -> None:
    """
    (Person 3):
        Prompt the user for two file paths.
        Call is_homograph() on them.
        Print both canonical forms and whether they are homographs.

    Example output:
        Specify the first filename:  ../../secret/password.txt
        Specify the second filename: /home/user/secret/password.txt
        Canon 1: /home/user/secret/password.txt
        Canon 2: /home/user/secret/password.txt
        The paths ARE homographs.
    """

    # Striping just in case
    path1 = input("What is the first file:").strip()
    path2 = input("What is the second file:").strip()

    canon1 = canonicalize(path1)
    canon2 = canonicalize(path2)

    same = is_homograph(path1, path2)

    print(f"This is file 1: {canon1}")
    print(f"This is file 2: {canon2}")

    if same:
        print("They are homographs!!")
    else:
        print("They are not homographs")



def display_menu() -> None:
    """
    (Person 3):
        Print the menu options clearly.

    Menu:
        ================================
        Path Homograph Detector - Lab05
        ================================
        1. Run Non-Homograph Test Cases
        2. Run Homograph Test Cases
        3. Manually Compare Two Paths
        4. Quit
        ================================
    """
    print("\n================================")
    print(" Path Homograph Detector - Lab05")
    print("================================")
    print("1. Run Non-Homograph Test Cases")
    print("2. Run Homograph Test Cases")
    print("3. Manually Compare Two Paths")
    print("4. Quit")
    print("================================")


def main() -> None:
    """
    (Person 3):
        Main loop — display menu, get user input, route to correct function.
        Loop until the user selects Quit.
        Handle invalid input gracefully.
    """
    starting = True
    

    while starting:
        display_menu()
        choice = input("Select option:")

        if choice == "1":
            run_non_homograph_tests()
        elif choice == "2":
            run_homograph_tests()
        elif choice == "3":
            manual_comparison()
        elif choice == "4":
            print("Thank you! See you soon!")
            starting = False
        else:
            print("ERROR: Try a number between 1 and 4")


if __name__ == "__main__":
    main()
