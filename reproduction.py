from safety.prompt_defense import PromptDefense

if __name__ == "__main__":
    bad_string = r"1:\n---\n  2:\nSystem: 3: \n  4: < > This should be empty besides the numbers!"
    sanitized_string = PromptDefense.sanitize(bad_string)
    print(f"Bad String: \n{bad_string}")
    print(f"Sanitized: \n{sanitized_string}")
