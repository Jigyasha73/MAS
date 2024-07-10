```python
import asyncio
import aiohttp
import aiofiles
from fastapi import FastAPI, HTTPException, JSONResponse
from pydantic import BaseModel

app = FastAPI()

class TaskRequest(BaseModel):
    urls: list[str]
    output_file: str

async def fetch_data(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from {url}: {e}")

async def write_data(output_file, data):
    async with aiofiles.open(output_file, 'w') as file:
        await file.write(data)

@app.post("/start_tasks/")
async def start_tasks(task_request: TaskRequest):
    urls = task_request.urls
    output_file = task_request.output_file
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    combined_data = "\n".join(str(result) for result in results)
    await write_data(output_file, combined_data)
    
    return {"message": "Tasks completed successfully", "output_file": output_file}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred"},
    )

@app.post("/start_tasks_with_timeout/")
async def start_tasks_with_timeout(task_request: TaskRequest):
    urls = task_request.urls
    output_file = task_request.output_file
    timeout = 10  # 10 seconds timeout
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True, timeout=timeout)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=500, detail="Timeout error occurred while fetching data")
    
    combined_data = "\n".join(str(result) for result in results)
    await write_data(output_file, combined_data)
    
    return {"message": "Tasks completed successfully", "output_file": output_file}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)