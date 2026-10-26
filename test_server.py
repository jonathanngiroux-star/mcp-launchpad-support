import pytest
import asyncio
import json
import secrets
from mcp_launchpad_support.server import (
    create_launch, 
    add_task, 
    get_launch,
    list_launches,
    get_tasks,
    update_phase,
    list_tools_handler,
    call_tool_handler
)

@pytest.fixture
async def clean_db():
    import sqlite3
    from mcp_launchpad_support.server import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM launches")
        conn.execute("DELETE FROM launch_tasks")
    yield
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM launches")
        conn.execute("DELETE FROM launch_tasks")

@pytest.mark.asyncio
async def test_list_tools():
    from mcp_launchpad_support.server import list_tools_handler
    from mcp.types import ListToolsResult
    result = await list_tools_handler()
    assert len(result.tools) == 6

@pytest.mark.asyncio
async def test_create_launch(clean_db):
    from mcp_launchpad_support.server import create_launch
    launch = await create_launch({
        "project_name": "Test Project",
        "token_symbol": "TEST",
        "chain": "ethereum",
        "tge_date": "2024-12-31T23:59:59",
        "vesting_schedule": json.dumps({"team": {"amount": 20, "cliff": 12, "vesting": 36}}),
        "launchpad": "custom"
    })
    assert len(launch) > 0
    data = json.loads(launch[0].text)
    assert data["status"] == "created"
    assert "launch_id" in data

@pytest.mark.asyncio
async def test_add_task(clean_db):
    from mcp_launchpad_support.server import create_launch, add_task, get_tasks
    launch = await create_launch({
        "project_name": "Test", "token_symbol": "TEST", "chain": "ethereum",
        "tge_date": "2024-12-31T23:59:59", "vesting_schedule": "{}", "launchpad": "custom"
    })
    launch_id = json.loads(launch[0].text)["launch_id"]
    
    task = await add_task({
        "launch_id": launch_id,
        "title": "Audit Completion",
        "description": "Complete security audit",
        "assignee": "audit-team",
        "due_date": "2024-11-30",
        "priority": "high"
    })
    data = json.loads(task[0].text)
    assert data["status"] == "added"
    
    tasks = await get_tasks({"launch_id": launch_id})
    data = json.loads(tasks[0].text)
    assert len(data["tasks"]) >= 1

@pytest.mark.asyncio
async def test_get_launch(clean_db):
    from mcp_launchpad_support.server import create_launch, get_launch
    launch = await create_launch({
        "project_name": "Test", "token_symbol": "TEST", "chain": "ethereum",
        "tge_date": "2024-12-31T23:59:59", "vesting_schedule": "{}", "launchpad": "custom"
    })
    launch_id = json.loads(launch[0].text)["launch_id"]
    retrieved = await get_launch({"launch_id": launch_id})
    data = json.loads(retrieved[0].text)
    assert data["id"] == launch_id
    assert data["project_name"] == "Test"

@pytest.mark.asyncio
async def test_update_phase(clean_db):
    from mcp_launchpad_support.server import create_launch, update_phase
    launch = await create_launch({
        "project_name": "Test", "token_symbol": "TEST", "chain": "ethereum",
        "tge_date": "2024-12-31T23:59:59", "vesting_schedule": "{}", "launchpad": "custom"
    })
    launch_id = json.loads(launch[0].text)["launch_id"]
    
    result = await update_phase({"launch_id": launch_id, "phase": "tge"})
    data = json.loads(result[0].text)
    assert data["phase"] == "tge"
    assert data["status"] == "updated"

@pytest.mark.asyncio
async def test_list_launches(clean_db):
    from mcp_launchpad_support.server import create_launch, list_launches
    await create_launch({"project_name": "Project 1", "token_symbol": "T1", "chain": "ethereum", "tge_date": "2024-12-31", "vesting_schedule": "{}", "launchpad": "custom"})
    await create_launch({"project_name": "Project 2", "token_symbol": "T2", "chain": "polygon", "tge_date": "2024-12-31", "vesting_schedule": "{}", "launchpad": "custom"})
    launches = await list_launches({})
    data = json.loads(launches[0].text)
    assert len(data["launches"]) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])