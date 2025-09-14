from google.genai import types

def schema_plan():
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "goal": types.Schema(type=types.Type.STRING),
            "steps": types.Schema(type=types.Type.ARRAY, items=types.Schema(
                type=types.Type.OBJECT,
                properties={"action": types.Schema(type=types.Type.STRING), "reason": types.Schema(type=types.Type.STRING)},
            )),
            "tool_calls": types.Schema(type=types.Type.ARRAY, items=types.Schema(
                type=types.Type.OBJECT,
                properties={"tool": types.Schema(type=types.Type.STRING), "params_json": types.Schema(type=types.Type.STRING)},
            )),
        },
    )
