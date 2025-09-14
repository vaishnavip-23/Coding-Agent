
# Function to check if a string is a palindrome
def is_palindrome(s):
    # Convert the string to lowercase and remove non-alphanumeric characters
    # This makes the check case-insensitive and ignores punctuation/spaces
    s = "".join(filter(str.isalnum, s)).lower()
    # Compare the string with its reverse
    # If they are the same, the string is a palindrome
    return s == s[::-1]

# Get input from the user
user_input = input("Enter a string: ")

# Check if the input is a palindrome using the is_palindrome function
if is_palindrome(user_input):
    # If it is a palindrome, print a success message
    print(f"'{user_input}' is a palindrome.")
else:
    # If it is not a palindrome, print a failure message
    print(f"'{user_input}' is not a palindrome.")
