from env import API_KEY, GUILD_ID, OPENAI_API_KEY, OPENAI_ORG_ID
import discord
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
import json
from google_search import turbo_search
import time
from message_db import MessageDatabase

user_messages = MessageDatabase()

openai = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)
MODEL = "gpt-4"

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

    user_messages[interaction.user.id].append({"role": "user", "content": message})

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    response: Stream[ChatCompletionChunk] = openai.chat.completions.create(
        model=MODEL,
        messages=user_messages[interaction.user.id]
        + [
            {
                "role": "system",
                "content": f"The current date is {current_time}. You cannot answer "
                "questions after 2022 without querying the search function. "
                "The results of your search operation will be bad unless you use "
                "specific language. Your query may include several topics. The engine "
                "is advanced and can handle it.",
            }
        ],
        stream=True,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "This is an advanced search engine that requires you to describe exactly what you want. You can enter as much text as you want, and more complex queries often lead to more precise results.",
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
            tool_id_from_chunk = chunk.choices[0].delta.tool_calls[0].id
            if tool_id_from_chunk:
                tool_id = tool_id_from_chunk
            content += chunk.choices[0].delta.tool_calls[0].function.arguments
            continue
        chunk_content = chunk.choices[0].delta.content
        if chunk_content:
            content += chunk_content
            await interaction.edit_original_response(content=content)

        elif chunk.choices[0].finish_reason == "tool_calls":
            arguments = json.loads(content)
            # TODO: make recursive
            if function_name == "search":
                search_results = turbo_search(arguments["query"])
                content = json.dumps(arguments)
                user_messages[interaction.user.id].append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_id,
                                "function": {"name": "search", "arguments": content},
                                "type": "function",
                            }
                        ],
                    }
                )
                user_messages[interaction.user.id].append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(search_results),
                    }
                )
                response = openai.chat.completions.create(
                    model=MODEL,
                    messages=user_messages[interaction.user.id],
                    stream=True,
                )
                content = ""
                count = 0
                edit_function = interaction.edit_original_response
                for chunk in response:
                    if chunk.choices[0].finish_reason:
                        break
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                    count += 1
                    if count % 5 == 0:
                        try:
                            await interaction.edit_original_response(content=content)
                        except:
                            await interaction.followup.send(
                                content=chunk.choices[0].delta.content
                            )
                            content = ""
                await interaction.edit_original_response(content=content)
        elif not chunk.choices[0].finish_reason:
            continue
        else:
            break
    user_messages[interaction.user.id].append({"role": "assistant", "content": content})


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.channel.type.name == "private":
        user_messages[message.author.id].append(
            {"role": "user", "content": message.content}
        )
        content: str = ""
        assistant_message: None | discord.Message = None
        count = 0
        for chunk in openai.chat.completions.create(
            model=MODEL, messages=user_messages[message.author.id], stream=True
        ):
            if chunk.choices[0].finish_reason:
                break
            content += chunk.choices[0].delta.content
            if content and count % 16 == 0:
                if assistant_message:
                    # refresh for content length
                    try:
                        await assistant_message.edit(content=content)
                    except:
                        content = chunk.choices[0].delta.content
                        assistant_message = await message.channel.send(content=content)
                else:
                    assistant_message = await message.channel.send(content=content)
            count += 1
        await assistant_message.edit(content=content)
        user_messages[message.author.id].append(
            {"role": "assistant", "content": content}
        )


@client.event
async def on_ready():
    await tree.sync(guild=guild)


if __name__ == "__main__":
    client.run(API_KEY)
