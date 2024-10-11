import idigbio
from openai import OpenAI
import instructor
from pydantic import BaseModel, Field
import asyncio

# Next Steps:
# - multiple tools for local db and idigbbio
# - filtering across dbs for focus, etc..
# - fine tune internvl for tool use

idigbio_api = idigbio.json()

class IDigBioSearch(BaseModel):
    rewritten_query: str
    async def execute(self):
        return idigbio_api.search_records(rq={"scientificname": self.rewritten_query})

client = instructor.from_openai(OpenAI())

retrieval, completion = client.chat.completions.create_with_completion(
    model="gpt-4",
    response_model=IDigBioSearch,
    messages=[
        {"role": "system", "content": "You are a biomedical researcher."},
        {"role": "user", "content": "What Lepidoptera are available in this IDigBio database?"},
    ],
)

print(retrieval)
print(completion)
asyncio.run(retrieval.execute())