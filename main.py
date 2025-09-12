import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from functions.get_files_info import get_files_info



def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client=genai.Client(api_key=api_key)

    # sys.argv variable is a list of strings representing the command-line arguments passed to the script. First element is the script name, rest are the arguments passed to the script.

    if len(sys.argv)<2:
        print("I didn't receieve a prompt!")
        sys.exit(1)
    verbose_flag=False
    if(len(sys.argv)==3 and sys.argv[2]=='-v'):
        verbose_flag=True
    prompt=sys.argv[1]

    messages=[
        types.Content(
            role='user',
            parts=[
                types.Part(text=prompt)
            ]
        )
    ]



    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=messages
    )

    print(response.text)
    if verbose_flag:
        print("User Prompt:",prompt)
        print(messages)
        print(sys.argv[1])
        print("Prompt tokens:",response.usage_metadata.prompt_token_count)
        print("Response tokens:",response.usage_metadata.candidates_token_count)

# print(get_files_info("functions"))

main()