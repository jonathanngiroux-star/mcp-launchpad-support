#!/usr/bin/env python3
"""
MCP Launchpad Support Server - Token Launch Support Retainer via MCP
"""

import json
import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

DB_PATH = Path(__file__).parent / "launchpad.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS launches (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                token_symbol TEXT NOT NULL,
                chain TEXT NOT NULL,
                phase TEXT NOT NULL,
                tge_date TEXT NOT NULL,
                vesting_schedule TEXT NOT NULL,
                launchpad TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS launch_tasks (
                id TEXT PRIMARY KEY,
                launch_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                assignee TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                FOREIGN KEY (launch_id) REFERENCES launches (id)
            )
        """)

init_db()

TOOLS = [
    Tool(
        name="create_launch",
        description="Create a token launch project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project name"},
                "token_symbol": {"type": "string", "description": "Token symbol"},
                "chain": {"type": "string", "description": "Blockchain"},
                "tge_date": {"type": "string", "description": "TGE date (ISO format)"},
                "vesting_schedule": {"type": "object", "description": "Vesting schedule JSON"},
                "launchpad": {"type": "string", "description": "Launchpad platform"}
            },
            "required": ["project_name", "token_symbol", "chain", "tge_date", "vesting_schedule", "launchpad"]
        }
    ),
    Tool(
        name="add_task",
        description="Add a launch task",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "assignee": {"type": "string", "description": "Assignee"},
                "due_date": {"type": "string", "description": "Due date (ISO format)"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"}
            },
            "required": ["launch_id", "title", "description", "assignee", "due_date"]
        }
    ),
    Tool(
        name="get_launch",
        description="Get launch details",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"}
            },
            "required": ["launch_id"]
        }
    ),
    Tool(
        name="list_launches",
        description="List all launches",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_tasks",
        description="Get tasks for a launch",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"}
            },
            "required": ["launch_id"]
        }
    ),
    Tool(
        name="update_phase",
        description="Update launch phase",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"},
                "phase": {"type": "string", "enum": ["pre-launch", "tge", "post-launch"], "description": "Launch phase"}
            },
            "required": ["launch_id", "phase"]
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "create_launch":
            result = await create_launch(arguments)
        elif name == "add_task":
            result = await add_task(arguments)
        elif name == "get_launch":
            result = await get_launch(arguments)
        elif name == "list_launches":
            result = await list_launches(arguments)
        elif name == "get_tasks":
            result = await get_tasks(arguments)
        elif name == "update_phase":
            result = await update_phase(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

async def create_launch(args: Dict[str, Any]) -> List[TextContent]:
    launch_id = f"{args['project_name'].lower().replace(' ', '-')}-{args['token_symbol'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    now = datetime.now().isoformat()
    launch = {
        "id": launch_id,
        "project_name": args["project_name"],
        "token_symbol": args["token_symbol"],
        "chain": args["chain"],
        "phase": "pre-launch",
        "tge_date": args["tge_date"],
        "vesting_schedule": args["vesting_schedule"],
        "launchpad": args["launchpad"],
        "status": "active",
        "created_at": now,
        "updated_at": now
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO launches (id, project_name, token_symbol, chain, phase, tge_date, vesting_schedule, launchpad, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (launch["id"], launch["project_name"], launch["token_symbol"], launch["chain"],
              launch["phase"], launch["tge_date"], json.dumps(launch["vesting_schedule"]),
              launch["launchpad"], launch["status"], launch["created_at"], launch["updated_at"]))
    return [TextContent(type="text", text=json.dumps({"launch_id": launch_id, "status": "created"}, indent=2))]

async def add_task(args: Dict[str, Any]) -> List[TextContent]:
    task_id = f"task-{args['launch_id']}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    task = {
        "id": task_id,
        "launch_id": args["launch_id"],
        "title": args["title"],
        "description": args["description"],
        "assignee": args["assignee"],
        "due_date": args["due_date"],
        "status": "todo",
        "priority": args.get("priority", "medium")
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO launch_tasks (id, launch_id, title, description, assignee, due_date, status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (task["id"], task["launch_id"], task["title"], task["description"],
              task["assignee"], task["due_date"], task["status"], task["priority"]))
    return [TextContent(type="text", text=json.dumps({"task_id": task_id, "status": "added"}, indent=2))]

async def get_launch(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM launches WHERE id = ?", (args["launch_id"],)).fetchone()
        if row:
            launch = dict(row)
            launch["vesting_schedule"] = json.loads(launch["vesting_schedule"])
            return [TextContent(type="text", text=json.dumps(launch, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": "Launch not found"}))]

async def list_launches(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM launches ORDER BY created_at DESC").fetchall()
        launches = []
        for r in rows:
            l = dict(r)
            l["vesting_schedule"] = json.loads(l["vesting_schedule"])
            launches.append(l)
    return [TextContent(type="text", text=json.dumps({"launches": launches}, indent=2))]

async def get_tasks(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM launch_tasks WHERE launch_id = ?", (args["launch_id"],)).fetchall()
        tasks = [dict(r) for r in rows]
    return [TextContent(type="text", text=json.dumps({"tasks": tasks}, indent=2))]

async def update_phase(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE launches SET phase = ?, updated_at = ? WHERE id = ?",
                     (args["phase"], datetime.now().isoformat(), args["launch_id"]))
    return [TextContent(type="text", text=json.dumps({"launch_id": args["launch_id"], "phase": args["phase"], "status": "updated"}, indent=2))]

from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

init_db()

TOOLS = [
    Tool(
        name="create_launch",
        description="Create a token launch project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project name"},
                "token_symbol": {"type": "string", "description": "Token symbol"},
                "chain": {"type": "string", "description": "Blockchain"},
                "tge_date": {"type": "string", "description": "TGE date (ISO format)"},
                "vesting_schedule": {"type": "object", "description": "Vesting schedule JSON"},
                "launchpad": {"type": "string", "description": "Launchpad platform"}
            },
            "required": ["project_name", "token_symbol", "chain", "tge_date", "vesting_schedule", "launchpad"]
        }
    ),
    Tool(
        name="add_task",
        description="Add a launch task",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "assignee": {"type": "string", "description": "Assignee"},
                "due_date": {"type": "string", "description": "Due date (ISO format)"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"}
            },
            "required": ["launch_id", "title", "description", "assignee", "due_date"]
        }
    ),
    Tool(
        name="get_launch",
        description="Get launch details",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"}
            },
            "required": ["launch_id"]
        }
    ),
    Tool(
        name="list_launches",
        description="List all launches",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_tasks",
        description="Get tasks for a launch",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"}
            },
            "required": ["launch_id"]
        }
    ),
    Tool(
        name="update_phase",
        description="Update launch phase",
        inputSchema={
            "type": "object",
            "properties": {
                "launch_id": {"type": "string", "description": "Launch ID"},
                "phase": {"type": "string", "enum": ["pre-launch", "tge", "post-launch"], "description": "Launch phase"}
            },
            "required": ["launch_id", "phase"]
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "create_launch":
            result = await create_launch(arguments)
        elif name == "add_task":
            result = await add_task(arguments)
        elif name == "get_launch":
            result = await get_launch(arguments)
        elif name == "list_launches":
            result = await list_launches(arguments)
        elif name == "get_tasks":
            result = await get_tasks(arguments)
        elif name == "update_phase":
            result = await update_phase(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

app = Server(
    name="mcp-launchpad-support",
    on_list_tools=lambda: list_tools_handler(),
    on_call_tool=lambda name, arguments: call_tool_handler(name, arguments)
)

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    async def serve():
        server = await stdio_server()
        await app.run(server.stdin, server.stdout)
    asyncio.run(serve())