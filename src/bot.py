from env import API_KEY, GUILD_ID, OPENAI_API_KEY, OPENAI_ORG_ID
import discord
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk
import json
from google_search import google_search

user_messages: dict[int, list[dict[str, str]]] = {}

openai = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
guild = client.get_guild(GUILD_ID)
tree = discord.app_commands.CommandTree(client)


@tree.command(name="reset", description="Creates a new message thread", guild=guild)
async def reset(interaction: discord.Interaction):
    user_messages[interaction.user.id] = []
    await interaction.response.send_message(
        ephemeral=True, content="New message thread created!"
    )


@tree.command(name="chat", description="Chat with GPT4!", guild=guild)
async def chat(interaction: discord.Interaction, message: str):
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
    except:
        pass

    if interaction.user.id not in user_messages:
        user_messages[interaction.user.id] = []
    if message:
        user_messages[interaction.user.id].append({"role": "user", "content": message})

    response: Stream[ChatCompletionChunk] = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=user_messages[interaction.user.id],
        stream=True,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the internet for an answer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to search for",
                            }
                        },
                    },
                },
            }
        ],
    )
    content = ""
    for chunk in response:
        print(chunk.model_dump_json(indent=2))
        if chunk.choices[0].delta.tool_calls:
            if chunk.choices[0].delta.tool_calls[0].function.name:
                function_name = chunk.choices[0].delta.tool_calls[0].function.name
            content += chunk.choices[0].delta.tool_calls[0].function.arguments
            continue
        chunk_content = chunk.choices[0].delta.content
        if chunk_content:
            content += chunk_content
            await interaction.edit_original_response(content=content)
        elif chunk.choices[0].finish_reason == "tool_calls":
            arguments = json.loads(content)
            print(arguments)
            if function_name == "search":
                search_results = google_search(arguments["query"])
                await chat(interaction, "")
        elif not chunk.choices[0].finish_reason:
            continue
        else:
            break


@client.event
async def on_ready():
    await tree.sync(guild=guild)


client.run(API_KEY)
